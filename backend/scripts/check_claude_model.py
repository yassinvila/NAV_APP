"""Check the Claude navigation model checkpoint and sample its output.

Run from the repository root:
    python backend/scripts/check_claude_model.py

Override the repository or prompts when needed:
    python backend/scripts/check_claude_model.py --model path/to/local/model
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any


DEFAULT_MODEL = "yassinvila/nav_model_claude"
DEFAULT_PROMPTS = (
    "take me to the Empire State Building",
    "find the nearest coffee shop",
    "take me home",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Hugging Face model ID or local path (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=128,
        help="Maximum generated tokens for each sample (default: 128)",
    )
    return parser.parse_args()


def print_checkpoint_report(config: Any, model: Any) -> None:
    expected_names = (
        "encoder.embed_tokens.weight",
        "decoder.embed_tokens.weight",
        "lm_head.weight",
    )
    state_dict = model.state_dict()

    print("\nCheckpoint configuration")
    print(f"  model_type: {getattr(config, 'model_type', 'unknown')}")
    print(f"  vocab_size: {getattr(config, 'vocab_size', 'unknown')}")
    print(f"  d_model: {getattr(config, 'd_model', 'unknown')}")
    print(f"  num_layers: {getattr(config, 'num_layers', 'unknown')}")
    print(f"  tie_word_embeddings: {getattr(config, 'tie_word_embeddings', 'unknown')}")

    print("\nEmbedding compatibility")
    for name in expected_names:
        print(f"  {name}: {'present' if name in state_dict else 'missing'}")
    print(f"  shared.weight: {'present' if 'shared.weight' in state_dict else 'missing'}")

    shared = getattr(model, "shared", None)
    encoder_embeddings = getattr(getattr(model, "encoder", None), "embed_tokens", None)
    decoder_embeddings = getattr(getattr(model, "decoder", None), "embed_tokens", None)
    lm_head = getattr(model, "lm_head", None)

    if shared is not None:
        shared_pointer = shared.weight.data_ptr()
        tied_names = [
            name
            for name, module in (
                ("shared.weight", shared),
                ("encoder.embed_tokens.weight", encoder_embeddings),
                ("decoder.embed_tokens.weight", decoder_embeddings),
                ("lm_head.weight", lm_head),
            )
            if module is not None and module.weight.data_ptr() == shared_pointer
        ]
        print(f"  tied to shared.weight: {', '.join(tied_names) or 'none'}")

    if getattr(config, "tie_word_embeddings", False) and "shared.weight" in state_dict:
        print("  assessment: shared T5 embedding is present; alias warnings are likely harmless.")
    else:
        print("  assessment: inspect the checkpoint carefully before relying on this model.")


def generate_samples(model: Any, tokenizer: Any, prompts: tuple[str, ...], max_new_tokens: int) -> None:
    import torch

    print("\nSample generation")
    model.eval()
    for prompt in prompts:
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True)
        with torch.no_grad():
            output_tokens = model.generate(**inputs, max_new_tokens=max_new_tokens)
        output = tokenizer.decode(output_tokens[0], skip_special_tokens=True)
        print(f"\n  prompt: {prompt}")
        print(f"  output: {output or '<empty>'}")
        try:
            parsed_output = json.loads(output)
            print(f"  format: valid JSON ({parsed_output})")
        except (json.JSONDecodeError, TypeError):
            normalized_output = normalize_key_value_output(output)
            if normalized_output is None:
                print("  format: unsupported (expected JSON or key=value pairs)")
            else:
                print(f"  format: valid key=value ({normalized_output})")


def normalize_key_value_output(output: str) -> dict[str, Any] | None:
    if not output or "=" not in output:
        return None

    pairs: dict[str, Any] = {}
    for item in output.split(";"):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value.lower() == "none":
            pairs[key] = None
        elif value.lower() in ("true", "false"):
            pairs[key] = value.lower() == "true"
        else:
            pairs[key] = value

    if not pairs:
        return None

    normalized: dict[str, Any] = {}
    if "intent" in pairs:
        normalized["intent"] = pairs["intent"]
    if "name" in pairs and pairs["name"] is not None:
        normalized["destination_name"] = pairs["name"]
    if "category" in pairs and pairs["category"] is not None:
        normalized["destination_category"] = pairs["category"]
    if "selection" in pairs:
        normalized["selection_rule"] = pairs["selection"]
    return normalized


def main() -> int:
    args = parse_args()

    try:
        from transformers import AutoConfig, T5ForConditionalGeneration, T5TokenizerFast
    except ImportError as exc:
        print(f"Transformers is not installed: {exc}", file=sys.stderr)
        return 1

    token = os.getenv("HF_TOKEN_TWO") or os.getenv("HF_TOKEN") or None
    print(f"Loading model: {args.model}")
    if token:
        print("Hugging Face authentication: token provided by environment")
    else:
        print("Hugging Face authentication: no token provided")

    try:
        config = AutoConfig.from_pretrained(args.model, token=token)
        tokenizer = T5TokenizerFast.from_pretrained(args.model, token=token)
        model = T5ForConditionalGeneration.from_pretrained(args.model, token=token)
    except Exception as exc:
        print(f"\nModel check failed: {exc}", file=sys.stderr)
        return 1

    print_checkpoint_report(config, model)
    generate_samples(model, tokenizer, DEFAULT_PROMPTS, args.max_new_tokens)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
