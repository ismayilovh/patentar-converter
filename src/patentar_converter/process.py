import os
import subprocess
from collections.abc import Sequence


def run_backend(command: Sequence[str]) -> None:
    timeout = int(os.getenv("PATENTAR_CONVERTER_TIMEOUT_SECONDS", "900"))
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"conversion executable is unavailable: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"conversion exceeded {timeout} seconds") from exc

    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()[-2000:]
        raise RuntimeError(
            f"{command[0]} exited with code {result.returncode}: {detail or 'no output'}"
        )
