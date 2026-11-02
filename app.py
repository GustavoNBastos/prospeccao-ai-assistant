"""
Aplicacao principal Streamlit.

Interface de chat com streaming, integrando DuckDB (dados estruturados),
ChromaDB (RAG) e modelo de ML via LLM (Anthropic Claude com tool use).
Perguntas compostas sao roteadas para os agentes CrewAI (Analista + Estrategista).
"""

import os
import re
import sys
import uuid

import streamlit as st

# garante que os modulos dentro de src/ sejam importaveis (db, rag, prompts, llm
# usam imports diretos entre si, sem prefixo de pacote)
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from agents import executar_crew  # noqa: E402
from llm import responder_stream  # noqa: E402
from observability import ativo, trace  # noqa: E402
from router import classificar  # noqa: E402

print(f"[app] carregado de {os.path.abspath(__file__)} | langfuse ativo: {ativo()}", flush=True)

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
        "- Quais leads da trilha T-EXEC tiveram objeção nas últimas interações?\n"
        "- Qual a chance de conversão de um contato de 55 anos, aposentado, saldo 3000, "
        "com campanha anterior de sucesso?\n"
        "- Quantos leads T-INFRA estão em negociação e como contornar a objeção "
        "'já temos um parceiro'? (usa os dois agentes)"
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
if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex[:12]

for mensagem in st.session_state.mensagens_display:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["texto"])
        if mensagem.get("origem") == "agentes":
            st.caption("🤖 Rota: agentes (Analista de Leads + Estrategista Comercial)")
        elif mensagem.get("origem") == "chat":
            st.caption("⚡ Rota: resposta direta (Claude + ferramentas)")

pergunta = st.chat_input("Pergunte sobre leads, cadências, objeções...")

if pergunta:
    st.session_state.mensagens_display.append({"role": "user", "texto": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    st.session_state.mensagens_api.append({"role": "user", "content": pergunta})

    with trace(
        "pergunta-chat", entrada=pergunta,
        session_id=st.session_state.session_id, tags=["prospeccao"],
    ) as raiz:
        origem = "chat"
        forcar = False
        with st.chat_message("assistant"):
            try:
                # "(agentes)" no texto força o caminho dos agentes (útil em demonstrações)
                forcar = "(agentes)" in pergunta.lower()
                pergunta_limpa = re.sub(r"\s*\(agentes\)\s*", " ", pergunta, flags=re.I).strip()
                rota = "composta" if forcar else classificar(pergunta_limpa)
                if rota == "composta":
                    origem = "agentes"
                    with st.spinner("Analista de Leads e Estrategista Comercial trabalhando..."):
                        resposta_completa = executar_crew(pergunta_limpa)
                    st.markdown(resposta_completa)
                    st.caption("🤖 Rota: agentes (Analista de Leads + Estrategista Comercial)")
                    st.session_state.mensagens_api.append(
                        {"role": "assistant", "content": resposta_completa}
                    )
                else:
                    resposta_completa = st.write_stream(
                        responder_stream(st.session_state.mensagens_api)
                    )
                    st.caption("⚡ Rota: resposta direta (Claude + ferramentas)")
            except Exception as erro:
                resposta_completa = (
                    "Desculpe, ocorreu um erro ao gerar a resposta. "
                    f"Detalhe técnico: {erro}"
                )
                st.error(resposta_completa)
        raiz.update(output=resposta_completa, metadata={"rota": origem, "forcado": forcar})

    st.session_state.mensagens_display.append(
        {"role": "assistant", "texto": resposta_completa, "origem": origem}
    )
