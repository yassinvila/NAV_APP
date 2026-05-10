import { useState } from 'react'

export default function SearchBox({ onNavigate, loading, error }) {
  const [value, setValue] = useState('')

  const handleSubmit = (event) => {
    event.preventDefault()
    onNavigate(value)
  }

  return (
    <form className="search-box" onSubmit={handleSubmit}>
      <label className="search-label" htmlFor="navigation-command">
        Navigation command
      </label>
      <div className="search-row">
        <input
          id="navigation-command"
          type="text"
          placeholder="Where do you want to go?"
          value={value}
          onChange={(event) => setValue(event.target.value)}
        />
        <button type="submit" disabled={loading || !value.trim()}>
          {loading ? 'Navigating...' : 'Navigate'}
        </button>
      </div>
      {error ? <p className="error-text">{error}</p> : null}
    </form>
  )
}
