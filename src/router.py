"""
Roteador de perguntas (Etapa 2).

Decide se a pergunta e SIMPLES (uma fonte, resposta direta com streaming) ou
COMPOSTA (precisa combinar dados + modelo de ML + documentos, caso dos agentes CrewAI).
Em caso de qualquer falha na classificacao, usa o caminho simples (mais barato e rapido).
"""

import os

import anthropic
from dotenv import load_dotenv

from llm import MODEL

load_dotenv()

_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

_SYSTEM = """Voce classifica perguntas de um assistente de prospeccao B2B.
Responda apenas com uma palavra: SIMPLES ou COMPOSTA.

COMPOSTA: a pergunta exige combinar pelo menos dois destes tres elementos: (a) dados
de leads/interacoes (contagens, status, historico), (b) estimativa de probabilidade de
conversao de um perfil de contato, (c) recomendacao de abordagem baseada no playbook,
objecoes ou ICP. Exemplo: "quantos leads T-INFRA estao em negociacao e como contornar a
objecao deles?" ou "esse contato converte? como abordo?".

SIMPLES: usa uma unica fonte ou nenhuma. Exemplos: "quantos leads por trilha?",
"como funciona a alocacao de especialista?", "qual a probabilidade de conversao de um
contato de 55 anos aposentado?", saudacoes, perguntas fora de escopo."""


def classificar(pergunta: str) -> str:
    """Retorna 'composta' ou 'simples'."""
    try:
        resposta = _client.messages.create(
            model=MODEL,
            max_tokens=200,  # folga: modelos com raciocinio podem gastar tokens antes do texto
            system=_SYSTEM,
            messages=[{"role": "user", "content": pergunta}],
        )
        texto = "".join(b.text for b in resposta.content if b.type == "text").upper()
        rota = "composta" if texto.rfind("COMPOSTA") > texto.rfind("SIMPLES") else "simples"
        print(f"[router] rota={rota} | resposta_bruta={texto!r} | pergunta={pergunta[:60]!r}")
        return rota
    except Exception as erro:
        print(f"[router] ERRO na classificacao, usando caminho simples: {erro!r}")
        return "simples"


if __name__ == "__main__":
    for p in [
        "Quantos leads existem por trilha?",
        "Quantos leads T-INFRA estao em negociacao e como contornar a objecao 'ja temos um parceiro'?",
        "Qual a chance de conversao de um contato de 55 anos aposentado?",
        "Esse contato de 40 anos, gerente, converte? Como devo abordar?",
    ]:
        classificar(p)
