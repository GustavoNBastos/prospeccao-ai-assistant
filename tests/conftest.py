import json
import os
from datetime import datetime
from pathlib import Path

import pytest

os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")

RESULTADOS: list[dict] = []
PASTA = Path(__file__).parent / "resultados"


@pytest.fixture(scope="session", autouse=True)
def salvar_resultados():
    yield
    if not RESULTADOS:
        return
    PASTA.mkdir(exist_ok=True)
    tag = os.environ.get("AVALIACAO_TAG", datetime.now().strftime("%Y%m%d-%H%M"))
    (PASTA / f"{tag}.json").write_text(
        json.dumps(RESULTADOS, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n>> Resultados salvos em tests/resultados/{tag}.json")
