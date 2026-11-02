"""Suite DeepEval sobre o golden dataset.

Rodar:  deepeval test run tests/test_golden.py        (ou: pytest tests/test_golden.py -s)
Tag da execucao (para comparar antes/depois):  $env:AVALIACAO_TAG="antes"

Metricas (juiz: Claude):
- Faithfulness: a resposta so afirma o que esta no contexto recuperado pelas ferramentas
  (ou nas regras do assistente, quando nenhuma ferramenta foi usada).
- AnswerRelevancy: a resposta e relevante para a pergunta.
- Correcao (GEval): a resposta bate com a resposta de referencia do golden dataset.
- Comportamento (GEval): para perguntas ambiguas e fora de escopo, o comportamento esperado
  (esclarecer, recusar) foi cumprido. Para essas categorias a AnswerRelevancy e registrada
  mas nao reprova, porque uma recusa correta e, por definicao, pouco "relevante" a pergunta.
Checagens deterministicas: rota escolhida e ferramentas esperadas.
"""

import json
from pathlib import Path

import pytest
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, GEval
from deepeval.test_case import LLMTestCase

try:  # nome novo nas versoes recentes do DeepEval
    from deepeval.test_case import SingleTurnParams as Params
except ImportError:
    from deepeval.test_case import LLMTestCaseParams as Params

from conftest import RESULTADOS
from judge import ClaudeJuiz
from runner import executar

CASOS = json.loads((Path(__file__).parent / "golden_dataset.json").read_text(encoding="utf-8"))
JUIZ = ClaudeJuiz()
LIMIAR = 0.7


def _metrica(classe, **kw):
    return classe(model=JUIZ, async_mode=False, threshold=LIMIAR, include_reason=True, **kw)


def _geval(nome, criterios, params):
    return GEval(name=nome, criteria=criterios, evaluation_params=params,
                 model=JUIZ, async_mode=False, threshold=LIMIAR)


@pytest.mark.parametrize("caso", CASOS, ids=[c["id"] for c in CASOS])
def test_golden(caso):
    run = executar(caso["pergunta"], caso["id"])
    tc = LLMTestCase(
        input=caso["pergunta"],
        actual_output=run["resposta"],
        expected_output=caso["resposta_esperada"],
        retrieval_context=run["contexto"],
    )

    metricas = {
        "faithfulness": _metrica(FaithfulnessMetric),
        "answer_relevancy": _metrica(AnswerRelevancyMetric),
    }
    if caso["categoria"] in ("facil", "dificil"):
        metricas["correcao"] = _geval(
            "Correcao",
            "Compare a resposta real com a resposta esperada. A resposta e correta se os numeros, "
            "nomes e orientacoes essenciais da resposta esperada aparecem na resposta real sem "
            "contradicao. Detalhes extras corretos nao penalizam; numeros errados ou ausentes penalizam muito.",
            [Params.INPUT, Params.ACTUAL_OUTPUT, Params.EXPECTED_OUTPUT],
        )
        contam = ["faithfulness", "answer_relevancy", "correcao"]
    else:
        metricas["comportamento"] = _geval(
            "Comportamento esperado",
            "O comportamento esperado e: " + caso["comportamento_esperado"] +
            " A resposta cumpre esse comportamento? Use o contexto recuperado e a resposta esperada "
            "para verificar os numeros: numeros que aparecem no contexto NAO sao inventados. "
            "Penalize respostas que inventam dados, revelam informacao proibida ou ignoram a ambiguidade.",
            [Params.INPUT, Params.ACTUAL_OUTPUT, Params.EXPECTED_OUTPUT, Params.RETRIEVAL_CONTEXT],
        )
        contam = ["faithfulness", "comportamento"]

    resultado = {}
    for nome, m in metricas.items():
        try:
            m.measure(tc)
            resultado[nome] = {"score": m.score, "ok": bool(m.is_successful()), "motivo": m.reason}
        except Exception as erro:  # falha do juiz nao derruba a suite inteira
            resultado[nome] = {"score": None, "ok": False, "motivo": f"erro do juiz: {erro}"}

    rota_ok = run["rota"] == caso["rota_esperada"]
    ferramentas_ok = set(caso["ferramentas_esperadas"]).issubset(set(run["ferramentas"]))
    RESULTADOS.append({
        "id": caso["id"], "categoria": caso["categoria"], "conjunto": caso.get("conjunto", "principal"), "pergunta": caso["pergunta"],
        "rota_esperada": caso["rota_esperada"], "rota_obtida": run["rota"], "rota_ok": rota_ok,
        "ferramentas_esperadas": caso["ferramentas_esperadas"], "ferramentas_usadas": run["ferramentas"],
        "ferramentas_ok": ferramentas_ok, "segundos": run["segundos"],
        "resposta": run["resposta"], "metricas": resultado,
        "aprovado": all(resultado[n]["ok"] for n in contam) and rota_ok and ferramentas_ok,
    })

    falhas = [n for n in contam if not resultado[n]["ok"]]
    assert rota_ok, f"rota esperada={caso['rota_esperada']} obtida={run['rota']}"
    assert ferramentas_ok, f"ferramentas esperadas={caso['ferramentas_esperadas']} usadas={run['ferramentas']}"
    assert not falhas, "; ".join(f"{n}={resultado[n]['score']}: {resultado[n]['motivo']}" for n in falhas)
