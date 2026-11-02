"""Diagnostico do Langfuse: abre um trace com a mesma estrutura do app e imprime a URL."""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from observability import ativo, observacao, trace, uso_e_custo, _cliente  # noqa: E402

print("Langfuse ativo:", ativo())
print("OTEL_SDK_DISABLED =", os.environ.get("OTEL_SDK_DISABLED"))

with trace("teste-diagnostico", entrada="pergunta de teste", session_id="diag", tags=["diagnostico"]) as raiz:
    with observacao("router", "generation", model="claude-sonnet-5", input="pergunta de teste") as g:
        time.sleep(0.2)
        g.update(output="COMPOSTA", **uso_e_custo(300, 5))
    with observacao("crew-prospeccao", "agent", input="pergunta de teste") as a:
        with observacao("tool:consultar_dados", "tool", input="SELECT 1") as t:
            time.sleep(0.2)
            t.update(output="1")
        with observacao("tool:buscar_documentos", "tool", input="objecao") as t:
            time.sleep(0.2)
            t.update(output="doc")
        with observacao("crew-llm-total", "generation", model="claude-sonnet-5", input="x") as g:
            g.update(output="ok", **uso_e_custo(5000, 800))
        a.update(output="ok")
    raiz.update(output="ok", metadata={"rota": "agentes"})

lf = _cliente()
if lf:
    try:
        print("URL do trace:", lf.get_trace_url())
    except Exception as e:
        print("sem URL:", e)
print("Pronto. Procure o trace 'teste-diagnostico' no Langfuse (pode levar ~30 s).")
