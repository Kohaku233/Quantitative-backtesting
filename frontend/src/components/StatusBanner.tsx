import type { ReactNode } from "react";

type StatusTone = "neutral" | "info" | "success" | "warning" | "error";

type StatusBannerProps = {
  tone?: StatusTone;
  title: string;
  description?: ReactNode;
  details?: ReactNode;
  actions?: ReactNode;
  className?: string;
};

export function StatusBanner({
  tone = "neutral",
  title,
  description,
  details,
  actions,
  className,
}: StatusBannerProps) {
  const role = tone === "error" ? "alert" : "status";

  return (
    <section
      className={className ? `status-banner status-banner--${tone} ${className}` : `status-banner status-banner--${tone}`}
      role={role}
    >
      <div className="status-banner__main">
        <p className="eyebrow status-banner__eyebrow">
          {tone === "error" ? "Attention" : tone === "success" ? "Ready" : tone === "warning" ? "Syncing" : "Status"}
        </p>
        <h3>{title}</h3>
        {description ? <p className="status-banner__description">{description}</p> : null}
      </div>
      {details ? <div className="status-banner__details">{details}</div> : null}
      {actions ? <div className="status-banner__actions">{actions}</div> : null}
    </section>
  );
}
