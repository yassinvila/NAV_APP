export default function DebugPanel({ parsedCommand, destination, route }) {
  return (
    <aside className="panel debug-panel">
      <h2>Debug</h2>
      <div className="debug-block">
        <h3>Parsed command</h3>
        <pre>{JSON.stringify(parsedCommand, null, 2) || '{}'}</pre>
      </div>
      <div className="debug-block">
        <h3>Destination</h3>
        <pre>{JSON.stringify(destination, null, 2) || '{}'}</pre>
      </div>
      <div className="debug-block">
        <h3>Route</h3>
        <pre>{JSON.stringify(route, null, 2) || '{}'}</pre>
      </div>
    </aside>
  )
}
