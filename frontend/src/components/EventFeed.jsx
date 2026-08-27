const SEVERITY_COLOR = { high: "#D85A30", medium: "#EF9F27", low: "#888780" };

export default function EventFeed({ events }) {
  if (!events || events.length === 0) {
    return <p className="muted">No suspicious events detected in this video.</p>;
  }

  return (
    <div className="event-feed">
      {events.map((e) => (
        <div key={e.id} className="event-card" style={{ borderLeftColor: SEVERITY_COLOR[e.severity] }}>
          <div className="event-header">
            <span className="event-type">{e.type.replaceAll("_", " ")}</span>
            <span className="event-time">{e.timestamp_sec.toFixed(1)}s</span>
          </div>
          <p className="event-desc">{e.description}</p>
        </div>
      ))}
    </div>
  );
}