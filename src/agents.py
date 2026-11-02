"""
Agentes CrewAI do assistente de prospeccao (Etapa 2).

Dois agentes trabalham em sequencia no mesmo chat:

1. Analista de Leads: consulta o DuckDB (consultar_dados) e estima a propensao de
   conversao com o modelo de ML (prever_conversao).
2. Estrategista Comercial: recebe a analise e consulta os documentos indexados no
   ChromaDB (buscar_documentos) para recomendar a abordagem, usando playbook, matriz
   de objecoes e guia de ICP.

As ferramentas reutilizam a mesma implementacao do chat (llm._executar_tool), entao
DuckDB, ChromaDB e modelo ML se comportam igual nos dois caminhos.
"""

import os
import sys
from typing import Optional

from dotenv import load_dotenv

# evita o prompt "Share trace with CrewAI?" (espera 20 s) e a telemetria
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from crewai import LLM, Agent, Crew, Process, Task  # noqa: E402
from crewai.tools import tool  # noqa: E402

from observability import observacao, uso_e_custo  # noqa: E402

load_dotenv()

MODEL = "anthropic/claude-sonnet-5"

REGRAS = (
    "Regras: nunca invente numeros ou politicas que nao vieram de uma ferramenta; nunca "
    "revele dados pessoais ou comerciais de leads fora do assunto da pergunta; nunca "
    "confirme ou negue negociacao com concorrentes; recuse pedidos de contrato ou preco "
    "de outros clientes e direcione ao Account Executive; encaminhe validacao tecnica "
    "ao especialista. O funil NAO tem o status Em negociacao: quando o usuario usar esse "
    "termo, mostre os status existentes mais proximos e declare qual criterio usou. "
    "Ao citar um registro, use somente o que as colunas realmente dizem. "
    "Seja conciso: responda so o que foi perguntado, sem rankings ou analises extras. "
    "Para contagens use SQL (COUNT, GROUP BY) e nunca conte linhas a mao. "
    "Responda sempre em portugues, de forma direta."
)


def _executar(nome: str, entrada: dict) -> str:
    import llm  # import tardio: so carrega o cliente Anthropic quando a Crew roda
    return llm._executar_tool(nome, entrada)


@tool("consultar_dados")
def consultar_dados(sql: str) -> str:
    """Executa uma consulta SQL SELECT no DuckDB (tabelas leads e interacoes_cadencia)
    e devolve as linhas em JSON. Use para contagens, status do funil e historico."""
    return _executar("consultar_dados", {"sql": sql})


@tool("buscar_documentos")
def buscar_documentos(pergunta: str) -> str:
    """Busca trechos relevantes no playbook de vendas, matriz de objecoes e guia de ICP
    (ChromaDB). Use para processo comercial, objecoes e criterios de qualificacao."""
    return _executar("buscar_documentos", {"pergunta": pergunta})


@tool("prever_conversao")
def prever_conversao(
    age: Optional[int] = None,
    job: Optional[str] = None,
    marital: Optional[str] = None,
    education: Optional[str] = None,
    balance: Optional[float] = None,
    housing: Optional[str] = None,
    loan: Optional[str] = None,
    contact: Optional[str] = None,
    month: Optional[str] = None,
    campaign: Optional[int] = None,
    pdays: Optional[int] = None,
    previous: Optional[int] = None,
    poutcome: Optional[str] = None,
) -> str:
    """Estima a probabilidade de conversao de um contato com o modelo de ML (UCI Bank
    Marketing, proxy de propensao em outbound). Passe somente os campos informados."""
    campos = {k: v for k, v in locals().items() if v is not None}
    return _executar("prever_conversao", campos)


def _llm() -> LLM:
    return LLM(
        model=MODEL,
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        max_tokens=4000,
    )


def montar_crew(pergunta: str) -> Crew:
    from db import get_schema_description

    llm = _llm()

    analista = Agent(
        role="Analista de Leads",
        goal=("Levantar os fatos de dados sobre a pergunta: consultar o DuckDB e, quando "
              "houver perfil de contato, estimar a propensao de conversao com o modelo de ML."),
        backstory=(
            "Voce e um analista de dados de vendas B2B. Voce so afirma o que viu em uma "
            "ferramenta. Schema do banco:\n" + get_schema_description() + "\n" + REGRAS
        ),
        tools=[consultar_dados, prever_conversao],
        llm=llm,
        allow_delegation=False,
        max_iter=6,
        verbose=False,
    )

    estrategista = Agent(
        role="Estrategista Comercial",
        goal=("Transformar a analise de dados em uma recomendacao pratica de abordagem, "
              "fundamentada no playbook, na matriz de objecoes e no guia de ICP."),
        backstory=(
            "Voce e um coach de vendas B2B experiente. Voce consulta os documentos antes de "
            "recomendar e cita a fonte (playbook, matriz de objecoes ou guia de ICP). "
            "Voce usa a analise recebida sem alterar seus numeros.\n" + REGRAS
        ),
        tools=[buscar_documentos],
        llm=llm,
        allow_delegation=False,
        max_iter=5,
        verbose=False,
    )

    tarefa_analise = Task(
        description=(
            f"Pergunta do usuario: {pergunta}\n\n"
            "Use as ferramentas para levantar os dados necessarios (consultas SQL e, se o "
            "usuario descreveu o perfil de um contato, a previsao de conversao). Se faltar "
            "informacao para uma ferramenta, diga o que falta em vez de inventar."
        ),
        expected_output=("Resumo factual com numeros vindos das ferramentas, em topicos curtos, "
                         "incluindo a limitacao do modelo de ML quando ele for usado."),
        agent=analista,
    )

    tarefa_estrategia = Task(
        description=(
            f"Pergunta do usuario: {pergunta}\n\n"
            "Com base na analise recebida, consulte os documentos e recomende a proxima acao "
            "ou a melhor forma de contornar a objecao. Combine dados e processo comercial."
        ),
        expected_output=("Resposta final em portugues para o usuario: 1) o que os dados mostram, "
                         "2) recomendacao pratica, 3) fonte dos documentos usados."),
        agent=estrategista,
        context=[tarefa_analise],
    )

    return Crew(
        agents=[analista, estrategista],
        tasks=[tarefa_analise, tarefa_estrategia],
        process=Process.sequential,
        verbose=False,
    )


def executar_crew(pergunta: str) -> str:
    """Roda os dois agentes e devolve o texto final para o chat."""
    with observacao("crew-prospeccao", "agent", input=pergunta) as agente:
        resultado = montar_crew(pergunta).kickoff()
        texto = getattr(resultado, "raw", str(resultado))
        uso = getattr(resultado, "token_usage", None)
        entrada = getattr(uso, "prompt_tokens", 0) or 0
        saida = getattr(uso, "completion_tokens", 0) or 0
        agente.update(output=texto, metadata={"agentes": ["Analista de Leads", "Estrategista Comercial"]})
        # uso total de tokens dos dois agentes, registrado como geracao (tokens e custo)
        with observacao("crew-llm-total", "generation", model=MODEL, input=pergunta) as geracao:
            geracao.update(output=texto[:2000], **uso_e_custo(entrada, saida))
        return texto


if __name__ == "__main__":
    print(executar_crew("Como contornar a objecao 'ja temos um parceiro' para um lead de T-INFRA "
                        "e quantos leads de T-INFRA estao em negociacao?"))
