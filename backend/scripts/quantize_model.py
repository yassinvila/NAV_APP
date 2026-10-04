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
from pathlib import Path

import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer


def quantize_model(model_name_or_path: str, output_dir: Path) -> None:
    print(f"Loading model: {model_name_or_path}")
    tokenizer = T5Tokenizer.from_pretrained(model_name_or_path)
    model = T5ForConditionalGeneration.from_pretrained(model_name_or_path)
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
