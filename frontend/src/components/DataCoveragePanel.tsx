import { formatTimestamp } from "../lib/formatters";
import type { CoverageSection, CoverageStatusResponse } from "../types/contracts";

type DataCoveragePanelProps = {
  coverage: CoverageStatusResponse | null;
  isLoading: boolean;
  syncStatus: string | null;
};

function CoverageBlock({
  title,
  section,
}: {
  title: string;
  section: CoverageSection;
}) {
  return (
    <article className="coverage-block">
      <div className="coverage-block__heading">
        <h3>{title}</h3>
        <span>{section.missing_ranges.length === 0 ? "Complete" : `${section.missing_ranges.length} missing`}</span>
      </div>

      <dl className="coverage-block__range">
        <div>
          <dt>Cached start</dt>
          <dd>{section.cached_start ? formatTimestamp(section.cached_start) : "Not cached"}</dd>
        </div>
        <div>
          <dt>Cached end</dt>
          <dd>{section.cached_end ? formatTimestamp(section.cached_end) : "Not cached"}</dd>
        </div>
      </dl>

      {section.missing_ranges.length > 0 ? (
        <ul className="coverage-block__gaps">
          {section.missing_ranges.map((range) => (
            <li key={`${range.start}-${range.end}`}>
              {formatTimestamp(range.start)} to {formatTimestamp(range.end)}
            </li>
          ))}
        </ul>
      ) : (
        <p className="coverage-block__complete">No gaps detected for this stream.</p>
      )}
    </article>
  );
}

export function DataCoveragePanel({
  coverage,
  isLoading,
  syncStatus,
}: DataCoveragePanelProps) {
  return (
    <section className="data-coverage panel-surface">
      <div className="section-heading">
        <p className="eyebrow">Data Coverage</p>
        <h2>Cache status</h2>
        <p className="section-heading__subtle">
          Coverage is checked against the selected timeframe before each run.
        </p>
      </div>

      {isLoading || !coverage ? (
        <p className="coverage-loading">Coverage details will appear once the current request is resolved.</p>
      ) : (
        <>
          <div className="coverage-summary">
            <p>{coverage.complete ? "Complete local coverage" : "Coverage has missing ranges"}</p>
            <span>{coverage.timeframe} bars</span>
            {syncStatus ? <span>Last sync: {syncStatus}</span> : null}
          </div>

          <dl className="coverage-request">
            <div>
              <dt>Requested start</dt>
              <dd>{formatTimestamp(coverage.requested_start)}</dd>
            </div>
            <div>
              <dt>Requested end</dt>
              <dd>{formatTimestamp(coverage.requested_end)}</dd>
            </div>
            <div>
              <dt>Effective start</dt>
              <dd>{formatTimestamp(coverage.effective_start)}</dd>
            </div>
            <div>
              <dt>Effective end</dt>
              <dd>{formatTimestamp(coverage.effective_end)}</dd>
            </div>
          </dl>

          <div className="coverage-grid">
            <CoverageBlock title="Kline history" section={coverage.kline} />
            <CoverageBlock title="Funding history" section={coverage.funding} />
          </div>
        </>
      )}
    </section>
  );
}
