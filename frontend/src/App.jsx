import { useEffect, useState } from 'react'

import AuthGate from './components/AuthGate'
import BetaPinGate from './components/BetaPinGate'
import MapView from './components/MapView'
import ProfileCard from './components/ProfileCard'
import DebugPanel from './components/DebugPanel'
import RouteInfo from './components/RouteInfo'
import SearchBox from './components/SearchBox'
import { DEFAULT_USER_ID, MODEL_OPTIONS } from './config'
import { getNavigationRoute, warmUpModel } from './services/api'
import './styles/App.css'

const BETA_STORAGE_KEY = 'nav_beta_granted'
const USER_STORAGE_KEY = 'nav_user'
const TOKEN_STORAGE_KEY = 'nav_access_token'

function readStoredUser() {
  try {
    const storedUser = window.localStorage.getItem(USER_STORAGE_KEY)
    return storedUser ? JSON.parse(storedUser) : null
  } catch {
    return null
  }
}

function App() {
  const [betaGranted, setBetaGranted] = useState(() => window.localStorage.getItem(BETA_STORAGE_KEY) === 'true')
  const [authUser, setAuthUser] = useState(() => readStoredUser())
  const [accessModalOpen, setAccessModalOpen] = useState(false)
  const [modalView, setModalView] = useState('auth') // 'auth' or 'profile'
  const [currentLocation, setCurrentLocation] = useState(null)
  const [locationError, setLocationError] = useState(() =>
    navigator.geolocation ? '' : 'Browser geolocation is not supported in this browser.',
  )
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [parsedCommand, setParsedCommand] = useState(null)
  const [destination, setDestination] = useState(null)
  const [route, setRoute] = useState(null)
  const [routeGeometry, setRouteGeometry] = useState(null)
  const [debugTrace, setDebugTrace] = useState([])
  const [modelWarmupError, setModelWarmupError] = useState('')

  const handleBetaAccessGranted = () => {
    window.localStorage.setItem(BETA_STORAGE_KEY, 'true')
    setBetaGranted(true)
  }

  const handleAuthSuccess = (user) => {
    window.localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user))
    setAuthUser(user)
    setAccessModalOpen(false)
    setModalView('auth')
  }

  const handleLogout = () => {
    window.localStorage.removeItem(USER_STORAGE_KEY)
    window.localStorage.removeItem(TOKEN_STORAGE_KEY)
    setAuthUser(null)
  }

  const handleProfileUpdate = (updatedUser) => {
    window.localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(updatedUser))
    setAuthUser(updatedUser)
  }

  useEffect(() => {
    let active = true

    warmUpModel('T5_NEMO')
      .then((statuses) => {
        const failedModels = Object.entries(statuses)
          .filter(([, result]) => result.status === 'error')
          .map(([model, result]) => `${model}: ${result.message}`)

        if (active && failedModels.length > 0) {
          setModelWarmupError(`Model warm-up issue — ${failedModels.join(' | ')}`)
        }
      })
      .catch((warmupError) => {
        if (active) setModelWarmupError(warmupError.message)
      })

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (!authUser || !navigator.geolocation) return

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setCurrentLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        })
        setLocationError('')
      },
      () => {
        setLocationError('Unable to access your current location. Please allow location access and try again.')
      },
      { enableHighAccuracy: true, timeout: 10000 },
    )
  }, [authUser])

  const handleNavigate = async (command, model) => {
    if (!currentLocation) {
      setError('Current location is missing. Allow browser location access first.')
      return
    }

    setLoading(true)
    setError('')
    setDebugTrace([
      `Submitted command: ${command}`,
      `Model selected: ${model}`,
      'Sending request to backend...',
    ])

    try {
      const response = await getNavigationRoute(
        command,
        currentLocation,
        authUser?.user_id || DEFAULT_USER_ID,
        model
      )
      setParsedCommand(response.parsed_command)
      setDestination(response.destination)
      setRoute(response.route)
      setRouteGeometry(response.route?.geometry || null)
      setDebugTrace((previousTrace) => [
        ...previousTrace,
        ...(response.debug_trace || []),
        'Route response rendered in the UI.',
      ])
    } catch (navigationError) {
      if (
        navigationError.message &&
        navigationError.message.toLowerCase().includes('destination_category is required for navigate_to_category')
      ) {
        try {
          const fallbackInput = `take me to ${command}`
          const response = await getNavigationRoute(
            fallbackInput,
            currentLocation,
            authUser?.user_id || DEFAULT_USER_ID,
            model
          )
          setParsedCommand(response.parsed_command)
          setDestination(response.destination)
          setRoute(response.route)
          setRouteGeometry(response.route?.geometry || null)
          setDebugTrace((previousTrace) => [
            ...previousTrace,
            `Fallback command used: ${fallbackInput}`,
            ...(response.debug_trace || []),
            'Route response rendered in the UI.',
          ])
          setError('')
          return
        } catch (err2) {
          setError(err2.message)
          setDebugTrace((previousTrace) => [...previousTrace, `Fallback failed: ${err2.message}`])
        }
      } else {
        setError(navigationError.message)
        setDebugTrace((previousTrace) => [...previousTrace, `Request failed: ${navigationError.message}`])
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="app-shell">
      <section className="hero-panel">
        <div className="brand-row">
          <div className="brand-chip">Natural Language Navigation</div>
          <div className="header-buttons">
            {authUser ? (
              <>
                <button
                  type="button"
                  className="logout-button"
                  onClick={() => {
                    setModalView('profile')
                    setAccessModalOpen(true)
                  }}
                >
                  Profile
                </button>
                <button type="button" className="logout-button" onClick={handleLogout}>
                  Log out
                </button>
              </>
            ) : (
              <button
                type="button"
                className="logout-button"
                onClick={() => {
                  setModalView('auth')
                  setAccessModalOpen(true)
                }}
              >
                Log in
              </button>
            )}
          </div>
        </div>
        <h1>Speak a destination, get a route.</h1>
      </section>

      <section className="map-stage">
        <MapView currentLocation={currentLocation} destination={destination} routeGeometry={routeGeometry} />

        <section className="overlay control-overlay">
          <SearchBox
            onNavigate={handleNavigate}
            loading={loading}
            error={error}
            disabled={!authUser}
            disabledReason="Log in to enable destination input."
            models={MODEL_OPTIONS}
          />
          <RouteInfo route={route} destination={destination} />
          <DebugPanel debugTrace={debugTrace} />
          {locationError ? <p className="error-text">{locationError}</p> : null}
          {modelWarmupError ? <p className="error-text">{modelWarmupError}</p> : null}
          {parsedCommand ? <p className="muted-text">Intent: {parsedCommand.intent}</p> : null}
        </section>
      </section>

      <section className="about-section">
        <div className="about-copy">
          <span className="section-eyebrow">Research prototype</span>
          <h2>Exploring a lower-cost path to task-specific AI.</h2>
          <p>
            Natural Language Navigation is a first-iteration research prototype. It explores whether
            models can be trained to perform useful tasks with synthetically generated examples instead
            of relying entirely on large collections of human-created data.
          </p>
          <p>
            Training a model is expensive not only because of GPU time. Teams also spend substantial
            effort collecting, licensing, labeling, reviewing, deduplicating, and cleaning data before
            training can begin. Synthetic data can help reduce some of those costs by generating
            targeted examples for a specific task, while still requiring careful evaluation to make
            sure the generated data is accurate, diverse, and useful.
          </p>
          <p>
            This navigation experience demonstrates that idea in one focused domain: a model interprets
            a natural-language request, then mapping services turn that interpretation into a route. It
            is part of a larger effort to investigate whether a model can be adapted to many different
            tasks without depending on human data for every new capability. The prototype is not a
            finished training system; it is a working experiment for testing the approach.
          </p>
        </div>
        <div className="about-stack">
          <h3>What this project is built with</h3>
          <p>
            The frontend is built with React and Vite for the interface, map experience, authentication
            flow, and route display. FastAPI and Python power the backend API, model orchestration,
            account features, and saved locations. Hugging Face Transformers provides the T5-based
            language models that interpret natural-language navigation commands. Mapbox handles
            geocoding, category search, interactive maps, and route geometry, while SQLAlchemy and
            PostgreSQL provide the database layer for accounts and saved home and work locations.
            SQLite is also available for local development.
          </p>
        </div>
      </section>

      {accessModalOpen ? (
        <section className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Access and login">
          <div className="modal-wrap">
            <button type="button" className="modal-close" onClick={() => setAccessModalOpen(false)}>
              Close
            </button>
            {!betaGranted ? (
              <BetaPinGate onAccessGranted={handleBetaAccessGranted} />
            ) : modalView === 'profile' ? (
              <ProfileCard user={authUser} onProfileUpdate={handleProfileUpdate} />
            ) : (
              <AuthGate onAuthSuccess={handleAuthSuccess} />
            )}
          </div>
        </section>
      ) : null}
    </main>
  )
}

export default App
