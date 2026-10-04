import { useEffect, useState } from 'react'

export default function DebugPanel({ debugTrace = [] }) {
  const [animatedTrace, setAnimatedTrace] = useState([])
  const charSpeed = 50 // milliseconds per character

  useEffect(() => {
    if (debugTrace.length === 0) {
      return
    }

    let nextAnimatedTrace = debugTrace.map(() => '')
    let traceIndex = 0

    const interval = setInterval(() => {
      setAnimatedTrace((prev) => {
        const newAnimated = nextAnimatedTrace.length === prev.length ? [...prev] : [...nextAnimatedTrace]
        
        if (traceIndex < debugTrace.length) {
          const currentTraceItem = debugTrace[traceIndex]
          const currentLength = newAnimated[traceIndex].length
          
          if (currentLength < currentTraceItem.length) {
            newAnimated[traceIndex] = currentTraceItem.substring(0, currentLength + 1)
          } else {
            traceIndex += 1
            if (traceIndex < debugTrace.length) {
              newAnimated[traceIndex] = debugTrace[traceIndex].substring(0, 1)
            }
          }
        }
        
        return newAnimated
      })
      nextAnimatedTrace = debugTrace.map((traceItem, index) => {
        if (index < traceIndex) return traceItem
        if (index === traceIndex) return debugTrace[index].substring(0, 1)
        return ''
      })
    }, charSpeed)

    return () => clearInterval(interval)
  }, [debugTrace, charSpeed])

  const hasTrace = debugTrace.length > 0
  const displayText = animatedTrace.length === debugTrace.length ? animatedTrace.join('\n') : ''

  return (
    <aside className="panel debug-panel">
      <h2>Live Trace</h2>
      <pre>{hasTrace ? displayText : 'Waiting for a route request...'}</pre>
    </aside>
  )
}
