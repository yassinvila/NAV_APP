import { useState } from 'react'

import { loginAccount, registerAccount } from '../services/api'

export default function AuthGate({ onAuthSuccess }) {
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [homeAddress, setHomeAddress] = useState('')
  const [workAddress, setWorkAddress] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response =
        mode === 'register'
          ? await registerAccount(username, password, homeAddress, workAddress)
          : await loginAccount(username, password)

      onAuthSuccess(response.user)
    } catch (authError) {
      setError(authError.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="auth-card">
      <div className="auth-badge">Account Access</div>
      <h1>{mode === 'register' ? 'Create your account.' : 'Log in to continue.'}</h1>
      <p>
        Use a username and password only. No email is required for this beta build.
      </p>

      <div className="auth-tabs" role="tablist" aria-label="Authentication mode">
        <button
          type="button"
          className={mode === 'login' ? 'active' : ''}
          onClick={() => setMode('login')}
        >
          Log in
        </button>
        <button
          type="button"
          className={mode === 'register' ? 'active' : ''}
          onClick={() => setMode('register')}
        >
          Create account
        </button>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label htmlFor="username">Username</label>
        <input
          id="username"
          type="text"
          autoComplete="username"
          placeholder="Choose a username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
        />

        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
          placeholder="Enter your password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />

        {mode === 'register' ? (
          <>
            <label htmlFor="home-address">Home address</label>
            <input
              id="home-address"
              type="text"
              placeholder="123 Main St, City"
              value={homeAddress}
              onChange={(event) => setHomeAddress(event.target.value)}
            />

            <label htmlFor="work-address">Work address</label>
            <input
              id="work-address"
              type="text"
              placeholder="456 Office Ave, City"
              value={workAddress}
              onChange={(event) => setWorkAddress(event.target.value)}
            />
          </>
        ) : null}

        <button
          type="submit"
          disabled={
            loading ||
            !username.trim() ||
            !password.trim() ||
            (mode === 'register' && (!homeAddress.trim() || !workAddress.trim()))
          }
        >
          {loading ? 'Please wait...' : mode === 'register' ? 'Create account' : 'Log in'}
        </button>
        {error ? <p className="error-text">{error}</p> : null}
      </form>
    </section>
  )
}