import pytest
from unittest.mock import patch
from app.services.model_service import ModelService, ModelServiceError
from app.config import get_settings
import app.services.model_service as model_service_module

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


def test_generation_uses_explicit_compatible_options(monkeypatch):
    class FakeTokenizer:
        def __call__(self, prompt, return_tensors, truncation):
            return {"input_ids": [1]}

        def decode(self, tokens, skip_special_tokens):
            return '{"intent": "navigate_to_place", "name": "Empire State Building"}'

    class FakeModel:
        def eval(self):
            return self

        def generate(self, **kwargs):
            assert kwargs["max_length"] == 256
            assert kwargs["early_stopping"] is False
            assert kwargs["do_sample"] is False
            assert kwargs["num_beams"] == 1
            assert kwargs["length_penalty"] == 1.0
            return [[1]]

    monkeypatch.setattr(
        model_service_module,
        "_load_model_bundle",
        lambda model_name, token: (FakeTokenizer(), FakeModel()),
    )

    service = ModelService(get_settings())
    result = service.parse_command("take me to the Empire State Building")
    assert result.destination_name == "Empire State Building"