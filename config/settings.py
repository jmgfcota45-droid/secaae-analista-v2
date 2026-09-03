
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "sim", "on"}


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    drive_folder_id: str = os.getenv("DRIVE_FOLDER_ID", "")
    drive_folder_name: str = os.getenv("DRIVE_FOLDER_NAME", "Dashboard")
    drive_shared_drive_id: str = os.getenv("DRIVE_SHARED_DRIVE_ID", "")

    db_path: str = os.getenv(
        "DB_PATH", str(PROJECT_ROOT / "data" / "analytics.duckdb")
    )

    recursive_drive_scan: bool = _bool("RECURSIVE_DRIVE_SCAN", False)
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "100"))

    max_tool_rounds: int = int(os.getenv("MAX_TOOL_ROUNDS", "8"))
    max_query_rows: int = int(os.getenv("MAX_QUERY_ROWS", "500"))


SETTINGS = Settings()

# Aliases comuns. Não substituem a inspeção real do esquema.
COLUMN_ALIASES = {
    "exercicio": [
        "exercicio", "ano", "ano_exercicio", "ano exercício", "exercise_year"
    ],
    "mes": ["mes", "mês", "month", "mes_referencia", "mês referência"],
    "ug": [
        "ug", "ug_responsavel", "ug responsável", "unidade_gestora",
        "unidade gestora", "codigo_ug", "código ug"
    ],
    "po": ["po", "plano_orcamentario", "plano orçamentário", "plano_orcamentario_codigo"],
    "natureza_despesa": [
        "natureza_despesa", "natureza da despesa", "nd", "natureza", "ndesp"
    ],
    "empenho": ["empenho", "valor_empenhado", "valor empenhado", "empenhado"],
    "liquidacao": [
        "liquidacao", "liquidação", "valor_liquidado", "valor liquidado", "liquidado"
    ],
    "pagamento": [
        "pagamento", "pagamentos", "valor_pago", "valor pago", "pago"
    ],
    "credito": [
        "credito", "crédito", "credito_disponivel", "crédito disponível",
        "saldo_credito", "saldo crédito"
    ],
}
