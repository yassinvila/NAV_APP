function formatDistance(meters) {
  if (typeof meters !== 'number') return '—'
  if (meters < 1000) return `${Math.round(meters)} m`
  return `${(meters / 1000).toFixed(1)} km`
}

function formatDuration(seconds) {
  if (typeof seconds !== 'number') return '—'
  const minutes = Math.max(1, Math.round(seconds / 60))
  if (minutes < 60) return `${minutes} min`
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return `${hours} h ${remainingMinutes} min`
}

export default function RouteInfo({ route, destination }) {
  return (
    <aside className="panel route-info">
      <h2>Route</h2>
      <div className="route-stats route-summary-grid">
        <div className="route-stat-card">
          <span>Route</span>
          <strong>{destination ? destination.name : 'No destination yet.'}</strong>
        </div>
        <div className="route-stat-card">
          <span>Distance</span>
          <strong>{formatDistance(route?.distance)}</strong>
        </div>
        <div className="route-stat-card">
          <span>Duration</span>
          <strong>{formatDuration(route?.duration)}</strong>
        </div>
      </div>
    </aside>
  )
}
