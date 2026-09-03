#!/usr/bin/env python
"""
Script de autenticação do Google Drive via OAuth2.
Gera credenciais salvas em ~/.config/gcloud/application_default_credentials.json
"""

import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import DefaultCredentialsError

# Escopos necessários (somente leitura)
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Diretório de credenciais (padrão gcloud)
CREDENTIALS_DIR = Path.home() / ".config" / "gcloud"
CREDENTIALS_FILE = CREDENTIALS_DIR / "application_default_credentials.json"

# Client ID padrão do Google Cloud (public/demo)
# Isto é um exemplo — em produção, usar credenciais da sua própria aplicação
CLIENT_CONFIG = {
    "installed": {
        "client_id": "764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com",
        "client_secret": "d-FL95Q19q7MQmFpd7hHD0Ty",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost"]
    }
}

def authenticate():
    """Faz autenticação OAuth2 e salva as credenciais."""

    # Criar diretório se não existir
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

    # Limpar credenciais antigas se existirem
    if CREDENTIALS_FILE.exists():
        print(f"[!] Removendo credenciais antigas: {CREDENTIALS_FILE}")
        CREDENTIALS_FILE.unlink()

    print("\n[AUTH] Iniciando autenticacao com o Google Drive...\n")
    print("Um navegador sera aberto. Faca login com sua conta Google e autorize o acesso.\n")

    try:
        # Criar o flow OAuth2
        flow = InstalledAppFlow.from_client_config(
            CLIENT_CONFIG,
            scopes=SCOPES,
            redirect_uri="http://localhost"
        )

        # Executar flow (abre navegador)
        credentials = flow.run_local_server(port=8080, open_browser=True)

        # Preparar credenciais no formato ADC
        adc_credentials = {
            "type": "authorized_user",
            "client_id": CLIENT_CONFIG["installed"]["client_id"],
            "client_secret": CLIENT_CONFIG["installed"]["client_secret"],
            "refresh_token": credentials.refresh_token,
        }

        # Salvar credenciais
        with open(CREDENTIALS_FILE, "w") as f:
            json.dump(adc_credentials, f, indent=2)

        os.chmod(CREDENTIALS_FILE, 0o600)  # Restringir permissões (Unix-like)

        print(f"\n[OK] Autenticacao bem-sucedida!")
        print(f"   Credenciais salvas em: {CREDENTIALS_FILE}\n")

        return credentials

    except Exception as e:
        print(f"\n[ERROR] Erro durante autenticacao: {e}\n")
        raise

if __name__ == "__main__":
    authenticate()
