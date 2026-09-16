"""
Gera os arquivos leads.csv e interacoes_cadencia.csv com dados sinteticos,
seguindo a logica real de segmentacao usada em prospeccao B2B de dados/IA:
trilhas por persona, setor, modo de execucao (account-based x lead a lead)
e oferta associada a cada trilha.

Uso:
    python scripts/gerar_dados_sinteticos.py
"""

import csv
import random
from datetime import date, timedelta

from faker import Faker

fake = Faker("pt_BR")
random.seed(42)
Faker.seed(42)

N_LEADS = 220

# Trilhas por persona, com peso proporcional ao observado na pratica real
# (coordenadores e gerentes de TI concentram a maior parte da base)
TRILHAS = {
    "T-INFRA": {"peso": 35, "cargos": ["Coordenador de TI", "Coordenadora de Infraestrutura", "Coordenador de Suporte"], "oferta": "Outsourcing e alocacao de especialistas"},
    "T-GESTAO": {"peso": 28, "cargos": ["Gerente de TI", "IT Manager", "Gestor de Infraestrutura"], "oferta": "Otimizacao de nuvem e licenciamento"},
    "T-DADOS": {"peso": 15, "cargos": ["Analista de Dados", "Data Engineer", "Coordenador de Analytics", "Head de Dados"], "oferta": "Plataforma de dados e governanca"},
    "T-EXEC": {"peso": 10, "cargos": ["CTO", "Diretor de Tecnologia", "CISO", "VP de Engenharia"], "oferta": "Modernizacao e IA em producao"},
    "T-FIN": {"peso": 7, "cargos": ["CFO", "Gerente Financeiro", "Coordenador de Compras"], "oferta": "FinOps e contrato unico"},
    "T-PROD": {"peso": 5, "cargos": ["Product Manager", "Head de Produto"], "oferta": "IA embarcada no produto"},
}

SEGMENTOS_SETOR = ["Financeiro"] * 27 + ["Geral"] * 73  # ~27% financeiro, como na base real
ORIGENS = ["Outbound", "Inbound", "Indicacao", "Evento"]
STATUS_FUNIL = ["Novo", "Qualificando", "Qualificado", "Reuniao Agendada", "Perdido"]
SDRS = ["Camila Rocha", "Bruno Alves", "Fernanda Lima", "Rafael Souza", "Juliana Prado"]

CANAIS_POR_TRILHA = {
    "T-INFRA": ["Email", "WhatsApp"],
    "T-GESTAO": ["LinkedIn", "Email", "WhatsApp"],
    "T-DADOS": ["Email", "LinkedIn", "WhatsApp"],
    "T-EXEC": ["Email", "LinkedIn"],  # sem WhatsApp antes do D10, cadencia mais enxuta
    "T-FIN": ["Email", "LinkedIn"],
    "T-PROD": ["LinkedIn", "Email"],
}
RESULTADOS = ["Sem resposta", "Respondeu", "Objecao", "Reuniao marcada", "Nao perturbe"]
OBJECOES = [
    "",
    "",
    "Ja temos parceiro",
    "Nao e prioridade este ano",
    "Nao sou eu quem decide",
    "Orcamento comprometido",
    "Manda material por email",
]

# Resumos realistas por resultado, para dar contexto qualitativo alem
# do campo categorico (usado em consultas de texto no DuckDB)
RESUMOS_POR_RESULTADO = {
    "Sem resposta": [
        "Nenhuma resposta ate o momento",
        "Mensagem visualizada no LinkedIn, sem retorno",
    ],
    "Respondeu": [
        "Perguntou sobre volume de dados processado e tempo de implantacao",
        "Pediu mais detalhes sobre governanca e controle de acesso a dado sensivel",
        "Perguntou como funciona a alocacao de especialista sem abrir headcount",
        "Questionou sobre integracao com o ambiente de nuvem que ja usam",
        "Pediu para encaminhar o material para o time tecnico avaliar",
        "Confirmou interesse mas pediu para retomar apos o fechamento do trimestre",
    ],
    "Objecao": [
        "Disse que ja tem um parceiro atendendo esse escopo",
        "Informou que o orcamento do ano ja esta comprometido",
        "Disse que a decisao nao e dele, indicou outro contato",
        "Respondeu que nao e prioridade neste momento",
        "Pediu para so enviar material por email, sem call",
    ],
    "Reuniao marcada": [
        "Aceitou reuniao para apresentar a solucao em detalhe",
        "Confirmou call para semana seguinte para discutir escopo tecnico",
        "Reuniao marcada apos troca sobre caso de uso similar ao deles",
    ],
    "Nao perturbe": [
        "Pediu para nao ser mais contatado sobre o tema",
        "Solicitou remocao da lista de prospeccao",
    ],
}


