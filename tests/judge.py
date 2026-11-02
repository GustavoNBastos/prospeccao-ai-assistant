"""Claude como juiz do DeepEval (em vez do padrao OpenAI)."""

import json
import os
import re

import anthropic
from deepeval.models import DeepEvalBaseLLM
from dotenv import load_dotenv

load_dotenv()

JUIZ_MODELO = os.environ.get("JUIZ_MODELO", "claude-sonnet-5")


def _extrair_json(texto: str) -> dict:
    texto = re.sub(r"^```(?:json)?|```$", "", texto.strip(), flags=re.M).strip()
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fim == -1:
        raise ValueError(f"sem JSON na resposta do juiz: {texto[:200]!r}")
    return json.loads(texto[inicio:fim + 1])


class ClaudeJuiz(DeepEvalBaseLLM):
    def __init__(self, modelo: str = JUIZ_MODELO):
        self.modelo = modelo
        self._cliente = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self._cliente_async = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def load_model(self):
        return None

    def get_model_name(self):
        return f"Claude ({self.modelo})"

    @staticmethod
    def _prompt(prompt: str, schema) -> str:
        if schema is None:
            return prompt
        return (
            f"{prompt}\n\nResponda APENAS com um objeto JSON valido (sem texto antes ou depois, "
            f"sem markdown) que siga exatamente este JSON Schema:\n"
            f"{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
        )

    @staticmethod
    def _texto(resposta) -> str:
        return "".join(b.text for b in resposta.content if b.type == "text")

    def generate(self, prompt: str, schema=None, **_):
        ultimo_erro = None
        for _tentativa in range(3):
            resposta = self._cliente.messages.create(
                model=self.modelo, max_tokens=8000,
                messages=[{"role": "user", "content": self._prompt(prompt, schema)}],
            )
            texto = self._texto(resposta)
            if schema is None:
                return texto
            try:
                return schema.model_validate(_extrair_json(texto))
            except Exception as erro:  # JSON invalido: tenta de novo
                ultimo_erro = erro
        raise ValueError(f"juiz nao devolveu JSON valido apos 3 tentativas: {ultimo_erro}")

    async def a_generate(self, prompt: str, schema=None, **_):
        ultimo_erro = None
        for _tentativa in range(3):
            resposta = await self._cliente_async.messages.create(
                model=self.modelo, max_tokens=8000,
                messages=[{"role": "user", "content": self._prompt(prompt, schema)}],
            )
            texto = self._texto(resposta)
            if schema is None:
                return texto
            try:
                return schema.model_validate(_extrair_json(texto))
            except Exception as erro:
                ultimo_erro = erro
        raise ValueError(f"juiz nao devolveu JSON valido apos 3 tentativas: {ultimo_erro}")
