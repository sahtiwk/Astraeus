"""Explicit one-time model setup; never imported by the application."""
import argparse
import os
import re
from pathlib import Path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--revision",required=True,help="Full upstream model commit SHA")
    parser.add_argument("--output",default="models/embedding")
    args=parser.parse_args()
    if not re.fullmatch(r"[0-9a-fA-F]{40}",args.revision):
        parser.error("revision must be a full 40-character commit SHA")
    os.environ["HF_HUB_OFFLINE"]="0"
    from huggingface_hub import snapshot_download
    target=Path(args.output)
    snapshot_download(repo_id="sentence-transformers/all-MiniLM-L6-v2",
        revision=args.revision,local_dir=target,
        allow_patterns=["*.json","*.txt","*.safetensors","*.md","LICENSE*","1_Pooling/*"])
    (target/"astraeus-model-revision.txt").write_text(args.revision+"\n")
    print(f"Prepared local model at {target.resolve()}")

if __name__ == "__main__":
    main()
