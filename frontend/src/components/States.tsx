interface Props {
  message?: string;
}

export function Loading({ message = "Loading briefing data…" }: Props) {
  return (
    <div className="state">
      <div className="spinner" />
      {message}
    </div>
  );
}

export function ErrorView({ message }: { message: string }) {
  return (
    <div className="state error">
      <strong>Could not load data.</strong>
      <div style={{ marginTop: 6, fontSize: 13 }}>{message}</div>
      <div style={{ marginTop: 10, fontSize: 13 }} className="muted">
        Make sure the backend is running and that ingestion + compute have been run.
      </div>
    </div>
  );
}

export function Empty({ message = "No data to display yet." }: Props) {
  return <div className="state">{message}</div>;
}
