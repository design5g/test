"""Build-only shim that downloads the pinned public Qwen GGUF in verified ranges."""
from pathlib import Path
import subprocess


def hf_hub_download(*, repo_id: str, filename: str, local_dir: str, force_download: bool = False, **_: object) -> str:
    if repo_id != "Qwen/Qwen3-0.6B-GGUF" or filename != "Qwen3-0.6B-Q8_0.gguf":
        raise ValueError("Only the pinned Qwen model is permitted in this reproducible build")
    output = Path(local_dir) / filename
    subprocess.run(
        ["bash", "water-build-v5/download-qwen-ranges.sh", str(output)],
        check=True,
    )
    return str(output)
