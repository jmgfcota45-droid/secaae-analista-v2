
from data.database import normalize_identifier, table_name_from_source


def test_normalize_identifier():
    assert normalize_identifier("Valor Liquidado") == "valor_liquidado"


def test_table_name():
    name = table_name_from_source("Execução Orçamentária.xlsx", "Janeiro")
    assert name.startswith("execucao_orcamentaria_janeiro")
