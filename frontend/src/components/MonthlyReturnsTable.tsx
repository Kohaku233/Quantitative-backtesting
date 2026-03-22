import { formatPercent } from "../lib/formatters";

export type MonthlyReturnRow = {
  month: string;
  return_pct: number;
};

type MonthlyReturnsTableProps = {
  monthlyReturns: MonthlyReturnRow[];
  className?: string;
};

export function MonthlyReturnsTable({
  monthlyReturns,
  className,
}: MonthlyReturnsTableProps) {
  const averageReturn =
    monthlyReturns.length > 0
      ? monthlyReturns.reduce((sum, item) => sum + item.return_pct, 0) /
        monthlyReturns.length
      : 0;

  return (
    <section className={className ? `monthly-returns ${className}` : "monthly-returns"}>
      <div className="section-heading">
        <p className="eyebrow">Calendar View</p>
        <h3>Monthly Returns</h3>
      </div>

      <div className="table-scroll">
        <table className="returns-table" aria-label="Monthly returns">
          <thead>
            <tr>
              <th scope="col">Month</th>
              <th scope="col">Return</th>
            </tr>
          </thead>
          <tbody>
            {monthlyReturns.length === 0 ? (
              <tr>
                <td colSpan={2} className="table-empty">
                  No monthly return data is available yet.
                </td>
              </tr>
            ) : (
              monthlyReturns.map((row) => (
                <tr key={row.month} data-tone={row.return_pct >= 0 ? "positive" : "negative"}>
                  <th scope="row">{row.month}</th>
                  <td className={row.return_pct >= 0 ? "table-value--positive" : "table-value--negative"}>
                    {formatPercent(row.return_pct, 2)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
          {monthlyReturns.length > 0 ? (
            <tfoot>
              <tr>
                <th scope="row">Average</th>
                <td>{formatPercent(averageReturn, 2)}</td>
              </tr>
            </tfoot>
          ) : null}
        </table>
      </div>
    </section>
  );
}
