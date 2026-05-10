import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from app.config import get_settings
from app.schemas import ParsedCommand


class ModelServiceError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _load_model_bundle(model_name_or_path: str):
    try:
        from transformers import T5ForConditionalGeneration, T5TokenizerFast  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - import guard
        raise ModelServiceError(f"Transformers is unavailable: {exc}") from exc

    if not model_name_or_path:
        raise ModelServiceError("MODEL_NAME_OR_PATH is not configured")

    try:
        tokenizer = T5TokenizerFast.from_pretrained(model_name_or_path)
        model = T5ForConditionalGeneration.from_pretrained(model_name_or_path)
        model.eval()
        return tokenizer, model
    except Exception as exc:
        raise ModelServiceError(f"Unable to load Hugging Face model '{model_name_or_path}': {exc}") from exc


@dataclass
class ModelService:
    """Adapter for the fine-tuned T5 parser."""

    settings: Any

    def parse_command(self, text: str) -> ParsedCommand:
        try:
            raw_text = self._generate_model_text(text)
            raw_data = json.loads(raw_text)
        except Exception as exc:
            raise ModelServiceError(f"Model parsing failed: {exc}") from exc

        return self._coerce_command(raw_data)

    def _generate_model_text(self, text: str) -> str:
        tokenizer, model = _load_model_bundle(self.settings.model_name_or_path)
        try:
            import torch  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover - import guard
            raise ModelServiceError(f"PyTorch is unavailable: {exc}") from exc

        prompt = self._build_prompt(text)
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True)

        with torch.no_grad():
            generated_tokens = model.generate(**inputs, max_new_tokens=128)

        return tokenizer.decode(generated_tokens[0], skip_special_tokens=True)

    def _coerce_command(self, raw_data: dict[str, Any]) -> ParsedCommand:
        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)

        try:
            return ParsedCommand.model_validate(raw_data)
        except Exception as exc:
            raise ModelServiceError(f"Model output did not match the expected schema: {exc}") from exc

    def _build_prompt(self, text: str) -> str:
        prefix = getattr(self.settings, "model_input_prefix", "") or ""
        if prefix:
            return f"{prefix}{text.strip()}"
        return text.strip()


def get_model_service() -> ModelService:
    return ModelService(get_settings())
