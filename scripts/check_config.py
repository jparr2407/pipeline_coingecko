from __future__ import annotations

import os
import sys
from pathlib import Path


REQUIRED_KEYS = [
    "COINGECKO_API_KEY",
    "COINGECKO_API_TIER",
    "WAREHOUSE_DB",
    "WAREHOUSE_USER",
    "WAREHOUSE_PASSWORD",
]


def load_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def main() -> int:
    env_values = load_dotenv(Path(".env"))
    merged = {key: os.getenv(key, env_values.get(key, "")) for key in REQUIRED_KEYS}
    missing = [key for key, value in merged.items() if not value]

    if missing:
        print("Configuracao incompleta. Preencha estes campos no .env:")
        for key in missing:
            print(f"- {key}")
        return 1

    tier = merged["COINGECKO_API_TIER"].lower()
    if tier not in {"demo", "pro"}:
        print("COINGECKO_API_TIER deve ser 'demo' ou 'pro'.")
        return 1

    print("Configuracao minima OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
