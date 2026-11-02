"""Executa uma pergunta pelo mesmo caminho do app (roteador, chat direto ou agentes)
e captura as saidas das ferramentas, que viram o `retrieval_context` do DeepEval."""

import os
import sys
import time

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(RAIZ, "src"))
sys.path.insert(0, RAIZ)

import agents  # noqa: E402
import llm  # noqa: E402
import prompts  # noqa: E402
import router  # noqa: E402
from observability import trace  # noqa: E402

LIMITE_CONTEXTO = 8000  # caracteres por saida de ferramenta


def executar(pergunta: str, caso_id: str = "") -> dict:
    contexto: list[str] = []
    ferramentas: list[str] = []
    original = llm._executar_tool_impl

    def gravar(nome, entrada):
        resultado = original(nome, entrada)
        ferramentas.append(nome)
        contexto.append(f"[ferramenta {nome} | entrada {entrada}]\n{str(resultado)[:LIMITE_CONTEXTO]}")
        return resultado

    llm._executar_tool_impl = gravar
    inicio = time.time()
    try:
        with trace("avaliacao-golden", entrada=pergunta, tags=["avaliacao", caso_id]) as raiz:
            rota = router.classificar(pergunta)
            if rota == "composta":
                resposta = agents.executar_crew(pergunta)
            else:
                mensagens = [{"role": "user", "content": pergunta}]
                resposta = "".join(llm.responder_stream(mensagens))
            raiz.update(output=resposta, metadata={"rota": rota, "caso": caso_id})
    finally:
        llm._executar_tool_impl = original

    if not contexto:
        # sem ferramentas, a resposta so pode se apoiar nas regras do assistente
        contexto = [prompts.SYSTEM_PROMPT]
    return {
        "resposta": resposta,
        "contexto": contexto,
        "rota": rota,
        "ferramentas": ferramentas,
        "segundos": round(time.time() - inicio, 1),
    }
