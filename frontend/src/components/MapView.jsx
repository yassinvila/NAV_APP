import { useEffect, useRef } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'

import { MAPBOX_TOKEN } from '../config'

function toLineStringGeometry(routeGeometry) {
  if (!routeGeometry) return null
  if (routeGeometry.type === 'LineString') return routeGeometry
  if (routeGeometry.geometry?.type === 'LineString') return routeGeometry.geometry
  if (routeGeometry.coordinates && Array.isArray(routeGeometry.coordinates)) {
    return {
      type: 'LineString',
      coordinates: routeGeometry.coordinates,
    }
  }
  return null
}

export default function MapView({ currentLocation, destination, routeGeometry }) {
  const mapContainerRef = useRef(null)
  const mapRef = useRef(null)
  const userMarkerRef = useRef(null)
  const destinationMarkerRef = useRef(null)

  useEffect(() => {
    if (!MAPBOX_TOKEN || !mapContainerRef.current || mapRef.current) return

    mapboxgl.accessToken = MAPBOX_TOKEN
    mapRef.current = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: currentLocation ? [currentLocation.longitude, currentLocation.latitude] : [-73.9442, 40.6782],
      zoom: currentLocation ? 13 : 11,
    })

    mapRef.current.addControl(new mapboxgl.NavigationControl(), 'top-right')

    return () => {
      mapRef.current?.remove()
      mapRef.current = null
    }
  }, [currentLocation])

  useEffect(() => {
    if (!mapRef.current || !currentLocation) return

    if (userMarkerRef.current) {
      userMarkerRef.current.remove()
    }

    userMarkerRef.current = new mapboxgl.Marker({ color: '#1d4ed8' })
      .setLngLat([currentLocation.longitude, currentLocation.latitude])
      .addTo(mapRef.current)

    mapRef.current.easeTo({
      center: [currentLocation.longitude, currentLocation.latitude],
      zoom: 13,
    })
  }, [currentLocation])

  useEffect(() => {
    if (!mapRef.current) return

    if (destinationMarkerRef.current) {
      destinationMarkerRef.current.remove()
      destinationMarkerRef.current = null
    }

    if (!destination) return

    destinationMarkerRef.current = new mapboxgl.Marker({ color: '#ef4444' })
      .setLngLat([destination.longitude, destination.latitude])
      .addTo(mapRef.current)
  }, [destination])

  useEffect(() => {
    if (!mapRef.current || !currentLocation) return

    const map = mapRef.current
    const lineGeometry = toLineStringGeometry(routeGeometry)

    const removeRouteLayer = () => {
      if (map.getLayer('route-line')) {
        map.removeLayer('route-line')
      }
      if (map.getSource('route')) {
        map.removeSource('route')
      }
    }

    removeRouteLayer()

    if (!lineGeometry) return

    map.addSource('route', {
      type: 'geojson',
      data: {
        type: 'Feature',
        geometry: lineGeometry,
        properties: {},
      },
    })

    map.addLayer({
      id: 'route-line',
      type: 'line',
      source: 'route',
      layout: {
        'line-join': 'round',
        'line-cap': 'round',
      },
      paint: {
        'line-color': '#f59e0b',
        'line-width': 5,
      },
    })

    const bounds = new mapboxgl.LngLatBounds()
    bounds.extend([currentLocation.longitude, currentLocation.latitude])
    if (destination) {
      bounds.extend([destination.longitude, destination.latitude])
    }

    map.fitBounds(bounds, { padding: 80, duration: 900 })
  }, [currentLocation, destination, routeGeometry])

  return <div ref={mapContainerRef} className="map-container" />
}
