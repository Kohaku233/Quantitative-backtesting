import { ArrowDownRight, ArrowUpRight, Clock3, Scale, Wallet } from "lucide-react";

import { formatNumber, formatPercent, formatTimestamp } from "../lib/formatters";
import type { TradeRow } from "./TradesTable";

type TradeInspectorProps = {
  trade: TradeRow | null;
};

function formatDuration(seconds: number) {
  if (!Number.isFinite(seconds) || seconds <= 0) {
    return "0m";
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

export function TradeInspector({ trade }: TradeInspectorProps) {
  return (
    <section className="summary-card trade-inspector" aria-label="Selected trade">
      <div className="section-heading">
        <p className="eyebrow">Selected Trade</p>
        <h3>Inspector</h3>
      </div>

      {!trade ? (
        <p className="section-heading__subtle">
          Select a trade row below the chart to inspect its sizing, costs, and realized outcome.
        </p>
      ) : (
        <div className="trade-inspector__body">
          <div className="trade-inspector__header">
            <div>
              <span className={`trade-pill trade-pill--${trade.side}`}>{trade.side}</span>
              <strong>Trade #{trade.trade_id}</strong>
            </div>
            <strong className={trade.net_pnl >= 0 ? "table-value--positive" : "table-value--negative"}>
              {formatNumber(trade.net_pnl, 2)}
            </strong>
          </div>

          <dl className="trade-inspector__grid">
            <div>
              <dt><ArrowUpRight size={14} aria-hidden="true" /> Entry</dt>
              <dd>{formatTimestamp(trade.entry_time)}</dd>
            </div>
            <div>
              <dt><ArrowDownRight size={14} aria-hidden="true" /> Exit</dt>
              <dd>{formatTimestamp(trade.exit_time)}</dd>
            </div>
            <div>
              <dt><Scale size={14} aria-hidden="true" /> Quantity</dt>
              <dd>{formatNumber(trade.quantity, 6)}</dd>
            </div>
            <div>
              <dt><Wallet size={14} aria-hidden="true" /> Margin</dt>
              <dd>{formatNumber(trade.allocated_margin_at_entry, 2)}</dd>
            </div>
            <div>
              <dt>Net Return</dt>
              <dd>{formatPercent(trade.return_pct_on_margin, 2)}</dd>
            </div>
            <div>
              <dt><Clock3 size={14} aria-hidden="true" /> Holding</dt>
              <dd>{formatDuration(trade.holding_seconds)}</dd>
            </div>
            <div>
              <dt>Fees</dt>
              <dd>{formatNumber(trade.fees, 2)}</dd>
            </div>
            <div>
              <dt>Funding</dt>
              <dd>{formatNumber(trade.funding_pnl, 2)}</dd>
            </div>
          </dl>

          <p className="trade-inspector__reason">
            Exit reason: <strong>{trade.exit_reason.replaceAll("_", " ")}</strong>
          </p>
        </div>
      )}
    </section>
  );
}
