
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import SETTINGS
from data.database import Database
from data.ingestion import ingest_drive


def main():
    print("=== SECAAE Analista V2 — sincronização ===")
    print(f"Banco: {SETTINGS.db_path}")

    db = Database(SETTINGS.db_path)

    try:
        stats = ingest_drive(
            db=db,
            folder_id=SETTINGS.drive_folder_id,
            folder_name=SETTINGS.drive_folder_name,
            recursive=SETTINGS.recursive_drive_scan,
            max_file_size_mb=SETTINGS.max_file_size_mb,
            progress_callback=print,
        )

        print("\n=== Resultado ===")
        for key, value in stats.items():
            print(f"{key}: {value}")

        if stats["errors"]:
            print("\n=== Erros ===")
            for error in stats["errors"]:
                print("-", error)

    finally:
        db.close()


if __name__ == "__main__":
    main()
