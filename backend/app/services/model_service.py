import json
import logging
from pathlib import Path
from dataclasses import dataclass
from difflib import get_close_matches
from functools import lru_cache
from typing import Any, cast

from app.config import get_settings
from app.schemas import ParsedCommand, Category

logger = logging.getLogger(__name__)




class ModelServiceError(RuntimeError):
    pass


@lru_cache(maxsize=4)
def _load_model_bundle(model_name_or_path: str, hf_token: str):
    try:
        from transformers import T5ForConditionalGeneration, T5TokenizerFast  # type: ignore[import-not-found]
        from huggingface_hub import login as hf_login
    except Exception as exc:  # pragma: no cover - import guard
        raise ModelServiceError(f"Transformers is unavailable: {exc}") from exc

    if not model_name_or_path:
        raise ModelServiceError("Model repo is not configured")

    if hf_token:
        try:
            hf_login(token=hf_token, add_to_git_credential=False)
        except Exception as exc:
            raise ModelServiceError(f"Hugging Face login failed: {exc}") from exc

    try:
        # Inspect the repo contents first to provide a clearer error when
        # the target repo is not a transformers-compatible model.
        repo_files = None
        try:
            from huggingface_hub import HfApi

            api = HfApi()
            try:
                repo_files = api.list_repo_files(model_name_or_path, token=hf_token or None)
            except Exception:
                repo_files = None

            if repo_files:
                has_model_file = any(
                    fn.endswith('pytorch_model.bin')
                    or fn.endswith('.bin')
                    or fn.endswith('.pt')
                    or fn.endswith('.safetensors')
                    for fn in repo_files
                ) or 'config.json' in repo_files or any('tokenizer' in fn for fn in repo_files)

                if not has_model_file:
                    sample = repo_files[:10] if isinstance(repo_files, list) else repo_files
                    raise ModelServiceError(
                        f"Model repository '{model_name_or_path}' does not appear to contain a PyTorch/transformers model. "
                        f"Found files: {sample}. Ensure the repo hosts a transformers-compatible T5 model or point T5_CLAUDE to a compatible repo."
                    )
        except Exception:
            # Non-fatal: if listing fails, we'll let from_pretrained raise the original error.
            pass

        model_path = Path(model_name_or_path)
        if repo_files and "quantized_model.pt" in repo_files and not model_path.is_dir():
            from huggingface_hub import snapshot_download

            model_path = Path(
                snapshot_download(
                    repo_id=model_name_or_path,
                    repo_type="model",
                    token=hf_token or None,
                )
            )

        try:
            tokenizer = T5TokenizerFast.from_pretrained(str(model_path), local_files_only=True)
        except Exception as exc:
            raise ModelServiceError(f"Tokenizer loading failed: {exc}") from exc

        quantized_checkpoint = model_path / "quantized_model.pt"
        if quantized_checkpoint.is_file():
            try:
                import torch

                model = torch.load(quantized_checkpoint, map_location="cpu", weights_only=False)
            except Exception as exc:
                raise ModelServiceError(f"Quantized checkpoint loading failed: {exc}") from exc
        else:
            try:
                model = T5ForConditionalGeneration.from_pretrained(
                    str(model_path),
                    local_files_only=True,
                )
            except Exception as exc:
                raise ModelServiceError(f"Transformers checkpoint loading failed: {exc}") from exc

        try:
            model.eval()
        except Exception as exc:
            raise ModelServiceError(f"Model initialization failed: {exc}") from exc
        return tokenizer, model
    except Exception as exc:
        raise ModelServiceError(f"Unable to load Hugging Face model '{model_name_or_path}': {exc}") from exc


