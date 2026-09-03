
from __future__ import annotations

import io
import os
from dataclasses import dataclass
from typing import Iterator

import google.auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

GOOGLE_SHEET_MIME = "application/vnd.google-apps.spreadsheet"
FOLDER_MIME = "application/vnd.google-apps.folder"

SUPPORTED_EXTENSIONS = {
    ".xlsx", ".xls", ".csv", ".tsv", ".parquet"
}


@dataclass
class DriveFile:
    id: str
    name: str
    mime_type: str
    modified_time: str | None = None
    size: int | None = None
    parents: list[str] | None = None


def get_drive_service():
    """
    Usa ADC.

    No Google Colab, o notebook chama google.colab.auth.authenticate_user()
    antes desta função.

    No Cloud Run, a identidade do serviço deve possuir acesso à pasta do Drive.
    """
    credentials, _ = google.auth.default(scopes=SCOPES)
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def _escape_drive_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def find_folder_by_name(service, name: str) -> str:
    q = (
        f"name = '{_escape_drive_value(name)}' "
        f"and mimeType = '{FOLDER_MIME}' "
        f"and trashed = false"
    )
    response = service.files().list(
        q=q,
        spaces="drive",
        fields="files(id,name,parents)",
        pageSize=50,
        orderBy="name",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
    ).execute()

    folders = response.get("files", [])
    if not folders:
        raise FileNotFoundError(f"Pasta do Drive não encontrada: {name}")

    return folders[0]["id"]


def resolve_folder_id(service, folder_id: str, folder_name: str) -> str:
    if folder_id:
        try:
            service.files().get(
                fileId=folder_id,
                fields="id,name,mimeType",
                supportsAllDrives=True,
            ).execute()
            return folder_id
        except HttpError as exc:
            raise RuntimeError(
                f"DRIVE_FOLDER_ID='{folder_id}' não pôde ser acessado. "
                "Verifique o ID e as permissões da conta/serviço."
            ) from exc

    return find_folder_by_name(service, folder_name)


def list_files(
    service,
    folder_id: str,
    recursive: bool = False,
) -> Iterator[DriveFile]:
    """
    Lista arquivos suportados na pasta.

    Por padrão, apenas filhos diretos são lidos. Com recursive=True,
    subpastas também são percorridas.
    """
    queue = [folder_id]
    visited = set()

    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)

        page_token = None
        while True:
            q = f"'{current}' in parents and trashed = false"
            response = service.files().list(
                q=q,
                spaces="drive",
                fields=(
                    "nextPageToken,files("
                    "id,name,mimeType,modifiedTime,size,parents)"
                ),
                pageSize=1000,
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                orderBy="name",
            ).execute()

            for item in response.get("files", []):
                mime = item.get("mimeType", "")
                if mime == FOLDER_MIME:
                    if recursive:
                        queue.append(item["id"])
                    continue

                suffix = os.path.splitext(item["name"])[1].lower()
                supported = suffix in SUPPORTED_EXTENSIONS or mime == GOOGLE_SHEET_MIME
                if not supported:
                    continue

                yield DriveFile(
                    id=item["id"],
                    name=item["name"],
                    mime_type=mime,
                    modified_time=item.get("modifiedTime"),
                    size=int(item["size"]) if item.get("size") else None,
                    parents=item.get("parents"),
                )

            page_token = response.get("nextPageToken")
            if not page_token:
                break


def download_file(service, drive_file: DriveFile) -> bytes:
    """
    Google Sheets são exportadas como XLSX.
    Arquivos binários são baixados com files.get(..., alt=media).
    """
    if drive_file.mime_type == GOOGLE_SHEET_MIME:
        request = service.files().export_media(
            fileId=drive_file.id,
            mimeType=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )
    else:
        request = service.files().get_media(
            fileId=drive_file.id,
            supportsAllDrives=True,
        )

    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False

    while not done:
        _, done = downloader.next_chunk()

    return buffer.getvalue()
