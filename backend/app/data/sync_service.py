import anyio
import httpx

from backend.app.data.repository import DuckDbRepository
from backend.app.models.data_sync import DataSyncRequest, DataSyncResponse, DownloadedRows, SyncError


class SyncFailedError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class StrategyNotFoundError(LookupError):
    def __init__(self, strategy_id: str) -> None:
        super().__init__(strategy_id)
        self.strategy_id = strategy_id


class DataSyncService:
    def __init__(
        self,
        *,
        repository: DuckDbRepository,
        binance_client,
        strategy_lookback_by_id: dict[str, int],
        retry_delays: list[float] | tuple[float, ...] | None = None,
    ) -> None:
        self.repository = repository
        self.binance_client = binance_client
        self.strategy_lookback_by_id = strategy_lookback_by_id
        self.retry_delays = list(retry_delays or [1, 2, 4, 8, 16])

    def get_status(self, request: DataSyncRequest):
        return self.repository.get_coverage(
            request=request,
            required_lookback_bars=self._get_required_lookback(request.strategy_id),
        )

    def _get_required_lookback(self, strategy_id: str) -> int:
        try:
            return self.strategy_lookback_by_id[strategy_id]
        except KeyError as exc:
            raise StrategyNotFoundError(strategy_id) from exc

    async def _call_with_retry(self, method, **kwargs):
        last_error: Exception | None = None
        for index, delay in enumerate(self.retry_delays):
            has_next_attempt = index < len(self.retry_delays) - 1
            try:
                return await method(**kwargs)
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code != 429 and exc.response.status_code < 500:
                    raise SyncFailedError(
                        "sync_failed",
                        f"Binance request failed with status {exc.response.status_code}.",
                    ) from exc
                if has_next_attempt:
                    await anyio.sleep(delay)
            except httpx.TransportError as exc:
                last_error = exc
                if has_next_attempt:
                    await anyio.sleep(delay)
            except RuntimeError as exc:
                last_error = exc
                if not str(exc).startswith(("429", "500")):
                    raise SyncFailedError("sync_failed", str(exc)) from exc
                if has_next_attempt:
                    await anyio.sleep(delay)
        if last_error is not None:
            if isinstance(last_error, httpx.HTTPStatusError):
                raise SyncFailedError(
                    "sync_failed",
                    f"Binance request failed with status {last_error.response.status_code}.",
                ) from last_error
            if isinstance(last_error, httpx.TransportError):
                raise SyncFailedError(
                    "sync_failed",
                    f"Binance transport error: {last_error}.",
                ) from last_error
            raise SyncFailedError("sync_failed", str(last_error)) from last_error
        raise SyncFailedError("sync_failed", "Unknown sync failure")

    def _build_response(
        self,
        *,
        request: DataSyncRequest,
        coverage,
        downloaded: DownloadedRows,
        status: str,
        error: SyncError | None = None,
    ) -> DataSyncResponse:
        return DataSyncResponse(
            status=status,
            symbol=request.symbol,
            strategy_id=request.strategy_id,
            timeframe=request.timeframe,
            requested_start=request.start,
            requested_end=request.end,
            effective_start=coverage.effective_start,
            effective_end=coverage.effective_end,
            complete=coverage.complete,
            downloaded=downloaded,
            coverage=coverage,
            error=error,
        )

    async def sync_market_data(self, request: DataSyncRequest) -> DataSyncResponse:
        lookback = self._get_required_lookback(request.strategy_id)
        starting_coverage = self.repository.get_coverage(request=request, required_lookback_bars=lookback)
        downloaded = DownloadedRows(kline_rows=0, funding_rows=0)

        try:
            for missing_range in starting_coverage.kline.missing_ranges:
                kline_rows = await self._call_with_retry(
                    self.binance_client.fetch_klines,
                    symbol=request.symbol,
                    timeframe=request.timeframe,
                    start=missing_range.start,
                    end=missing_range.end,
                )
                self.repository.upsert_klines(kline_rows)
                downloaded.kline_rows += len(kline_rows)

            for missing_range in starting_coverage.funding.missing_ranges:
                funding_rows = await self._call_with_retry(
                    self.binance_client.fetch_funding_rates,
                    symbol=request.symbol,
                    start=missing_range.start,
                    end=missing_range.end,
                )
                self.repository.upsert_funding_rates(funding_rows)
                downloaded.funding_rows += len(funding_rows)
        except SyncFailedError as exc:
            coverage = self.repository.get_coverage(request=request, required_lookback_bars=lookback)
            return self._build_response(
                request=request,
                coverage=coverage,
                downloaded=downloaded,
                status="sync_failed",
                error=SyncError(code=exc.code, message=exc.message),
            )

        coverage = self.repository.get_coverage(request=request, required_lookback_bars=lookback)

        if downloaded.kline_rows == 0 and downloaded.funding_rows == 0 and not coverage.complete:
            return self._build_response(
                request=request,
                coverage=coverage,
                downloaded=downloaded,
                status="no_data_available",
            )
        if coverage.complete:
            return self._build_response(
                request=request,
                coverage=coverage,
                downloaded=downloaded,
                status="completed",
            )
        return self._build_response(
            request=request,
            coverage=coverage,
            downloaded=downloaded,
            status="sync_failed",
            error=SyncError(
                code="sync_failed",
                message="Market data coverage remained incomplete after sync.",
            ),
        )
