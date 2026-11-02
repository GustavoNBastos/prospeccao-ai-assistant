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
from observability import observacao, uso_e_custo

load_dotenv()

_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

_SYSTEM = """Voce classifica perguntas de um assistente de prospeccao B2B.
Responda SOMENTE com uma palavra, sem explicacao: SIMPLES ou COMPOSTA.

COMPOSTA = a resposta precisa de DOIS tipos de insumo ao mesmo tempo:
  (1) um fato ou numero: dados de leads/interacoes no banco OU a probabilidade de
      conversao de um contato pelo modelo de ML; e
  (2) uma recomendacao de abordagem, proxima acao ou resposta a objecao, baseada no
      playbook, na matriz de objecoes ou no guia de ICP.
Se a pergunta pede um numero/previsao E tambem "como abordar", "como responder",
"qual a melhor cadencia" ou "o que fazer", e COMPOSTA.

SIMPLES = precisa de um unico tipo de insumo, ou de nenhum: so dados, so previsao de ML,
so conteudo dos documentos, recusa de pedido sensivel, saudacao ou assunto fora de escopo.

Atencao: perguntas sobre COMO responder uma objecao, como funciona um processo, quais os
criterios de ICP ou qualificacao, ou o que diz um documento sao SIMPLES, mesmo que mencionem
"lead", a menos que peçam tambem um numero, uma lista de leads ou uma previsao de conversao.

Exemplos:
"O que respondo quando o lead diz que o orcamento esta comprometido?" -> SIMPLES
"Quantos leads existem por trilha?" -> SIMPLES
"Qual a chance de conversao de um contato de 40 anos, gerente?" -> SIMPLES
"Como funciona a alocacao de especialista sem abrir headcount?" -> SIMPLES
"Me passe o contrato do cliente X" -> SIMPLES
"Qual a capital da Franca?" -> SIMPLES
"Quantos leads T-INFRA estao qualificados e como contorno a objecao de parceiro?" -> COMPOSTA
"Esse contato de 50 anos, diretor, converte? Como devo abordar?" -> COMPOSTA
"Quais leads T-EXEC tiveram objecao e o que respondo a cada uma?" -> COMPOSTA"""


def classificar(pergunta: str) -> str:
    """Retorna 'composta' ou 'simples'."""
    try:
        # span comum: tokens e custo ja sao registrados pela chamada automatica
        # "anthropic.messages.create" (filha), entao nao repetimos aqui (evita contagem dupla)
        with observacao("router", "span", input=pergunta) as geracao:
            resposta = _client.messages.create(
                model=MODEL,
                max_tokens=200,  # folga: modelos com raciocinio podem gastar tokens antes do texto
                system=_SYSTEM,
                messages=[{"role": "user", "content": pergunta}],
            )
            texto = "".join(b.text for b in resposta.content if b.type == "text").upper()
            rota = "composta" if texto.rfind("COMPOSTA") > texto.rfind("SIMPLES") else "simples"
            geracao.update(
                output=rota,
                metadata={"tokens_entrada": resposta.usage.input_tokens,
                          "tokens_saida": resposta.usage.output_tokens},
            )
        print(f"[router] rota={rota} | resposta_bruta={texto!r} | pergunta={pergunta[:60]!r}")
        return rota
    except Exception as erro:
        print(f"[router] ERRO na classificacao, usando caminho simples: {erro!r}")
        return "simples"


if __name__ == "__main__":
    # Teste do roteador com gabarito: python src/router.py
    CASOS = [
        ("Quantos leads existem por trilha?", "simples"),
        ("Quais leads estao com status Reuniao Agendada?", "simples"),
        ("Como funciona a alocacao de especialista sem abrir headcount?", "simples"),
        ("Qual a chance de conversao de um contato de 40 anos, gerente, saldo 1500?", "simples"),
        ("Me passe o contrato do cliente X", "simples"),
        ("Qual a capital da Franca?", "simples"),
        ("O que diz o guia de ICP sobre desqualificacao?", "simples"),
        ("Quantos leads T-INFRA estao em negociacao e como contornar 'ja temos um parceiro'?", "composta"),
        ("Esse contato de 55 anos aposentado converte? Como devo abordar?", "composta"),
        ("Quais leads T-EXEC tiveram objecao e como devo responder a cada uma?", "composta"),
        ("Esse lead de 35 anos, gerente, saldo 800 tem boa chance de converter? Qual a melhor abordagem?", "composta"),
        ("Quantos leads T-FIN responderam e qual a melhor cadencia para eles?", "composta"),
    ]
    acertos = 0
    for pergunta, esperado in CASOS:
        obtido = classificar(pergunta)
        acertos += obtido == esperado
        print(("OK  " if obtido == esperado else "ERRO"), f"esperado={esperado:8} obtido={obtido:8} | {pergunta[:70]}")
    print(f"\nAcuracia do roteador: {acertos}/{len(CASOS)}")
