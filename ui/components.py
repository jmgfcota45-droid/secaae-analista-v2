
from __future__ import annotations

import pandas as pd
import streamlit as st


def format_number(value):
    if isinstance(value, (int, float)):
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return value


def render_dataframe(df: pd.DataFrame):
    if df is None or df.empty:
        st.info("A consulta não retornou dados.")
        return

    st.dataframe(df, use_container_width=True, hide_index=True)


def render_sidebar(status: dict | None = None):
    with st.sidebar:
        st.markdown("## SECAAE Analista V2")
        st.caption("Assistente analítico institucional")

        if status:
            st.metric("Tabelas carregadas", status.get("tables", 0))
            if status.get("ultima_ingestao"):
                st.caption(f"Última ingestão: {status['ultima_ingestao']}")

        st.divider()
        st.markdown("### Exemplos")
        st.markdown(
            "- Compare a execução de 2025 e 2026\n"
            "- Quais UGs tiveram maior liquidação?\n"
            "- Mostre a evolução mensal dos pagamentos\n"
            "- Quais tabelas estão disponíveis?"
        )

        st.divider()
        st.caption(
            "Os cálculos são executados no banco de dados. "
            "O Gemini interpreta a pergunta e explica os resultados."
        )
