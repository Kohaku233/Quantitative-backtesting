import { formatNumber, formatPercent, formatTimestamp } from "../lib/formatters";

export type TradeRow = {
  trade_id: number;
  side: string;
  entry_time: string;
  exit_time: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  allocated_margin_at_entry: number;
  notional: number;
  gross_pnl: number;
  fees: number;
  funding_pnl: number;
  net_pnl: number;
  return_pct_on_margin: number;
  holding_bars: number;
  holding_seconds: number;
  exit_reason: string;
};

type TradesTableProps = {
  trades: TradeRow[];
  className?: string;
  selectedTradeId?: number | null;
  onSelectTrade?: (tradeId: number) => void;
};

function formatDuration(seconds: number) {
  if (!Number.isFinite(seconds) || seconds <= 0) {
    return "0s";
  }

  const total = Math.round(seconds);
  const days = Math.floor(total / 86_400);
  const hours = Math.floor((total % 86_400) / 3_600);
  const minutes = Math.floor((total % 3_600) / 60);

  if (days > 0) {
    return `${days}d ${hours}h`;
  }

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }

  return `${minutes}m`;
}

function formatSide(side: string) {
  return side.replaceAll("_", " ");
}

export function TradesTable({
  trades,
  className,
  selectedTradeId = null,
  onSelectTrade,
}: TradesTableProps) {
  return (
    <section className={className ? `trades-table-shell ${className}` : "trades-table-shell"}>
      <div className="section-heading">
        <p className="eyebrow">Execution Log</p>
        <h3>Trade List</h3>
        <p className="section-heading__subtle">
          Select a row to inspect the execution and highlight its chart markers.
        </p>
      </div>

      <div className="table-scroll">
        <table className="trades-table" aria-label="Trade list">
          <thead>
            <tr>
              <th scope="col">Trade</th>
              <th scope="col">Side</th>
              <th scope="col">Entry</th>
              <th scope="col">Exit</th>
              <th scope="col">Entry Price</th>
              <th scope="col">Exit Price</th>
              <th scope="col">Qty</th>
              <th scope="col">Margin</th>
              <th scope="col">Notional</th>
              <th scope="col">Gross PnL</th>
              <th scope="col">Fees</th>
              <th scope="col">Funding</th>
              <th scope="col">Net PnL</th>
              <th scope="col">Return on Margin</th>
              <th scope="col">Holding</th>
              <th scope="col">Exit Reason</th>
            </tr>
          </thead>
          <tbody>
            {trades.length === 0 ? (
              <tr>
                <td colSpan={16} className="table-empty">
                  No trades were generated for the selected range.
                </td>
              </tr>
            ) : (
              trades.map((trade) => (
                <tr
                  key={trade.trade_id}
                  data-tone={trade.net_pnl >= 0 ? "positive" : "negative"}
                  data-active={selectedTradeId === trade.trade_id}
                  className={selectedTradeId === trade.trade_id ? "trades-table__row trades-table__row--active" : "trades-table__row"}
                  onClick={() => onSelectTrade?.(trade.trade_id)}
                >
                  <th scope="row">#{trade.trade_id}</th>
                  <td>{formatSide(trade.side)}</td>
                  <td>{formatTimestamp(trade.entry_time)}</td>
                  <td>{formatTimestamp(trade.exit_time)}</td>
                  <td>{formatNumber(trade.entry_price, 2)}</td>
                  <td>{formatNumber(trade.exit_price, 2)}</td>
                  <td>{formatNumber(trade.quantity, 6)}</td>
                  <td>{formatNumber(trade.allocated_margin_at_entry, 2)}</td>
                  <td>{formatNumber(trade.notional, 2)}</td>
                  <td>{formatNumber(trade.gross_pnl, 2)}</td>
                  <td>{formatNumber(trade.fees, 2)}</td>
                  <td>{formatNumber(trade.funding_pnl, 2)}</td>
                  <td className={trade.net_pnl >= 0 ? "table-value--positive" : "table-value--negative"}>
                    {formatNumber(trade.net_pnl, 2)}
                  </td>
                  <td>{formatPercent(trade.return_pct_on_margin, 2)}</td>
                  <td>
                    {formatDuration(trade.holding_seconds)} / {trade.holding_bars} bars
                  </td>
                  <td>{formatSide(trade.exit_reason)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
