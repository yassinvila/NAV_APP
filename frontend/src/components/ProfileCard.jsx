import { useEffect, useState } from 'react'

import { updateUserProfile, fetchUserProfile } from '../services/api'

export default function ProfileCard({ user, onProfileUpdate }) {
  const [isEditing, setIsEditing] = useState(false)
  const [homeAddress, setHomeAddress] = useState('')
  const [workAddress, setWorkAddress] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [initialLoading, setInitialLoading] = useState(true)

  useEffect(() => {
    if (!user?.user_id) return

    const loadProfile = async () => {
      try {
        const profile = await fetchUserProfile(user.user_id)
        setHomeAddress(profile.home_address || '')
        setWorkAddress(profile.work_address || '')
      } catch (err) {
        console.error('Failed to load profile:', err)
      } finally {
        setInitialLoading(false)
      }
    }

    loadProfile()
  }, [user?.user_id])

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    try {
      const response = await updateUserProfile(user.user_id, homeAddress, workAddress)
      setSuccess('Profile updated successfully')
      if (onProfileUpdate) {
        onProfileUpdate(response.user)
      }
      setIsEditing(false)
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (initialLoading) {
    return (
      <section className="auth-card">
        <div className="auth-badge">Your Profile</div>
        <h1>Loading...</h1>
      </section>
    )
  }

  return (
    <section className="auth-card">
      <div className="auth-badge">Your Profile</div>
      <h1>Account Settings</h1>

      {!isEditing ? (
        <div className="profile-view">
          <div className="profile-item">
            <label>Home Address</label>
            <p>{homeAddress || 'Not set'}</p>
          </div>
          <div className="profile-item">
            <label>Work Address</label>
            <p>{workAddress || 'Not set'}</p>
          </div>
          <button type="button" className="profile-action-button" onClick={() => setIsEditing(true)}>
            Edit Addresses
          </button>
        </div>
      ) : (
        <form className="auth-form" onSubmit={handleSubmit}>
          <label htmlFor="home-address">Home address</label>
          <input
            id="home-address"
            type="text"
            placeholder="123 Main St, City, State 12345"
            value={homeAddress}
            onChange={(event) => setHomeAddress(event.target.value)}
          />

          <label htmlFor="work-address">Work address</label>
          <input
            id="work-address"
            type="text"
            placeholder="456 Office Ave, City, State 12345"
            value={workAddress}
            onChange={(event) => setWorkAddress(event.target.value)}
          />

          <div className="button-row">
            <button type="submit" disabled={loading || !homeAddress.trim() || !workAddress.trim()}>
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
            <button type="button" className="ghost-button" onClick={() => setIsEditing(false)}>
              Cancel
            </button>
          </div>

          {error ? <p className="error-text">{error}</p> : null}
          {success ? <p className="success-text">{success}</p> : null}
        </form>
      )}
    </section>
  )
}
