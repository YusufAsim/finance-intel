/** Loading, empty and error placeholders shared by every page. */

interface MessageProps {
  title: string;
  detail?: string;
  action?: React.ReactNode;
}

function Panel({ title, detail, action }: MessageProps) {
  return (
    <div className="rounded-lg border border-line bg-surface px-6 py-10 text-center">
      <p className="text-sm font-medium">{title}</p>
      {detail && <p className="mt-1 text-sm text-muted">{detail}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function Loading({ label = "Loading…" }: { label?: string }) {
  return <Panel title={label} />;
}

export function Empty({ label = "There is nothing to show yet." }: { label?: string }) {
  return <Panel title={label} />;
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <Panel
      title="This view could not be loaded."
      detail={message}
      action={
        onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="rounded-md border border-line px-3 py-1.5 text-sm hover:bg-canvas"
          >
            Try again
          </button>
        )
      }
    />
  );
}

/** Renders the right state for an async view in one place. */
export function AsyncView<T>({
  state,
  isEmpty,
  emptyLabel,
  children,
}: {
  state: { data: T | null; loading: boolean; error: string | null; reload: () => void };
  isEmpty?: (data: T) => boolean;
  emptyLabel?: string;
  children: (data: T) => React.ReactNode;
}) {
  if (state.loading) return <Loading />;
  if (state.error) return <ErrorState message={state.error} onRetry={state.reload} />;
  if (!state.data) return <Empty label={emptyLabel} />;
  if (isEmpty?.(state.data)) return <Empty label={emptyLabel} />;
  return <>{children(state.data)}</>;
}
