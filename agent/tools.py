
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from data.database import Database


def _json_safe(value: Any):
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def list_tables(db: Database, **_: Any) -> dict:
    return {
        "tables": _json_safe(db.list_tables()),
        "count": len(db.list_tables()),
    }


def describe_table(db: Database, table_name: str, **_: Any) -> dict:
    return {
        "table_name": table_name,
        "columns": _json_safe(db.describe_table(table_name)),
    }


def run_query(db: Database, sql: str, max_rows: int = 500, **_: Any) -> dict:
    df = db.safe_query(sql, max_rows=max_rows)

    # Para a resposta do modelo, dados tabulares devem ser compactos.
    records = json.loads(df.to_json(orient="records", date_format="iso"))

    return {
        "row_count_returned": len(records),
        "columns": list(df.columns),
        "rows": _json_safe(records),
        "sql": sql,
    }


def summarize_table(db: Database, table_name: str, **_: Any) -> dict:
    if not db.table_exists(table_name):
        raise ValueError(f"Tabela inexistente: {table_name}")

    desc = db.describe_table(table_name)
    row = db.safe_query(
        f'SELECT COUNT(*) AS total_linhas FROM "{table_name}"'
    )

    return {
        "table_name": table_name,
        "columns": _json_safe(desc),
        "total_linhas": int(row.iloc[0]["total_linhas"]),
    }


def refresh_status(db: Database, **_: Any) -> dict:
    tables = db.list_tables()
    latest = None

    for table in tables:
        value = table.get("ingested_at")
        if value and (latest is None or value > latest):
            latest = value

    return {
        "tables": len(tables),
        "ultima_ingestao": _json_safe(latest),
        "status": "dados carregados" if tables else "nenhum dado carregado",
    }


TOOL_DECLARATIONS = [
    {
        "type": "function",
        "name": "list_tables",
        "description": (
            "Lista as tabelas disponíveis no banco analítico e as respectivas "
            "fontes. Use quando precisar descobrir onde estão os dados."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "type": "function",
        "name": "describe_table",
        "description": (
            "Mostra as colunas e tipos de uma tabela específica."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Nome exato da tabela.",
                }
            },
            "required": ["table_name"],
        },
    },
    {
        "type": "function",
        "name": "run_query",
        "description": (
            "Executa uma consulta SQL somente de leitura no DuckDB. "
            "Use SELECT ou WITH. Faça agregações e comparações aqui, "
            "não no texto do modelo."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "Uma única consulta SQL SELECT/WITH.",
                },
                "max_rows": {
                    "type": "integer",
                    "description": "Máximo de linhas retornadas, entre 1 e 500.",
                },
            },
            "required": ["sql"],
        },
    },
    {
        "type": "function",
        "name": "summarize_table",
        "description": "Resume uma tabela, mostrando colunas e quantidade de linhas.",
        "parameters": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Nome exato da tabela.",
                }
            },
            "required": ["table_name"],
        },
    },
    {
        "type": "function",
        "name": "refresh_status",
        "description": "Informa o estado e a data da última ingestão do banco.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
]


FUNCTIONS = {
    "list_tables": list_tables,
    "describe_table": describe_table,
    "run_query": run_query,
    "summarize_table": summarize_table,
    "refresh_status": refresh_status,
}
