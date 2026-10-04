import { BACKEND_URL } from '../config'

const TOKEN_STORAGE_KEY = 'nav_access_token'

function authHeaders() {
  const token = window.localStorage.getItem(TOKEN_STORAGE_KEY)
  return token ? { Authorization: 'Bearer ' + token } : {}
}

function saveAuthResponse(response) {
  if (response.access_token) {
    window.localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token)
  }
  return response
}

export async function warmUpModel(modelKey = 'T5_NEMO') {
  const response = await fetch(`${BACKEND_URL}/models/warmup?model_key=${encodeURIComponent(modelKey)}`, {
    method: 'POST',
  })

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => null)
    const message = errorPayload?.detail || `Unable to warm up ${modelKey}.`
    throw new Error(message)
  }

  return response.json()
}

export async function getNavigationRoute(command, currentLocation, userId, modelKey) {
  const response = await fetch(`${BACKEND_URL}/navigation/route`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify({
      user_id: userId,
      text: command,
      current_location: currentLocation,
      model_key: modelKey,
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

export async function registerAccount(username, password, homeAddress, workAddress) {
  const response = await fetch(`${BACKEND_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      username,
      password,
      home_address: homeAddress,
      work_address: workAddress,
    }),
  })

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => null)
    const message = errorPayload?.detail || 'Unable to create account.'
    throw new Error(message)
  }

  return saveAuthResponse(await response.json())
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

  return saveAuthResponse(await response.json())
}

export async function updateUserProfile(userId, homeAddress, workAddress) {
  const response = await fetch(`${BACKEND_URL}/auth/profile`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify({
      user_id: userId,
      home_address: homeAddress,
      work_address: workAddress,
    }),
  })

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => null)
    const message = errorPayload?.detail || 'Unable to update profile.'
    throw new Error(message)
  }

  return saveAuthResponse(await response.json())
}

export async function fetchUserProfile(userId) {
  const response = await fetch(`${BACKEND_URL}/auth/profile/${userId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
  })

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => null)
    const message = errorPayload?.detail || 'Unable to fetch profile.'
    throw new Error(message)
  }

  return response.json()
}
