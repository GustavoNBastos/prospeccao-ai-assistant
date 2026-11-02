"""
Observabilidade com Langfuse (Etapa 2).

Cada pergunta vira um trace com:
- uma observacao raiz ("pergunta-chat");
- geracoes do LLM com modelo, tokens de entrada/saida, custo em USD e latencia
  (a latencia vem do inicio/fim da propria observacao);
- spans de ferramenta (consultar_dados, buscar_documentos, prever_conversao);
- no caminho dos agentes, o span "crew-prospeccao" com o uso total de tokens.

Se as chaves do Langfuse nao estiverem no .env, tudo aqui vira no-op e o app
funciona normalmente, apenas sem registrar nada.
"""

import contextlib
import os

from dotenv import load_dotenv

load_dotenv()

# Preco do claude-sonnet-5 em USD por 1 milhao de tokens (fonte: documentacao oficial
# da Anthropic). Sobrescreva com PRECO_ENTRADA_MTOK / PRECO_SAIDA_MTOK no .env se mudar.
PRECO_ENTRADA = float(os.environ.get("PRECO_ENTRADA_MTOK", "2.0"))
PRECO_SAIDA = float(os.environ.get("PRECO_SAIDA_MTOK", "10.0"))

_cache = {}


class _Nulo:
    """Substituto quando o Langfuse esta desligado."""

    def update(self, **_):
        return None


def ativo() -> bool:
    return bool(os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"))


def _cliente():
    if not ativo():
        return None
    if "lf" not in _cache:
        try:
            from langfuse import get_client
            _cache["lf"] = get_client()
        except Exception as erro:
            print(f"[observability] Langfuse indisponivel: {erro!r}")
            _cache["lf"] = None
    return _cache["lf"]


def custo_usd(tokens_entrada: int, tokens_saida: int) -> dict:
    entrada = tokens_entrada * PRECO_ENTRADA / 1_000_000
    saida = tokens_saida * PRECO_SAIDA / 1_000_000
    return {"input": entrada, "output": saida, "total": entrada + saida}


def uso_e_custo(tokens_entrada: int, tokens_saida: int) -> dict:
    """Campos prontos para gen.update(**uso_e_custo(...))."""
    return {
        "usage_details": {"input": int(tokens_entrada), "output": int(tokens_saida)},
        "cost_details": custo_usd(int(tokens_entrada), int(tokens_saida)),
    }


@contextlib.contextmanager
def observacao(nome: str, tipo: str = "span", **campos):
    """Observacao (span, generation, tool, agent...) aninhada no trace atual."""
    lf = _cliente()
    if lf is None:
        yield _Nulo()
        return
    try:
        cm = lf.start_as_current_observation(name=nome, as_type=tipo, **campos)
        obs = cm.__enter__()
    except Exception as erro:
        print(f"[observability] falha ao abrir '{nome}': {erro!r}")
        yield _Nulo()
        return
    try:
        yield obs
    except BaseException as erro:
        try:
            obs.update(level="ERROR", status_message=str(erro))
        except Exception:
            pass
        cm.__exit__(type(erro), erro, erro.__traceback__)
        raise
    else:
        cm.__exit__(None, None, None)


@contextlib.contextmanager
def trace(nome: str, entrada=None, session_id: str | None = None, tags: list[str] | None = None):
    """Abre o trace raiz de uma pergunta e envia os dados ao final (flush)."""
    lf = _cliente()
    if lf is None:
        yield _Nulo()
        return
    from langfuse import propagate_attributes
    try:
        with propagate_attributes(session_id=session_id, tags=tags or [], trace_name=nome):
            with observacao(nome, "span", input=entrada) as raiz:
                yield raiz
    finally:
        try:
            lf.flush()
        except Exception:
            pass
