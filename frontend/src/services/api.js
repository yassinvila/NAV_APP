import { BACKEND_URL } from '../config'

export async function getNavigationRoute(command, currentLocation, userId) {
  const response = await fetch(`${BACKEND_URL}/navigation/route`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: userId,
      text: command,
      current_location: currentLocation,
    }),
  })

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => null)
    const message = errorPayload?.detail || 'Unable to get navigation route.'
    throw new Error(message)
  }

  return response.json()
}

export async function validateBetaPin(pin) {
  const response = await fetch(`${BACKEND_URL}/auth/beta-pin`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ pin }),
  })

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => null)
    const message = errorPayload?.detail || 'Invalid beta access pin.'
    throw new Error(message)
  }

  return response.json()
}

export async function registerAccount(username, password) {
  const response = await fetch(`${BACKEND_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password }),
  })

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => null)
    const message = errorPayload?.detail || 'Unable to create account.'
    throw new Error(message)
  }

  return response.json()
}

export async function loginAccount(username, password) {
  const response = await fetch(`${BACKEND_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password }),
  })

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => null)
    const message = errorPayload?.detail || 'Unable to log in.'
    throw new Error(message)
  }

  return response.json()
}
