
# Migração do Colab para Cloud Run

## 1. Pré-requisitos

- projeto Google Cloud;
- faturamento habilitado;
- Google Cloud CLI instalada;
- API Cloud Run e Cloud Build habilitadas;
- uma chave Gemini válida;
- pasta do Google Drive compartilhada com a conta de serviço usada pelo Cloud Run.

## 2. Habilitar APIs

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
```

## 3. Testar localmente

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## 4. Implantar

```bash
gcloud config set project SEU_PROJECT_ID
gcloud run deploy secaae-analista --source .
```

Quando solicitado:

- escolha a região;
- configure acesso de acordo com a política da organização.

## 5. Variáveis de ambiente

Configure:

```text
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.6-flash
DRIVE_FOLDER_ID=...
DB_PATH=/tmp/analytics.duckdb
```

### Observação sobre o DuckDB no Cloud Run

A V2 mantém DuckDB no filesystem do contêiner para simplificar a primeira migração.
O filesystem local do Cloud Run não deve ser tratado como armazenamento persistente.

Para produção, há duas opções:

1. executar uma sincronização na inicialização e manter a instância aquecida, aceitando
   o modelo efêmero;
2. evoluir para armazenamento persistente/objeto e um banco analítico apropriado.

Para uma primeira versão operacional, a opção 1 pode ser suficiente se a sincronização
for rápida e o volume de dados for moderado.

## 6. Conta de serviço

A identidade do Cloud Run precisa conseguir ler a pasta do Drive.

Se a pasta for de uma conta pessoal/organizacional, compartilhe a pasta com o e-mail
da conta de serviço, com permissão de leitor.

Se os dados estiverem em Shared Drive, configure `DRIVE_SHARED_DRIVE_ID` quando necessário.

## 7. Segredos

Não comite `.env` nem chaves no Git.

Para produção, prefira Secret Manager e injete o segredo no serviço Cloud Run.

## 8. Próxima evolução

Depois de validar o deploy:

- separar sincronização do Drive do serviço Streamlit;
- criar Cloud Scheduler → endpoint/job de sincronização;
- persistir os dados fora do filesystem efêmero;
- criar autenticação do usuário;
- adicionar logs e auditoria;
- adicionar métricas de uso.
