import { useState } from 'react'

export default function SearchBox({ onNavigate, loading, error, disabled = false, disabledReason = '', models }) {
  const [value, setValue] = useState('')
  const [selectedModel, setSelectedModel] = useState(models[0] || '')

  const handleSubmit = (event) => {
    event.preventDefault()
    onNavigate(value, selectedModel)
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
          disabled={disabled}
          onChange={(event) => setValue(event.target.value)}
        />
        <select
          className="model-select"
          aria-label="Model"
          value={selectedModel}
          onChange={(event) => setSelectedModel(event.target.value)}
          disabled={disabled || loading}
        >
          {models.map((model) => (
            <option key={model} value={model}>
              {model}
            </option>
          ))}
        </select>
        <button type="submit" disabled={disabled || loading || !value.trim()}>
          {loading ? 'Navigating...' : 'Navigate'}
        </button>
      </div>
      {disabled && disabledReason ? <p className="muted-text">{disabledReason}</p> : null}
      {error ? <p className="error-text">{error}</p> : null}
    </form>
  )
}