@dataclass
class ModelService:
    """Adapter for the fine-tuned T5 parser."""

    settings: Any

    def _resolve_model_settings(self, model_key: str | None) -> tuple[str, str]:
        key = (model_key or self.settings.default_model_key or "T5_NEMO").strip().upper()
        if key == "T5_CLAUDE":
            return self.settings.t5_claude or self.settings.model_name_or_path, self.settings.hf_token_two or self.settings.hf_token
        return self.settings.t5_nemo or self.settings.model_name_or_path, self.settings.hf_token

    def warm_up(self, model_key: str) -> str:
        model_name_or_path, hf_token = self._resolve_model_settings(model_key)
        if not model_name_or_path:
            return "not_configured"

        _load_model_bundle(model_name_or_path, hf_token)
        return "ready"

    def parse_command(self, text: str, model_key: str | None = None) -> ParsedCommand:
        parsed_command, _ = self.parse_command_with_trace(text, model_key=model_key)
        return parsed_command

    def parse_command_with_trace(self, text: str, model_key: str | None = None) -> tuple[ParsedCommand, list[str]]:
        trace: list[str] = []
        try:
            raw_text = self._generate_model_text(text, model_key=model_key)
            trace.append(f"T5 raw response: {raw_text}")
            logger.info(f"Model raw output: {raw_text}")  # Log the raw output from the model
            if not raw_text or not raw_text.strip():
                raise ModelServiceError(f"Model generated empty output for input: '{text}'")
            raw_data = json.loads(raw_text)
            trace.append(f"Model payload parsed as JSON: {json.dumps(raw_data, ensure_ascii=False)}")
        except Exception as exc:
            logger.error(f"Error during model parsing: {exc}")  # Log the error
            raise ModelServiceError(f"Model parsing failed: {exc}") from exc

        try:
            parsed_command = self._coerce_command(raw_data)
            trace.append(f"Normalized parsed command: {json.dumps(parsed_command.model_dump(), ensure_ascii=False)}")
            logger.info(f"Parsed command: {parsed_command}")  # Log the parsed command
            return parsed_command, trace
        except Exception as exc:
            logger.error(f"Error during command coercion: {exc}")  # Log the error during coercion
            raise ModelServiceError(f"Model output did not match the expected schema: {exc}") from exc

    def _generate_model_text(self, text: str, model_key: str | None = None) -> str:
        model_name_or_path, hf_token = self._resolve_model_settings(model_key)
        tokenizer, model = _load_model_bundle(model_name_or_path, hf_token)
        try:
            import torch  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover - import guard
            raise ModelServiceError(f"PyTorch is unavailable: {exc}") from exc

        prompt = self._build_prompt(text)
        logger.info(f"Model input prompt: {prompt}")
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True)

        try:
            with torch.no_grad():
                generated_tokens = cast(Any, model).generate(
                    **inputs,
                    max_new_tokens=128,
                    early_stopping=False,
                )
        except Exception as exc:
            raise ModelServiceError(f"Model generation failed: {exc}") from exc

        raw_text = tokenizer.decode(generated_tokens[0], skip_special_tokens=True)
        logger.info(f"Model raw output: '{raw_text}'")
        
        if not raw_text or not raw_text.strip():
            raise ModelServiceError(f"Model generated empty output for input: '{text}'")
        
        # Convert custom format (key=value; key=value) to JSON if needed
        if "=" in raw_text and "{" not in raw_text:
            raw_text = self._convert_to_json(raw_text)
        
        return raw_text

    def _convert_to_json(self, formatted_text: str) -> str:
        """Convert key=value; key=value format to JSON."""
        pairs = {}
        for item in formatted_text.split(";"):
            item = item.strip()
            if "=" in item:
                key, value = item.split("=", 1)
                key = key.strip()
                value = value.strip()
                # Handle special values
                if value.lower() == "none":
                    pairs[key] = None
                elif value.lower() in ("true", "false"):
                    pairs[key] = value.lower() == "true"
                else:
                    pairs[key] = value
        # Map custom field names to expected schema field names
        mapped = {}
        if "intent" in pairs:
            mapped["intent"] = pairs["intent"]
        if "name" in pairs and pairs["name"] is not None:
            mapped["destination_name"] = pairs["name"]
        if "category" in pairs and pairs["category"] is not None:
            mapped["destination_category"] = pairs["category"]  # Pass category as-is
        if "selection" in pairs:
            mapped["selection_rule"] = pairs["selection"]
        return json.dumps(mapped)



    def _coerce_command(self, raw_data: dict[str, Any]) -> ParsedCommand:
        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)

        try:
            if "name" in raw_data and "destination_name" not in raw_data:
                raw_data["destination_name"] = raw_data.get("name")
            if "category" in raw_data and "destination_category" not in raw_data:
                raw_data["destination_category"] = raw_data.get("category")

            if raw_data.get("intent") == "navigate":
                if raw_data.get("destination_category"):
                    raw_data["intent"] = "navigate_to_category"
                else:
                    raw_data["intent"] = "navigate_to_place"

            # Allow any category to pass through without validation
            if "destination_category" in raw_data:
                raw_data["destination_category"] = raw_data.get("destination_category", None)

            # If category exists, send it to Mapbox; otherwise, treat as a location
            if not raw_data.get("destination_category"):
                logger.info(f"No valid category found. Treating as location search for: {raw_data.get('destination_name')}")
                raw_data["destination_category"] = None  # Clear category to trigger location search

            return ParsedCommand.model_validate(raw_data)
        except Exception as exc:
            logger.error(f"Error during command coercion: {exc}")
            raise ModelServiceError(f"Model output did not match the expected schema: {exc}") from exc

    def _build_prompt(self, text: str) -> str:
        prefix = getattr(self.settings, "model_input_prefix", "") or ""
        if prefix:
            return f"{prefix}{text.strip()}"
        return text.strip()


def get_model_service() -> ModelService:
    return ModelService(get_settings())
