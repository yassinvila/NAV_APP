from dataclasses import dataclass
from math import atan2, cos, radians, sin, sqrt
from typing import Any

import requests

from app.config import get_settings
from app.schemas import DestinationCandidate


class MapboxServiceError(RuntimeError):
    pass


@dataclass
class MapboxService:
    settings: Any

    def geocode_place(self, destination_name: str) -> DestinationCandidate:
        url = f"{self.settings.mapbox_geocoding_url}/{requests.utils.quote(destination_name)}.json"
        params = {
            "access_token": self.settings.mapbox_access_token,
            "limit": 1,
        }
        data = self._request_json(url, params)
        return self._first_candidate(data, destination_name)

    def search_category(
        self,
        category: str,
        latitude: float,
        longitude: float,
        selection_rule: str,
    ) -> DestinationCandidate:
        url = f"{self.settings.mapbox_geocoding_url}/{requests.utils.quote(category)}.json"
        params = {
            "access_token": self.settings.mapbox_access_token,
            "proximity": f"{longitude},{latitude}",
            "limit": 10,
            "types": "poi",
        }
        data = self._request_json(url, params)
        features = data.get("features", [])
        if not features:
            raise MapboxServiceError(f"No results found for category '{category}'")

        candidates = [self._feature_to_candidate(feature) for feature in features]
        if selection_rule == "nearest":
            return min(candidates, key=lambda candidate: self._distance_km(latitude, longitude, candidate.latitude, candidate.longitude))
        if selection_rule == "best":
            return max(candidates, key=lambda candidate: candidate.relevance or 0.0)
        return candidates[0]

    def route(self, origin: tuple[float, float], destination: tuple[float, float]) -> dict[str, Any]:
        origin_lat, origin_lon = origin
        destination_lat, destination_lon = destination
        coordinates = f"{origin_lon},{origin_lat};{destination_lon},{destination_lat}"
        url = f"{self.settings.mapbox_directions_url}/{coordinates}"
        params = {
            "access_token": self.settings.mapbox_access_token,
            "geometries": "geojson",
            "overview": "full",
            "steps": "true",
        }
        data = self._request_json(url, params)
        routes = data.get("routes", [])
        if not routes:
            raise MapboxServiceError("Mapbox Directions API returned no routes")

        route = routes[0]
        return {
            "distance": route.get("distance", 0),
            "duration": route.get("duration", 0),
            "geometry": route.get("geometry", {}),
        }

    def _request_json(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.mapbox_access_token:
            raise MapboxServiceError("MAPBOX_ACCESS_TOKEN is not configured")

        try:
            response = requests.get(url, params=params, timeout=self.settings.request_timeout_seconds)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise MapboxServiceError(f"Mapbox request failed: {exc}") from exc
        except ValueError as exc:
            raise MapboxServiceError("Mapbox response was not valid JSON") from exc

    def _first_candidate(self, data: dict[str, Any], fallback_name: str) -> DestinationCandidate:
        features = data.get("features", [])
        if not features:
            raise MapboxServiceError(f"No geocoding results found for '{fallback_name}'")
        return self._feature_to_candidate(features[0])

    def _feature_to_candidate(self, feature: dict[str, Any]) -> DestinationCandidate:
        center = feature.get("center") or feature.get("geometry", {}).get("coordinates")
        if not center or len(center) < 2:
            raise MapboxServiceError("Mapbox feature did not include coordinates")
        return DestinationCandidate(
            name=feature.get("place_name") or feature.get("text") or "Unknown destination",
            latitude=center[1],
            longitude=center[0],
            relevance=feature.get("relevance"),
            raw=feature,
        )

    def _distance_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        earth_radius_km = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return earth_radius_km * c


def get_mapbox_service() -> MapboxService:
    return MapboxService(get_settings())
