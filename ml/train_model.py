"""Treino do modelo de propensão de conversão (Etapa 2).

Dataset: UCI Bank Marketing (id 222), campanhas de telemarketing de um banco.
Alvo: y (o cliente assinou o produto?). Analogia com SDR: lead converte ou não.

Decisões:
- `duration` é removida: só é conhecida DEPOIS da ligação (vazamento de dados).
- Split estratificado 80/20 com seed fixa, pois a classe positiva é ~12%.
- AutoML com FLAML otimizando ROC-AUC (métrica de ranking de leads).
- Threshold escolhido num holdout interno do treino (recall >= 0.60), sem tocar no teste.

Uso:
    python ml/train_model.py                # baixa o dataset da UCI
    python ml/train_model.py --demo-offline # dados sintéticos, só para testar o pipeline
    python ml/train_model.py --budget 120   # segundos de busca do FLAML
"""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from flaml import AutoML
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_recall_curve, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split

SEED = 42
RAIZ = Path(__file__).resolve().parent.parent
MODELO_PATH = RAIZ / "models" / "lead_scoring.joblib"
METRICAS_PATH = RAIZ / "models" / "metrics.json"
RECALL_ALVO = 0.60


def carregar_uci() -> tuple[pd.DataFrame, pd.Series]:
    from ucimlrepo import fetch_ucirepo
    d = fetch_ucirepo(id=222)
    X = d.data.features.copy()
    y = d.data.targets.iloc[:, 0].map({"yes": 1, "no": 0})
    return X, y


def carregar_demo() -> tuple[pd.DataFrame, pd.Series]:
    """Dados sintéticos com as mesmas colunas. NÃO usar para resultado final."""
    rng = np.random.default_rng(SEED)
    n = 6000
    X = pd.DataFrame({
        "age": rng.integers(18, 90, n),
        "job": rng.choice(["admin.", "technician", "services", "management", "retired", "student"], n),
        "marital": rng.choice(["married", "single", "divorced"], n),
        "education": rng.choice(["primary", "secondary", "tertiary", None], n),
        "default": rng.choice(["no", "yes"], n, p=[.98, .02]),
        "balance": rng.normal(1300, 3000, n).round(),
        "housing": rng.choice(["yes", "no"], n),
        "loan": rng.choice(["yes", "no"], n, p=[.16, .84]),
        "contact": rng.choice(["cellular", "telephone", None], n),
        "day_of_week": rng.integers(1, 31, n),
        "month": rng.choice(["jan", "mar", "may", "jun", "aug", "oct"], n),
        "duration": rng.integers(0, 1500, n),
        "campaign": rng.integers(1, 20, n),
        "pdays": rng.choice([-1, 30, 90, 200], n, p=[.8, .08, .07, .05]),
        "previous": rng.integers(0, 5, n),
        "poutcome": rng.choice(["success", "failure", "other", None], n, p=[.03, .1, .04, .83]),
    })
    z = (-2.6 + 1.8 * (X.poutcome == "success") + 0.5 * (X.job.isin(["retired", "student"]))
         + 0.0003 * X.balance - 0.08 * X.campaign + 0.5 * X.month.isin(["mar", "oct"]))
    y = pd.Series((rng.random(n) < 1 / (1 + np.exp(-z))).astype(int))
    return X, y


def preparar(X: pd.DataFrame) -> pd.DataFrame:
    X = X.drop(columns=["duration"], errors="ignore")
    for c in X.select_dtypes(include=["object", "string"]).columns:
        X[c] = X[c].fillna("desconhecido").astype("category")
    return X


def escolher_threshold(y_val, proba_val) -> float:
    """Maior threshold que ainda entrega recall >= RECALL_ALVO na validação."""
    prec, rec, thr = precision_recall_curve(y_val, proba_val)
    ok = [t for r, t in zip(rec[:-1], thr) if r >= RECALL_ALVO]
    return float(max(ok)) if ok else 0.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo-offline", action="store_true")
    ap.add_argument("--budget", type=int, default=60)
    a = ap.parse_args()

    X, y = carregar_demo() if a.demo_offline else carregar_uci()
    X = preparar(X)
    print(f"Linhas: {len(X)} | positivos: {y.mean():.1%} | features: {X.shape[1]}")

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=SEED)
    # holdout interno do treino, só para escolher o threshold sem tocar no teste
    X_fit, X_val, y_fit, y_val = train_test_split(
        X_tr, y_tr, test_size=0.2, stratify=y_tr, random_state=SEED)

    automl = AutoML()
    automl.fit(X_train=X_fit, y_train=y_fit, task="classification",
               metric="roc_auc", time_budget=a.budget, seed=SEED,
               eval_method="cv", n_splits=3, verbose=0)
    print("Melhor modelo:", automl.best_estimator, automl.best_config)

    thr = escolher_threshold(y_val, automl.predict_proba(X_val)[:, 1])

    proba = automl.predict_proba(X_te)[:, 1]
    pred = (proba >= thr).astype(int)
    metricas = {
        "dataset": "UCI Bank Marketing (id 222)" if not a.demo_offline else "SINTETICO (teste)",
        "n_treino": int(len(X_tr)), "n_teste": int(len(X_te)),
        "taxa_positivos": float(y.mean()),
        "melhor_modelo": automl.best_estimator,
        "threshold": thr,
        "accuracy": accuracy_score(y_te, pred),
        "precision": precision_score(y_te, pred, zero_division=0),
        "recall": recall_score(y_te, pred),
        "f1": f1_score(y_te, pred),
        "roc_auc": roc_auc_score(y_te, proba),
        "baseline_accuracy_classe_majoritaria": float(1 - y_te.mean()),
        "matriz_confusao": confusion_matrix(y_te, pred).tolist(),
    }
    metricas = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in metricas.items()}
    print(json.dumps(metricas, indent=2, ensure_ascii=False))

    MODELO_PATH.parent.mkdir(exist_ok=True)
    joblib.dump({"modelo": automl, "threshold": thr,
                 "colunas": list(X.columns),
                 "categorias": {c: list(X[c].cat.categories) for c in X.select_dtypes("category")}},
                MODELO_PATH)
    METRICAS_PATH.write_text(json.dumps(metricas, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Salvo: {MODELO_PATH.name}, {METRICAS_PATH.name}")


if __name__ == "__main__":
    main()
