
from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Callable

import pandas as pd

from data.database import Database, table_name_from_source
from data.drive import (
    GOOGLE_SHEET_MIME,
    DriveFile,
    download_file,
    get_drive_service,
    list_files,
    resolve_folder_id,
)


def _read_csv_bytes(data: bytes, filename: str) -> list[tuple[str, pd.DataFrame]]:
    for encoding in ("utf-8-sig", "cp1252", "latin1"):
        try:
            df = pd.read_csv(io.BytesIO(data), encoding=encoding, low_memory=False)
            return [(Path(filename).stem, df)]
        except UnicodeDecodeError:
            continue

    raise ValueError(f"Não foi possível decodificar CSV: {filename}")


def _read_tsv_bytes(data: bytes, filename: str) -> list[tuple[str, pd.DataFrame]]:
    df = pd.read_csv(io.BytesIO(data), sep="\t", encoding="utf-8-sig", low_memory=False)
    return [(Path(filename).stem, df)]


def _read_excel_bytes(data: bytes, filename: str) -> list[tuple[str, pd.DataFrame]]:
    workbook = pd.ExcelFile(io.BytesIO(data))
    result = []

    for sheet in workbook.sheet_names:
        df = workbook.parse(sheet)
        if not df.empty:
            result.append((sheet, df))

    return result


def _read_parquet_bytes(data: bytes, filename: str) -> list[tuple[str, pd.DataFrame]]:
    df = pd.read_parquet(io.BytesIO(data))
    return [(Path(filename).stem, df)]


def read_drive_file(drive_file: DriveFile, data: bytes):
    suffix = Path(drive_file.name).suffix.lower()

    if drive_file.mime_type == GOOGLE_SHEET_MIME or suffix in {".xlsx", ".xls"}:
        return _read_excel_bytes(data, drive_file.name)

    if suffix == ".csv":
        return _read_csv_bytes(data, drive_file.name)

    if suffix == ".tsv":
        return _read_tsv_bytes(data, drive_file.name)

    if suffix == ".parquet":
        return _read_parquet_bytes(data, drive_file.name)

    raise ValueError(f"Formato não suportado: {drive_file.name}")


def ingest_drive(
    db: Database,
    folder_id: str,
    folder_name: str = "Dashboard",
    recursive: bool = False,
    max_file_size_mb: int = 100,
    progress_callback: Callable[[str], None] | None = None,
) -> dict:
    service = get_drive_service()
    resolved_folder = resolve_folder_id(service, folder_id, folder_name)

    stats = {
        "folder_id": resolved_folder,
        "files_found": 0,
        "files_loaded": 0,
        "tables_loaded": 0,
        "rows_loaded": 0,
        "errors": [],
    }

    for drive_file in list_files(service, resolved_folder, recursive=recursive):
        stats["files_found"] += 1

        if drive_file.size and drive_file.size > max_file_size_mb * 1024 * 1024:
            stats["errors"].append(
                f"{drive_file.name}: arquivo excede {max_file_size_mb} MB"
            )
            continue

        try:
            if progress_callback:
                progress_callback(f"Baixando: {drive_file.name}")

            raw = download_file(service, drive_file)
            sheets = read_drive_file(drive_file, raw)

            file_loaded = False

            for sheet_name, df in sheets:
                if df is None or df.empty:
                    continue

                table_name = table_name_from_source(
                    drive_file.name,
                    sheet_name if len(sheets) > 1 or drive_file.mime_type == GOOGLE_SHEET_MIME else None,
                )

                if progress_callback:
                    progress_callback(
                        f"Carregando {table_name}: {len(df):,} linhas"
                    )

                db.replace_table(
                    df,
                    table_name,
                    {
                        "source_file": drive_file.name,
                        "source_id": drive_file.id,
                        "source_mime_type": drive_file.mime_type,
                        "sheet_name": sheet_name,
                        "modified_time": drive_file.modified_time,
                    },
                )

                stats["tables_loaded"] += 1
                stats["rows_loaded"] += len(df)
                file_loaded = True

            if file_loaded:
                stats["files_loaded"] += 1

        except Exception as exc:
            stats["errors"].append(f"{drive_file.name}: {type(exc).__name__}: {exc}")

    return stats