def escolher_trilha() -> str:
    trilhas = list(TRILHAS.keys())
    pesos = [TRILHAS[t]["peso"] for t in trilhas]
    return random.choices(trilhas, weights=pesos)[0]


def data_aleatoria(dias_atras_min: int, dias_atras_max: int) -> date:
    dias = random.randint(dias_atras_min, dias_atras_max)
    return date.today() - timedelta(days=dias)


def gerar_empresas(n_empresas: int) -> list[str]:
    return [fake.company() for _ in range(n_empresas)]


def gerar_leads(n: int) -> list[dict]:
    # gera um pool de empresas menor que n para forcar contas com varios leads
    # (replicando o padrao real de concentracao account-based)
    n_empresas = max(1, int(n * 0.55))
    empresas = gerar_empresas(n_empresas)

    leads = []
    for lead_id in range(1, n + 1):
        trilha = escolher_trilha()
        cargo = random.choice(TRILHAS[trilha]["cargos"])
        setor = random.choice(SEGMENTOS_SETOR)
        empresa = random.choice(empresas)
        data_criacao = data_aleatoria(1, 180)

        leads.append(
            {
                "lead_id": lead_id,
                "nome_contato": fake.name(),
                "cargo": cargo,
                "empresa": empresa,
                "setor": setor,
                "trilha": trilha,
                "oferta_principal": TRILHAS[trilha]["oferta"],
                "origem": random.choice(ORIGENS),
                "responsavel_sdr": random.choice(SDRS),
                "status_funil": random.choices(
                    STATUS_FUNIL, weights=[20, 25, 20, 15, 20]
                )[0],
                "data_criacao": data_criacao.isoformat(),
                "icp_fit_score": random.randint(1, 5),
            }
        )

    # marca o modo (account-based x lead a lead) com base na contagem por empresa
    contagem_empresa: dict[str, int] = {}
    for lead in leads:
        contagem_empresa[lead["empresa"]] = contagem_empresa.get(lead["empresa"], 0) + 1
    for lead in leads:
        lead["modo"] = "Account-based" if contagem_empresa[lead["empresa"]] >= 4 else "Lead a lead"

    return leads


def gerar_interacoes(leads: list[dict]) -> list[dict]:
    interacoes = []
    interacao_id = 1
    for lead in leads:
        trilha = lead["trilha"]
        canais_possiveis = CANAIS_POR_TRILHA[trilha]
        n_interacoes = random.randint(2, 6) if trilha != "T-EXEC" else random.randint(2, 4)
        data_base = date.fromisoformat(lead["data_criacao"])

        for etapa in range(1, n_interacoes + 1):
            intervalo = random.randint(3, 5) if trilha == "T-INFRA" else random.randint(3, 6)
            data_interacao = data_base + timedelta(days=etapa * intervalo)
            if data_interacao > date.today():
                break

            # regra: T-EXEC nao usa WhatsApp antes da etapa 4 (~D10+)
            canal_opcoes = canais_possiveis
            if trilha == "T-EXEC" and etapa < 4:
                canal_opcoes = [c for c in canais_possiveis if c != "WhatsApp"]

            resultado = random.choices(
                RESULTADOS, weights=[40, 25, 15, 10, 10]
            )[0]
            objecao = random.choice(OBJECOES) if resultado == "Objecao" else ""
            resumo = random.choice(RESUMOS_POR_RESULTADO[resultado])

            interacoes.append(
                {
                    "interacao_id": interacao_id,
                    "lead_id": lead["lead_id"],
                    "canal": random.choice(canal_opcoes),
                    "etapa_cadencia": etapa,
                    "data_interacao": data_interacao.isoformat(),
                    "resultado": resultado,
                    "objecao_registrada": objecao,
                    "resumo_interacao": resumo,
                }
            )
            interacao_id += 1
    return interacoes


def salvar_csv(caminho: str, registros: list[dict]) -> None:
    if not registros:
        return
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=registros[0].keys())
        writer.writeheader()
        writer.writerows(registros)


if __name__ == "__main__":
    leads = gerar_leads(N_LEADS)
    interacoes = gerar_interacoes(leads)

    salvar_csv("data/leads.csv", leads)
    salvar_csv("data/interacoes_cadencia.csv", interacoes)

    print(f"Gerados {len(leads)} leads e {len(interacoes)} interacoes.")
