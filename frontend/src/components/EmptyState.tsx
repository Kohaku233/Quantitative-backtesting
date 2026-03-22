import type { ReactNode } from "react";

type EmptyStateProps = {
  title: string;
  description: ReactNode;
  eyebrow?: string;
  actions?: ReactNode;
  className?: string;
};

export function EmptyState({
  title,
  description,
  eyebrow,
  actions,
  className,
}: EmptyStateProps) {
  return (
    <section className={className ? `empty-state ${className}` : "empty-state"}>
      {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
      <div className="empty-state__copy">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
      {actions ? <div className="empty-state__actions">{actions}</div> : null}
    </section>
  );
}
