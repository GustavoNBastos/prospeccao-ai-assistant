"""Inferência do modelo de propensão de conversão (Etapa 2).

O modelo foi treinado no UCI Bank Marketing, então as variáveis de entrada são as
do dataset (perfil do contato e histórico da campanha). Ele funciona como um
PROXY de propensão de conversão em abordagem outbound, não como um modelo treinado
com os leads B2B da Semantix. Essa limitação é informada em todo resultado.
"""
from pathlib import Path

import joblib
import pandas as pd

MODELO_PATH = Path(__file__).resolve().parent.parent / "models" / "lead_scoring.joblib"

# Valores usados quando o usuário não informa o campo (campo ausente = desconhecido).
PADROES = {
    "age": 40, "balance": 500, "day_of_week": 15, "campaign": 2,
    "pdays": -1, "previous": 0,
}
CATEGORICAS_PADRAO = "desconhecido"

DESCRICAO_CAMPOS = {
    "age": "idade do contato (anos)",
    "job": "profissão (admin., technician, management, services, retired, student...)",
    "marital": "estado civil (married, single, divorced)",
    "education": "escolaridade (primary, secondary, tertiary)",
    "default": "tem inadimplência (yes/no)",
    "balance": "saldo médio anual em euros",
    "housing": "tem financiamento imobiliário (yes/no)",
    "loan": "tem empréstimo pessoal (yes/no)",
    "contact": "canal do último contato (cellular, telephone)",
    "day_of_week": "dia do mês do último contato (1 a 31)",
    "month": "mês do último contato (jan, feb, mar, ..., dec)",
    "campaign": "número de contatos nesta campanha",
    "pdays": "dias desde o último contato de campanha anterior (-1 = nunca)",
    "previous": "número de contatos antes desta campanha",
    "poutcome": "resultado da campanha anterior (success, failure, other)",
}

_cache = {}


def _carregar() -> dict:
    if "pacote" not in _cache:
        if not MODELO_PATH.exists():
            raise FileNotFoundError(
                "Modelo não encontrado. Rode: python ml/train_model.py")
        _cache["pacote"] = joblib.load(MODELO_PATH)
    return _cache["pacote"]


def prever_conversao(**campos) -> dict:
    """Retorna probabilidade de conversão e classificação para um contato."""
    pacote = _carregar()
    colunas, categorias = pacote["colunas"], pacote["categorias"]
    desconhecidos = [c for c in campos if c not in colunas]

    linha = {}
    for col in colunas:
        if col in categorias:
            valor = str(campos.get(col, CATEGORICAS_PADRAO))
            if valor not in categorias[col]:
                valor = None  # categoria não vista no treino: tratada como ausente
            linha[col] = pd.Categorical([valor], categories=categorias[col])
        else:
            linha[col] = [campos.get(col, PADROES.get(col, 0))]
    X = pd.DataFrame(linha)

    proba = float(pacote["modelo"].predict_proba(X)[0, 1])
    thr = float(pacote["threshold"])
    informados = [c for c in campos if c in colunas]
    return {
        "probabilidade_conversao": round(proba, 4),
        "threshold_de_decisao": round(thr, 4),
        "classe": "priorizar" if proba >= thr else "baixa prioridade",
        "campos_informados": informados,
        "campos_ignorados": desconhecidos,
        "aviso": ("Modelo treinado no UCI Bank Marketing (proxy de propensão em "
                  "outbound). Use como apoio à priorização, não como decisão final. "
                  "Quanto menos campos informados, menos confiável o resultado."),
    }


if __name__ == "__main__":
    print(prever_conversao(age=55, job="retired", balance=3000, poutcome="success"))
