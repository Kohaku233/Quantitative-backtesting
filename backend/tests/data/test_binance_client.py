import anyio

from backend.app.data.binance_client import BinancePublicClient
from backend.app.data.coverage import parse_timestamp


def _ms(value: str) -> int:
    return int(parse_timestamp(value).timestamp() * 1000)


class PagingBinanceClient(BinancePublicClient):
    def __init__(self) -> None:
        super().__init__(kline_limit=2, funding_limit=1)
        self.kline_calls: list[dict[str, int | str]] = []
        self.funding_calls: list[dict[str, int | str]] = []

    async def _request_json(self, path: str, params: dict[str, int | str]):
        if path == "/fapi/v1/klines":
            self.kline_calls.append(params)
            start_time = params["startTime"]
            if start_time == _ms("2024-01-01T00:00:00Z"):
                return [
                    [_ms("2024-01-01T00:00:00Z"), "42000", "42100", "41950", "42050", "100", _ms("2024-01-01T00:59:59Z")],
                    [_ms("2024-01-01T01:00:00Z"), "42050", "42200", "42000", "42150", "110", _ms("2024-01-01T01:59:59Z")],
                ]
            if start_time == _ms("2024-01-01T02:00:00Z"):
                return [
                    [_ms("2024-01-01T02:00:00Z"), "42150", "42300", "42100", "42200", "120", _ms("2024-01-01T02:59:59Z")],
                    [_ms("2024-01-01T03:00:00Z"), "42200", "42400", "42150", "42350", "130", _ms("2024-01-01T03:59:59Z")],
                ]
            return []

        self.funding_calls.append(params)
        start_time = params["startTime"]
        if start_time == _ms("2024-01-01T00:00:00Z"):
            return [{"fundingTime": _ms("2024-01-01T00:00:00Z"), "fundingRate": "0.0001"}]
        if start_time == _ms("2024-01-01T08:00:00Z"):
            return [{"fundingTime": _ms("2024-01-01T08:00:00Z"), "fundingRate": "0.0002"}]
        if start_time == _ms("2024-01-01T16:00:00Z"):
            return [{"fundingTime": _ms("2024-01-01T16:00:00Z"), "fundingRate": "0.0003"}]
        return []


def test_fetch_klines_paginates_until_end() -> None:
    client = PagingBinanceClient()

    async def run_fetch():
        return await client.fetch_klines(
            symbol="BTCUSDT",
            timeframe="1h",
            start="2024-01-01T00:00:00Z",
            end="2024-01-01T03:00:00Z",
        )

    rows = anyio.run(run_fetch)

    assert [row["open_time"] for row in rows] == [
        "2024-01-01T00:00:00Z",
        "2024-01-01T01:00:00Z",
        "2024-01-01T02:00:00Z",
        "2024-01-01T03:00:00Z",
    ]
    assert len(client.kline_calls) == 2


def test_fetch_funding_rates_paginates_until_end() -> None:
    client = PagingBinanceClient()

    async def run_fetch():
        return await client.fetch_funding_rates(
            symbol="BTCUSDT",
            start="2024-01-01T00:00:00Z",
            end="2024-01-01T16:00:00Z",
        )

    rows = anyio.run(run_fetch)

    assert [row["funding_time"] for row in rows] == [
        "2024-01-01T00:00:00Z",
        "2024-01-01T08:00:00Z",
        "2024-01-01T16:00:00Z",
    ]
    assert len(client.funding_calls) == 3
