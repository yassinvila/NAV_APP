import { useEffect, useState } from 'react'

import AuthGate from './components/AuthGate'
import BetaPinGate from './components/BetaPinGate'
import DebugPanel from './components/DebugPanel'
import MapView from './components/MapView'
import RouteInfo from './components/RouteInfo'
import SearchBox from './components/SearchBox'
import { DEFAULT_USER_ID } from './config'
import { getNavigationRoute } from './services/api'
import './styles/App.css'

const BETA_STORAGE_KEY = 'nav_beta_granted'
const USER_STORAGE_KEY = 'nav_user'

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

  const handleBetaAccessGranted = () => {
    window.localStorage.setItem(BETA_STORAGE_KEY, 'true')
    setBetaGranted(true)
  }

  const handleAuthSuccess = (user) => {
    window.localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user))
    setAuthUser(user)
  }

  const handleLogout = () => {
    window.localStorage.removeItem(USER_STORAGE_KEY)
    setAuthUser(null)
  }

  const handleResetBetaAccess = () => {
    window.localStorage.removeItem(BETA_STORAGE_KEY)
    window.localStorage.removeItem(USER_STORAGE_KEY)
    setBetaGranted(false)
    setAuthUser(null)
  }

  useEffect(() => {
    if (!betaGranted || !authUser || !navigator.geolocation) return

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
  }, [betaGranted, authUser])

  const handleNavigate = async (command) => {
    if (!currentLocation) {
      setError('Current location is missing. Allow browser location access first.')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await getNavigationRoute(command, currentLocation, authUser?.user_id || DEFAULT_USER_ID)
      setParsedCommand(response.parsed_command)
      setDestination(response.destination)
      setRoute(response.route)
      setRouteGeometry(response.route?.geometry || null)
    } catch (navigationError) {
      setError(navigationError.message)
    } finally {
      setLoading(false)
    }
  }

  if (!betaGranted) {
    return <BetaPinGate onAccessGranted={handleBetaAccessGranted} />
  }

  if (!authUser) {
    return <AuthGate onAuthSuccess={handleAuthSuccess} onLogout={handleResetBetaAccess} />
  }

  return (
    <main className="app-shell">
      <MapView currentLocation={currentLocation} destination={destination} routeGeometry={routeGeometry} />

      <section className="overlay top-overlay">
        <div className="brand-row">
          <div className="brand-chip">Natural Language Navigation</div>
          <button type="button" className="logout-button" onClick={handleLogout}>
            Log out
          </button>
        </div>
        <h1>Speak a destination, get a route.</h1>
        <p>The backend handles model parsing, Mapbox geocoding, directions, and saved locations.</p>
        {locationError ? <p className="error-text">{locationError}</p> : null}
      </section>

      <section className="overlay control-overlay">
        <SearchBox onNavigate={handleNavigate} loading={loading} error={error} />
        <RouteInfo route={route} destination={destination} />
      </section>

      <section className="overlay debug-overlay">
        <DebugPanel parsedCommand={parsedCommand} destination={destination} route={route} />
      </section>
    </main>
  )
}

export default App
