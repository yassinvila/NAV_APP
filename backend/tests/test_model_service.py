import pytest
from unittest.mock import patch
from app.services.model_service import ModelService, ModelServiceError
from app.config import get_settings

def test_parse_command_with_valid_place():
    service = ModelService(get_settings())

    # Mock the model output for "Starbucks"
    with patch.object(service, '_generate_model_text', return_value='{"intent": "navigate", "name": "Starbucks"}'):
        parsed_command = service.parse_command("take me to Starbucks")
        assert parsed_command.intent == "navigate_to_place"
        assert parsed_command.destination_name == "Starbucks"
        assert parsed_command.destination_category is None

def test_parse_command_with_invalid_schema():
    service = ModelService(get_settings())

    # Mock the model output with a category payload that should be preserved
    with patch.object(service, '_generate_model_text', return_value='{"intent": "navigate", "name": "Chick-fil-A", "category": "invalid_category"}'):
        parsed_command = service.parse_command("take me to Chick-fil-A")
        assert parsed_command.intent == "navigate_to_category"
        assert parsed_command.destination_name == "Chick-fil-A"
        assert parsed_command.destination_category == "invalid_category"

def test_parse_command_with_empty_output():
    service = ModelService(get_settings())

    # Mock the model output with empty response
    with patch.object(service, '_generate_model_text', return_value=''):
        with pytest.raises(ModelServiceError) as excinfo:
            service.parse_command("take me to nowhere")
        assert "Model generated empty output" in str(excinfo.value)