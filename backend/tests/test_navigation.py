from types import SimpleNamespace

from app.routes.navigation import _build_destination_from_command
from app.schemas import Location, NavigationRequest, ParsedCommand


class FakeDatabaseService:
    def __init__(self):
        self.calls = []

    def get_saved_location(self, user_id, location_type):
        self.calls.append((user_id, location_type))
        return 40.7128, -74.0060


def test_home_command_uses_saved_home_coordinates():
    database_service = FakeDatabaseService()
    request_data = NavigationRequest(
        user_id=42,
        text="take me home",
        current_location=Location(latitude=40.7, longitude=-74.0),
    )
    trace = []

    destination = _build_destination_from_command(
        ParsedCommand(intent="navigate_home"),
        request_data,
        database_service,
        SimpleNamespace(),
        trace,
    )

    assert destination == ("Home", 40.7128, -74.006)
    assert database_service.calls == [(42, "home")]
    assert trace == ["Resolved saved home location"]
