"""Upload a local model directory to Hugging Face.

Examples from the repository root:

    python backend/scripts/upload_model.py \
        --folder backend/models/nav_model_int8 \
        --repo yassinvila/nav_model_int8

    python backend/scripts/upload_model.py \
        --folder backend/models/nav_model_claude_int8 \
        --repo yassinvila/nav_model_claude_int8
"""

from __future__ import annotations

import argparse
from pathlib import Path

from huggingface_hub import HfApi, login, upload_folder


def upload_model(folder: Path, repo_id: str) -> None:
    folder = folder.expanduser().resolve()
    if not folder.is_dir():
        raise FileNotFoundError(f"Model folder does not exist: {folder}")

    required_files = ("config.json", "tokenizer.json", "quantized_model.pt")
    missing_files = [name for name in required_files if not (folder / name).is_file()]
    if missing_files:
        missing = ", ".join(missing_files)
        raise FileNotFoundError(f"Model folder is missing required files: {missing}")

    print(f"Logging in to Hugging Face...")
    login()
    print(f"Creating repository if needed: {repo_id}...")
    HfApi().create_repo(repo_id=repo_id, repo_type="model", exist_ok=True)
    print(f"Uploading {folder} to {repo_id}...")
    result = upload_folder(
        folder_path=str(folder),
        repo_id=repo_id,
        repo_type="model",
        commit_message="Upload quantized CPU INT8 model",
    )
    print(f"Upload complete: {result}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", required=True, type=Path, help="Local model directory to upload")
    parser.add_argument("--repo", required=True, help="Hugging Face model repository, such as username/model-name")
    args = parser.parse_args()
    upload_model(args.folder, args.repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
