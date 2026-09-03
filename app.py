
from __future__ import annotations

import streamlit as st

from agent.gemini import GeminiAgent
from agent.prompts import WELCOME_MESSAGE
from config.settings import SETTINGS
from data.database import Database
from ui.components import render_sidebar


st.set_page_config(
    page_title="SECAAE Analista V2",
    page_icon="📊",
    layout="wide",
)


@st.cache_resource
def get_database():
    return Database(SETTINGS.db_path)


@st.cache_resource
def get_agent():
    db = get_database()
    return GeminiAgent(
        db=db,
        api_key=SETTINGS.gemini_api_key,
        model=SETTINGS.gemini_model,
        max_rounds=SETTINGS.max_tool_rounds,
    )


db = get_database()

status = {
    "tables": len(db.list_tables()),
    "ultima_ingestao": None,
}
if db.list_tables():
    status["ultima_ingestao"] = db.list_tables()[0].get("ingested_at")

render_sidebar(status)

st.title("📊 SECAAE Analista")
st.caption(
    "Pergunte em linguagem natural sobre os dados institucionais "
    "carregados do Google Drive."
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "interaction_id" not in st.session_state:
    st.session_state.interaction_id = None

if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown(WELCOME_MESSAGE)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ex.: compare as liquidações de 2025 e 2026")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            agent = get_agent()
            with st.spinner("Consultando os dados..."):
                response = agent.ask(
                    prompt,
                    previous_interaction_id=st.session_state.interaction_id,
                )

            st.markdown(response.text)
            st.session_state.interaction_id = response.interaction_id
            st.session_state.messages.append(
                {"role": "assistant", "content": response.text}
            )

            if response.tool_calls:
                with st.expander("🔎 Evidência técnica"):
                    for call in response.tool_calls:
                        st.write(
                            {
                                "ferramenta": call["name"],
                                "argumentos": call["arguments"],
                                "erro": call["error"],
                            }
                        )

        except Exception as exc:
            error_message = (
                f"Não foi possível processar a consulta: "
                f"`{type(exc).__name__}: {exc}`"
            )
            st.error(error_message)
