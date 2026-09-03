
# SECAAE Analista V2

Assistente analítico para consultar dados do Google Drive em linguagem natural.

## Arquitetura

Google Drive → ingestão Python → DuckDB → ferramentas SQL/analíticas → Gemini 3.6 Flash → Streamlit

O Gemini interpreta a pergunta e decide quando usar ferramentas. Os cálculos e consultas são executados pelo Python/DuckDB; o modelo não é usado como calculadora.

## Estrutura

```text
secaae_analista_v2/
├── app.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
├── .env.example
├── config/
│   ├── __init__.py
│   └── settings.py
├── data/
│   ├── __init__.py
│   ├── drive.py
│   ├── ingestion.py
│   └── database.py
├── agent/
│   ├── __init__.py
│   ├── prompts.py
│   ├── tools.py
│   └── gemini.py
├── ui/
│   ├── __init__.py
│   └── components.py
├── scripts/
│   ├── __init__.py
│   └── sync_data.py
├── tests/
│   ├── test_sql_guard.py
│   └── test_names.py
├── .streamlit/
│   └── config.toml
└── colab/
    └── SECAAE_Analista_V2.ipynb
```

## 1. Desenvolvimento no Google Colab

Abra `colab/SECAAE_Analista_V2.ipynb` no Google Colab.

A sequência é:

1. instalar dependências;
2. montar o projeto;
3. autenticar no Google Drive;
4. configurar `DRIVE_FOLDER_ID`;
5. sincronizar os arquivos;
6. iniciar o Streamlit;
7. opcionalmente expor com ngrok.

Para a primeira execução, o modo de autenticação do Colab usa `google.colab.auth.authenticate_user()` e Application Default Credentials.

## 2. Configuração

Copie `.env.example` para `.env` em ambiente local.

Variáveis principais:

```text
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.6-flash
DRIVE_FOLDER_ID=...
DB_PATH=data/analytics.duckdb
```

### Google Drive

Recomenda-se informar diretamente o ID da pasta:

```text
DRIVE_FOLDER_ID=1AbCdEf...
```

O sistema não depende de procurar a pasta por nome em toda inicialização.

Se `DRIVE_FOLDER_ID` estiver vazio, pode ser usado:

```text
DRIVE_FOLDER_NAME=Dashboard
```

mas o ID é a opção recomendada.

### Cloud Run

No Cloud Run, a aplicação usa Application Default Credentials. A conta de serviço do serviço precisa ter acesso à pasta do Google Drive que contém os dados.

Se a pasta estiver em um Drive compartilhado, configure também:

```text
DRIVE_SHARED_DRIVE_ID=...
```

## 3. Sincronizar dados

Execute:

```bash
python scripts/sync_data.py
```

Isso:

- localiza a pasta;
- lista arquivos;
- baixa Google Sheets/Excel/CSV;
- lê todas as abas dos arquivos Excel;
- normaliza nomes de tabelas e colunas;
- grava as tabelas no DuckDB;
- atualiza o catálogo de fontes.

## 4. Executar Streamlit

```bash
streamlit run app.py
```

## 5. Cloud Run

O projeto já possui Dockerfile.

Com Google Cloud CLI:

```bash
gcloud config set project SEU_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
gcloud run deploy secaae-analista --source .
```

No Cloud Run, configure pelo menos:

- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `DRIVE_FOLDER_ID`

Também conceda à identidade do serviço acesso à pasta do Drive.

## 6. Como o agente funciona

Pergunta:

> Compare as liquidações de 2025 e 2026.

Fluxo:

```text
Usuário
  ↓
Gemini
  ↓
list_tables / describe_table
  ↓
run_query
  ↓
DuckDB
  ↓
resultado estruturado
  ↓
Gemini
  ↓
resposta + fontes
```

O agente possui ferramentas para:

- listar tabelas;
- descrever tabelas;
- executar consultas somente de leitura;
- comparar períodos;
- gerar resumo de uma tabela;
- verificar atualização dos dados.

## 7. Importante sobre o esquema dos dados

A V2 foi desenhada para não depender de nomes exatos de colunas ainda não confirmados.

Depois da primeira sincronização, consulte:

```text
Quais tabelas existem e quais são suas colunas?
```

Isso permite ajustar os aliases sem reescrever a arquitetura.

O arquivo `config/settings.py` contém aliases de colunas comuns em execução orçamentária. Eles são auxiliares, não uma dependência rígida.

## 8. Segurança

Nunca coloque a chave Gemini diretamente no código.

Use:

- `.env` local;
- `st.secrets` em Streamlit Cloud, se aplicável;
- Secret Manager/variáveis de ambiente no Google Cloud.

O `run_query` bloqueia DDL/DML e limita o número de linhas retornadas.

## 9. Próxima evolução recomendada

Depois de validar a V2:

1. criar indicadores específicos da SECAAE;
2. criar gráficos automáticos;
3. adicionar filtros por UG, PO, ND, mês e exercício;
4. criar camada de auditoria/evidências;
5. adicionar autenticação de usuários;
6. mover o DuckDB para uma camada persistente mais apropriada se o volume crescer;
7. agendar sincronização automática do Drive.
