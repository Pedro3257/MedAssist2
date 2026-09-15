"""Gera um manifesto verificável para a preparação da release candidate."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "release_candidate.json"
OUTPUT_PATH = ROOT / "reports" / "evidence" / "release_candidate_manifest.json"


def sha256(path: Path) -> str:
    """Calcula a assinatura SHA-256 de um arquivo sem carregá-lo inteiro."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest() -> dict[str, object]:
    """Valida os caminhos obrigatórios e descreve o estado da candidata."""
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    files = []
    missing = []

    for relative_name in config["required_paths"]:
        path = ROOT / relative_name
        if not path.is_file():
            missing.append(relative_name)
            continue
        files.append(
            {
                "path": relative_name,
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )

    blockers = list(config["open_blockers"])
    if missing:
        blockers.insert(0, "Adicionar os arquivos obrigatórios ausentes.")

    return {
        "schema_version": 1,
        "project": config["name"],
        "target_version": config["target_version"],
        "status": "preparation" if blockers else "ready_to_freeze",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "required_file_count": len(config["required_paths"]),
        "verified_file_count": len(files),
        "missing_paths": missing,
        "excluded_directories": config["excluded_directories"],
        "open_blockers": blockers,
        "files": files,
    }


def main() -> int:
    """Grava o manifesto e falha somente se faltar artefato obrigatório."""
    manifest = build_manifest()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Versão alvo: {manifest['target_version']}")
    print(f"Estado: {manifest['status']}")
    print(
        "Arquivos verificados: "
        f"{manifest['verified_file_count']}/{manifest['required_file_count']}"
    )
    print(f"Pendências de congelamento: {len(manifest['open_blockers'])}")
    print(f"Manifesto salvo em: {OUTPUT_PATH.relative_to(ROOT).as_posix()}")

    if manifest["missing_paths"]:
        for path in manifest["missing_paths"]:
            print(f"Arquivo ausente: {path}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
