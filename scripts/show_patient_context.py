#!/usr/bin/env python3
"""Consulta e exibe o contexto estruturado de um paciente sintético."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path

import psycopg

from medassist.infrastructure.config import load_env_file
from medassist.infrastructure.postgres_patient_repository import (
    PostgresPatientRepository,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    """Lê o identificador do paciente informado no terminal."""
    parser = argparse.ArgumentParser(
        description="Consulta o contexto sintético de um paciente."
    )
    parser.add_argument(
        "patient_id",
        help="Identificador no formato PAT-000",
    )
    return parser.parse_args()


def main() -> None:
    """Conecta ao PostgreSQL e apresenta o contexto em formato JSON."""
    args = parse_args()
    load_env_file(PROJECT_ROOT / ".env")

    with psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "medassist"),
        user=os.getenv("POSTGRES_USER", "medassist"),
        password=os.environ["POSTGRES_PASSWORD"],
    ) as connection:
        context = PostgresPatientRepository(
            connection
        ).get_by_id(args.patient_id)

    if context is None:
        print(
            f"Paciente {args.patient_id.upper()} não encontrado."
        )
        return

    print(
        json.dumps(
            asdict(context),
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )

    print()
    print(f"Paciente: {context.patient.patient_id}")
    print(f"Atendimentos: {len(context.encounters)}")
    print(f"Exames concluídos: {len(context.exams)}")
    print(f"Exames pendentes: {len(context.pending_exams)}")
    print(
        "Possui exames pendentes:",
        context.has_pending_exams,
    )


if __name__ == "__main__":
    main()