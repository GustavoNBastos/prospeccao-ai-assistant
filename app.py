"""
Aplicacao principal Streamlit.

Interface de chat com streaming, integrando DuckDB (dados estruturados)
e ChromaDB (RAG) via LLM (Anthropic Claude com tool use).
"""

import os
import sys

import streamlit as st

# garante que os modulos dentro de src/ sejam importaveis (db, rag, prompts, llm
# usam imports diretos entre si, sem prefixo de pacote)
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from llm import responder_stream  # noqa: E402

st.set_page_config(
    page_title="Assistente de Prospecção B2B",
    page_icon="💬",
    layout="centered",
)

st.title("💬 Assistente de Prospecção B2B")
st.caption(
    "Consulte leads, cadências, playbook de vendas e critérios de qualificação (ICP) "
    "em linguagem natural."
)

with st.sidebar:
    st.subheader("Exemplos de pergunta")
    st.markdown(
        "- Quantos leads existem por trilha?\n"
        "- Quais leads estão com status 'Reunião Agendada'?\n"
        "- Como funciona a alocação de especialista sem abrir headcount?\n"
        "- Como devo responder se o lead disser que já tem um parceiro atendendo?\n"
        "- Quais leads da trilha T-EXEC tiveram objeção nas últimas interações?"
    )
    st.divider()
    if st.button("🗑️ Limpar conversa"):
        st.session_state.mensagens_display = []
        st.session_state.mensagens_api = []
        st.rerun()

# mensagens_display: o que aparece na tela (formato simples, so texto)
# mensagens_api: historico no formato exigido pela API da Anthropic,
# atualizado automaticamente por responder_stream a cada pergunta
if "mensagens_display" not in st.session_state:
    st.session_state.mensagens_display = []
if "mensagens_api" not in st.session_state:
    st.session_state.mensagens_api = []

for mensagem in st.session_state.mensagens_display:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["texto"])

pergunta = st.chat_input("Pergunte sobre leads, cadências, objeções...")

if pergunta:
    st.session_state.mensagens_display.append({"role": "user", "texto": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    st.session_state.mensagens_api.append({"role": "user", "content": pergunta})

    with st.chat_message("assistant"):
        try:
            resposta_completa = st.write_stream(
                responder_stream(st.session_state.mensagens_api)
            )
        except Exception as erro:
            resposta_completa = (
                "Desculpe, ocorreu um erro ao gerar a resposta. "
                f"Detalhe técnico: {erro}"
            )
            st.error(resposta_completa)

    st.session_state.mensagens_display.append(
        {"role": "assistant", "texto": resposta_completa}
    )
