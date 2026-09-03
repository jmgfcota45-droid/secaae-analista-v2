
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

DANGEROUS_SQL = re.compile(
    r"\b("
    r"insert|update|delete|drop|alter|create|replace|truncate|copy|attach|"
    r"detach|install|load|pragma|call|export|import|set|reset|vacuum"
    r")\b",
    re.IGNORECASE,
)

IDENTIFIER_RE = re.compile(r"[^0-9a-zA-Z_]+")


def normalize_identifier(value: str, fallback: str = "coluna") -> str:
    text = str(value).strip().lower()
    text = (
        text.replace("á", "a").replace("à", "a").replace("ã", "a")
        .replace("â", "a").replace("ä", "a")
        .replace("é", "e").replace("ê", "e").replace("ë", "e")
        .replace("í", "i").replace("ï", "i")
        .replace("ó", "o").replace("ô", "o").replace("õ", "o").replace("ö", "o")
        .replace("ú", "u").replace("ü", "u")
        .replace("ç", "c")
    )
    text = IDENTIFIER_RE.sub("_", text).strip("_")
    if not text:
        text = fallback
    if text[0].isdigit():
        text = f"c_{text}"
    return text[:120]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    seen: dict[str, int] = {}
    new_cols = []

    for col in df.columns:
        base = normalize_identifier(col)
        count = seen.get(base, 0)
        seen[base] = count + 1
        new_cols.append(base if count == 0 else f"{base}_{count+1}")

    result = df.copy()
    result.columns = new_cols
    return result


def table_name_from_source(filename: str, sheet_name: str | None = None) -> str:
    base = Path(filename).stem
    if sheet_name:
        base = f"{base}_{sheet_name}"
    return normalize_identifier(base, "tabela")[:150]


class Database:
    def __init__(self, path: str):
        self.path = str(Path(path))
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(self.path)
        self._ensure_catalog()

    def close(self):
        self.conn.close()

    def _ensure_catalog(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS _source_catalog (
                table_name VARCHAR PRIMARY KEY,
                source_file VARCHAR,
                source_id VARCHAR,
                source_mime_type VARCHAR,
                sheet_name VARCHAR,
                modified_time TIMESTAMP,
                row_count BIGINT,
                columns_json VARCHAR,
                ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def replace_table(
        self,
        df: pd.DataFrame,
        table_name: str,
        metadata: dict[str, Any],
    ):
        if df.empty:
            return

        df = normalize_columns(df)

        self.conn.register("_incoming_df", df)
        self.conn.execute(
            f'DROP TABLE IF EXISTS "{table_name}"'
        )
        self.conn.execute(
            f'CREATE TABLE "{table_name}" AS SELECT * FROM "_incoming_df"'
        )
        self.conn.unregister("_incoming_df")

        self.conn.execute(
            "DELETE FROM _source_catalog WHERE table_name = ?",
            [table_name],
        )
        self.conn.execute(
            """
            INSERT INTO _source_catalog (
                table_name, source_file, source_id, source_mime_type,
                sheet_name, modified_time, row_count, columns_json
            )
            VALUES (?, ?, ?, ?, ?, TRY_CAST(? AS TIMESTAMP), ?, ?)
            """,
            [
                table_name,
                metadata.get("source_file"),
                metadata.get("source_id"),
                metadata.get("source_mime_type"),
                metadata.get("sheet_name"),
                metadata.get("modified_time"),
                int(len(df)),
                json.dumps(list(df.columns), ensure_ascii=False),
            ],
        )

    def list_tables(self) -> list[dict[str, Any]]:
        rows = self.conn.execute("""
            SELECT table_name, source_file, sheet_name, row_count,
                   modified_time, ingested_at
            FROM _source_catalog
            ORDER BY source_file, sheet_name, table_name
        """).fetchall()

        columns = [
            "table_name", "source_file", "sheet_name", "row_count",
            "modified_time", "ingested_at"
        ]
        return [dict(zip(columns, row)) for row in rows]

    def describe_table(self, table_name: str) -> list[dict[str, Any]]:
        if not self.table_exists(table_name):
            raise ValueError(f"Tabela inexistente: {table_name}")

        rows = self.conn.execute(
            f'DESCRIBE "{table_name}"'
        ).fetchall()

        columns = ["column_name", "column_type", "null", "key", "default", "extra"]
        return [dict(zip(columns, row)) for row in rows]

    def table_exists(self, table_name: str) -> bool:
        result = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = ?
            """,
            [table_name],
        ).fetchone()[0]
        return bool(result)

    def safe_query(
        self,
        sql: str,
        max_rows: int = 500,
    ) -> pd.DataFrame:
        sql = sql.strip()

        if not sql:
            raise ValueError("Consulta SQL vazia.")

        if ";" in sql.rstrip(";"):
            raise ValueError("Somente uma instrução SQL é permitida.")

        normalized = sql.rstrip(";").strip()

        if not re.match(r"^(select|with)\b", normalized, re.IGNORECASE):
            raise ValueError("Apenas consultas SELECT/WITH são permitidas.")

        if DANGEROUS_SQL.search(normalized):
            raise ValueError("A consulta contém uma operação não permitida.")

        # Limita o resultado no nível externo.
        limited_sql = f"SELECT * FROM ({normalized}) AS _q LIMIT {int(max_rows)}"
        return self.conn.execute(limited_sql).df()

    def schema_context(self, max_tables: int = 80) -> str:
        tables = self.list_tables()[:max_tables]
        chunks = []

        for table in tables:
            name = table["table_name"]
            desc = self.describe_table(name)
            cols = ", ".join(
                f"{d['column_name']} ({d['column_type']})" for d in desc
            )
            chunks.append(
                f"- {name}: {cols} | linhas={table['row_count']} | "
                f"fonte={table['source_file']}"
            )

        return "\n".join(chunks) if chunks else "Nenhuma tabela foi carregada."
