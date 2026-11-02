"""Resume uma execucao ou compara duas:  python tests/comparar.py antes [depois]"""
import json
import sys
from collections import defaultdict
from pathlib import Path

PASTA = Path(__file__).parent / "resultados"


def carregar(tag):
    return json.loads((PASTA / f"{tag}.json").read_text(encoding="utf-8"))


def media(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 3) if xs else None


def resumo(dados):
    por_cat = defaultdict(list)
    for d in dados:
        por_cat[d["categoria"]].append(d)
    linhas = {}
    for cat, itens in por_cat.items():
        linhas[cat] = {
            "n": len(itens),
            "aprovados": sum(i["aprovado"] for i in itens),
            "faithfulness": media([i["metricas"]["faithfulness"]["score"] for i in itens]),
            "answer_relevancy": media([i["metricas"].get("answer_relevancy", {}).get("score") for i in itens]),
            "rota_ok": sum(i["rota_ok"] for i in itens),
            "latencia_s": media([i["segundos"] for i in itens]),
        }
    linhas["TOTAL"] = {
        "n": len(dados), "aprovados": sum(d["aprovado"] for d in dados),
        "faithfulness": media([d["metricas"]["faithfulness"]["score"] for d in dados]),
        "answer_relevancy": media([d["metricas"].get("answer_relevancy", {}).get("score") for d in dados]),
        "rota_ok": sum(d["rota_ok"] for d in dados), "latencia_s": media([d["segundos"] for d in dados]),
    }
    return linhas


def imprimir(tag, dados):
    holdout = [d for d in dados if d.get("conjunto") == "holdout"]
    if holdout:
        principal = [d for d in dados if d.get("conjunto") != "holdout"]
        _imprimir(f"{tag} (conjunto principal)", principal)
        _imprimir(f"{tag} (holdout, nao usado para ajustes)", holdout)
    else:
        _imprimir(tag, dados)


def _imprimir(tag, dados):
    print(f"\n== {tag} ==")
    print(f"{'categoria':16}{'n':>3}{'aprov.':>8}{'faith.':>8}{'relev.':>8}{'rota':>6}{'lat(s)':>8}")
    for cat, r in resumo(dados).items():
        print(f"{cat:16}{r['n']:>3}{r['aprovados']:>8}{str(r['faithfulness']):>8}{str(r['answer_relevancy']):>8}{r['rota_ok']:>6}{str(r['latencia_s']):>8}")
    print("\nReprovados:")
    for d in dados:
        if not d["aprovado"]:
            falhas = [f"{n}={m['score']}" for n, m in d["metricas"].items() if not m["ok"]]
            print(f"  {d['id']} ({d['categoria']}): {', '.join(falhas)}"
                  f"{'' if d['rota_ok'] else ' | rota errada'}{'' if d['ferramentas_ok'] else ' | ferramenta esperada nao usada'}")


if __name__ == "__main__":
    tags = sys.argv[1:] or [sorted(p.stem for p in PASTA.glob('*.json'))[-1]]
    for t in tags:
        imprimir(t, carregar(t))
