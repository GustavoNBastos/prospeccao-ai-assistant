"""
Cliente de chamada a LLM (Anthropic Claude), com:
- Loop de tool use: o modelo decide sozinho quando consultar o DuckDB
  (consultar_dados) e/ou buscar nos documentos indexados (buscar_documentos).
- Streaming de tokens na resposta final, para exibir no chat em tempo real.
"""

import json
import os

import anthropic
from dotenv import load_dotenv

import db
import rag
from prompts import SYSTEM_PROMPT, TOOLS

load_dotenv()

MODEL = "claude-sonnet-5"
MAX_TOKENS = 1024

_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def _executar_tool(nome: str, entrada: dict) -> str:
    """Executa a ferramenta pedida pelo modelo e retorna o resultado como texto."""
    if nome == "consultar_dados":
        try:
            con = db.get_connection()
            resultado = db.run_query(con, entrada["sql"])
            return json.dumps(resultado, default=str, ensure_ascii=False)
        except Exception as erro:
            return f"Erro ao executar a consulta: {erro}"

    if nome == "buscar_documentos":
        chunks = rag.retrieve(entrada["pergunta"], top_k=3)
        if not chunks:
            return "Nenhum trecho relevante encontrado nos documentos."
        return "\n\n---\n\n".join(
            f"[Fonte: {c['fonte']} | {c['titulo_secao']}]\n{c['texto']}" for c in chunks
        )

    return f"Ferramenta desconhecida: {nome}"


def responder_stream(mensagens: list[dict]):
    """
    Gera a resposta do assistente para a conversa em `mensagens`, resolvendo
    automaticamente qualquer chamada de ferramenta no caminho, e faz streaming
    (yield) do texto final token a token para exibicao incremental no Streamlit.

    `mensagens` deve ser uma lista no formato da API da Anthropic (role
    "user"/"assistant") ja terminando com a pergunta mais recente do usuario.
    A lista e MUTADA in place: os turnos intermediarios de tool use e a
    resposta final do assistente sao acrescentados a ela, para que o
    historico persista entre chamadas (ex.: via st.session_state).
    """
    while True:
        with _client.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=mensagens,
        ) as stream:
            for texto in stream.text_stream:
                yield texto
            resposta_final = stream.get_final_message()

        mensagens.append({"role": "assistant", "content": resposta_final.content})

        if resposta_final.stop_reason != "tool_use":
            break

        resultados_tools = []
        for bloco in resposta_final.content:
            if bloco.type == "tool_use":
                resultado = _executar_tool(bloco.name, bloco.input)
                resultados_tools.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": bloco.id,
                        "content": resultado,
                    }
                )
        mensagens.append({"role": "user", "content": resultados_tools})


if __name__ == "__main__":
    pergunta_teste = "Quantos leads existem por trilha?"
    print(f"Pergunta: {pergunta_teste}\n")
    mensagens_teste = [{"role": "user", "content": pergunta_teste}]
    for pedaco in responder_stream(mensagens_teste):
        print(pedaco, end="", flush=True)
    print()
