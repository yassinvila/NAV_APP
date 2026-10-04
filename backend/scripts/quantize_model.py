"""Create a CPU-friendly dynamic INT8 version of a T5 checkpoint.

Example:
    python backend/scripts/quantize_model.py \
        --model yassinvila/nav_model_claude \
        --output backend/models/nav_model_claude_int8

The output directory contains the tokenizer/configuration and a trusted
``quantized_model.pt`` file. It is intended for CPU inference only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from huggingface_hub import snapshot_download
from transformers import T5ForConditionalGeneration, T5TokenizerFast


def quantize_model(model_name_or_path: str, output_dir: Path) -> None:
    print(f"Loading model: {model_name_or_path}")
    source_path = Path(model_name_or_path)
    if not source_path.is_dir():
        source_path = Path(snapshot_download(model_name_or_path, repo_type="model"))

    source_tokenizer_config = source_path / "tokenizer_config.json"
    if source_tokenizer_config.is_file():
        tokenizer_config = json.loads(source_tokenizer_config.read_text(encoding="utf-8"))
        if isinstance(tokenizer_config.get("extra_special_tokens"), list):
            tokenizer_config.pop("extra_special_tokens")
            source_tokenizer_config.write_text(
                json.dumps(tokenizer_config, indent=2) + "\n",
                encoding="utf-8",
            )

    tokenizer = T5TokenizerFast.from_pretrained(str(source_path), local_files_only=True)
    model = T5ForConditionalGeneration.from_pretrained(str(source_path), local_files_only=True)
    model.eval()

    print("Applying dynamic INT8 quantization to linear layers...")
    quantized_model = torch.ao.quantization.quantize_dynamic(
        model,
        {torch.nn.Linear},
        dtype=torch.qint8,
    )
    quantized_model.eval()

    output_dir.mkdir(parents=True, exist_ok=True)
    tokenizer.save_pretrained(output_dir)
    model.config.save_pretrained(output_dir)
    torch.save(quantized_model, output_dir / "quantized_model.pt")
    print(f"Saved quantized model to: {output_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Hugging Face model ID or local model directory")
    parser.add_argument("--output", required=True, type=Path, help="Directory for the quantized checkpoint")
    args = parser.parse_args()
    quantize_model(args.model, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
