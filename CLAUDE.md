# Programador do Assistente Orçamentário da SECAAE

Antes de trabalhar, leia integralmente:

- `../documentos/CLAUDE.md`
- `../documentos/HANDOFF_CLAUDE_CODE.md`
- `../documentos/MIGRATION_CHECKLIST.md`
- `README.md`
- qualquer status ou evidência existente no próprio repositório.

Este repositório foi restaurado do checkpoint `CURRENT` do Google Drive, datado de 9 de agosto de 2026. Ele é um baseline anterior, não uma prova de conter as etapas 44.1I e 44.2A descritas no handoff. Não recrie artefatos ausentes por suposição.

## Regras permanentes

- Começar em diagnóstico somente leitura e comparar este baseline com o handoff.
- O próximo marco é a ETAPA 44.2A.1; a ETAPA 44.2B permanece bloqueada.
- Manter o Scheduler desligado.
- Nunca promover `raw_*` diretamente. Usar `raw → candidate → validação → promoted → views`.
- Não alterar fontes canônicas sem evidência física e semântica.
- Manter RPNP como `NAO_CONSOLIDAR`; fonte independente é `CROSS_CHECK_ONLY`.
- Manter GND bloqueado enquanto a decisão formal estiver pendente.
- Preservar `data/analytics.duckdb`; o checkpoint restaurado tem SHA-256 `ca2cc66356868a18065cf293976f7a963cf7ae2032d27a4c2ce059ebd5da6696`.
- Não alterar BigQuery, IAM, dados ou Scheduler durante o diagnóstico inicial.
- Não inventar arquivos, valores, filtros, fontes, chaves ou granularidades.
- Resolver NEs 433×432 e RPNP 49×99 por causa raiz, após localizar as evidências e o código mais recente.

## Estado restaurado

O checkpoint contém `data/database.py`, confirmando que `data.database` era módulo interno. Porém ele possui apenas uma suíte pequena e não contém, no momento da restauração, os scripts e evidências conhecidos das etapas 44.1I/44.2A. Trate essa diferença como lacuna de versão a investigar, não como autorização para reimplementar imediatamente.
