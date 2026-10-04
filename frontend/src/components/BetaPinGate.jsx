import { useState } from 'react'

import { validateBetaPin } from '../services/api'

export default function BetaPinGate({ onAccessGranted }) {
  const [pin, setPin] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      await validateBetaPin(pin)
      onAccessGranted()
    } catch (gateError) {
      setError(gateError.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="auth-card beta-card">
      <div className="auth-badge">Beta Access Required</div>
      <h1>Enter the pin to continue.</h1>
      <form className="auth-form" onSubmit={handleSubmit}>
        <label htmlFor="beta-pin">Access pin</label>
        <input
          id="beta-pin"
          type="password"
          placeholder="Enter beta pin"
          value={pin}
          onChange={(event) => setPin(event.target.value)}
        />
        <button type="submit" disabled={loading || !pin.trim()}>
          {loading ? 'Checking...' : 'Continue'}
        </button>
        {error ? <p className="error-text">{error}</p> : null}
      </form>
    </section>
  )
}