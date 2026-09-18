"""
Camada de RAG (Retrieval-Augmented Generation).

Le os documentos de dominio em docs/, faz chunking por secao (headings
markdown), indexa no ChromaDB com a funcao de embedding padrao, e expoe
uma funcao de retrieval para buscar os trechos mais relevantes dada
uma pergunta em linguagem natural.
"""

import glob
import os
import re

import chromadb

DOCS_DIR = "docs"
CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "documentos_dominio"


def _chunk_por_secao(texto: str, nome_arquivo: str) -> list[dict]:
    """
    Divide o markdown em chunks por secao de segundo nivel (##).
    Cada chunk carrega metadata com o arquivo de origem e o titulo da secao,
    para facilitar rastreabilidade da resposta gerada.
    """
    secoes = re.split(r"\n(?=## )", texto)
    chunks = []
    for secao in secoes:
        secao = secao.strip()
        if not secao:
            continue
        primeira_linha = secao.split("\n", 1)[0]
        titulo = primeira_linha.replace("#", "").strip()
        chunks.append(
            {
                "texto": secao,
                "fonte": nome_arquivo,
                "titulo_secao": titulo or nome_arquivo,
            }
        )
    return chunks


def build_index() -> chromadb.Collection:
    """
    Le todos os .md de docs/, faz chunking e (re)cria a colecao no ChromaDB.
    Deve ser chamado uma vez na inicializacao da aplicacao (ou via script
    de ingestao separado).
    """
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # recria a colecao para evitar duplicar chunks em re-execucoes
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    documentos: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []
    contador = 0

    for caminho in sorted(glob.glob(os.path.join(DOCS_DIR, "*.md"))):
        nome_arquivo = os.path.basename(caminho)
        with open(caminho, "r", encoding="utf-8") as f:
            texto = f.read()

        for chunk in _chunk_por_secao(texto, nome_arquivo):
            documentos.append(chunk["texto"])
            metadatas.append({"fonte": chunk["fonte"], "titulo_secao": chunk["titulo_secao"]})
            ids.append(f"chunk-{contador}")
            contador += 1

    if documentos:
        collection.add(documents=documentos, metadatas=metadatas, ids=ids)

    return collection


def get_collection() -> chromadb.Collection:
    """Abre a colecao ja indexada (sem reindexar)."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_collection(COLLECTION_NAME)


def retrieve(pergunta: str, top_k: int = 3) -> list[dict]:
    """
    Busca os top_k chunks mais relevantes para a pergunta.
    Retorna lista de dicts com texto, fonte e titulo da secao.
    """
    collection = get_collection()
    resultado = collection.query(query_texts=[pergunta], n_results=top_k)

    chunks = []
    for texto, metadata in zip(resultado["documents"][0], resultado["metadatas"][0]):
        chunks.append(
            {
                "texto": texto,
                "fonte": metadata.get("fonte"),
                "titulo_secao": metadata.get("titulo_secao"),
            }
        )
    return chunks


if __name__ == "__main__":
    print("Indexando documentos...")
    collection = build_index()
    print(f"Total de chunks indexados: {collection.count()}")

    print("\nTeste de retrieval:")
    pergunta_teste = "Como funciona a alocacao de especialista sem abrir headcount?"
    for chunk in retrieve(pergunta_teste, top_k=2):
        print(f"\n[{chunk['fonte']} | {chunk['titulo_secao']}]")
        print(chunk["texto"][:200], "...")