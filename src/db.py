"""
Camada de acesso a dados estruturados via DuckDB.

Carrega leads.csv e interacoes_cadencia.csv como tabelas relacionais
e expoe utilitarios para descrever o schema (usado no system prompt)
e executar consultas SQL geradas pela LLM a partir de perguntas em
linguagem natural.
"""

import duckdb

DATA_DIR = "data"

SCHEMA_DESCRIPTION = """
Tabela: leads
Colunas:
  - lead_id (INTEGER, chave primaria)
  - nome_contato (VARCHAR)
  - cargo (VARCHAR)
  - empresa (VARCHAR)
  - setor (VARCHAR) -- 'Financeiro' ou 'Geral'
  - trilha (VARCHAR) -- T-INFRA, T-GESTAO, T-DADOS, T-EXEC, T-FIN, T-PROD
  - oferta_principal (VARCHAR)
  - origem (VARCHAR) -- Outbound, Inbound, Indicacao, Evento
  - responsavel_sdr (VARCHAR)
  - status_funil (VARCHAR) -- Novo, Qualificando, Qualificado, Reuniao Agendada, Perdido
  - data_criacao (DATE)
  - icp_fit_score (INTEGER, 1 a 5)
  - modo (VARCHAR) -- 'Account-based' ou 'Lead a lead'

Tabela: interacoes_cadencia
Colunas:
  - interacao_id (INTEGER, chave primaria)
  - lead_id (INTEGER, chave estrangeira para leads.lead_id)
  - canal (VARCHAR) -- Email, WhatsApp, LinkedIn
  - etapa_cadencia (INTEGER)
  - data_interacao (DATE)
  - resultado (VARCHAR) -- Sem resposta, Respondeu, Objecao, Reuniao marcada, Nao perturbe
  - objecao_registrada (VARCHAR)
  - resumo_interacao (VARCHAR) -- descricao qualitativa do que aconteceu na interacao

As duas tabelas se relacionam por lead_id (1 lead para N interacoes).
"""


def get_connection() -> duckdb.DuckDBPyConnection:
    """Cria uma conexao DuckDB em memoria e carrega as tabelas a partir dos CSVs."""
    con = duckdb.connect(database=":memory:")
    con.execute(
        f"CREATE TABLE leads AS SELECT * FROM read_csv_auto('{DATA_DIR}/leads.csv')"
    )
    con.execute(
        f"CREATE TABLE interacoes_cadencia AS "
        f"SELECT * FROM read_csv_auto('{DATA_DIR}/interacoes_cadencia.csv')"
    )
    return con


def get_schema_description() -> str:
    """Retorna a descricao do schema, usada no system prompt para gerar SQL."""
    return SCHEMA_DESCRIPTION


def run_query(con: duckdb.DuckDBPyConnection, sql: str) -> list[dict]:
    """
    Executa uma consulta SQL e retorna os resultados como lista de dicts.

    Por seguranca, so permite comandos que comecem com SELECT (somente leitura).
    """
    sql_normalizado = sql.strip().lower()
    if not sql_normalizado.startswith("select"):
        raise ValueError("Somente consultas SELECT sao permitidas.")

    resultado = con.execute(sql).fetchdf()
    return resultado.to_dict(orient="records")


if __name__ == "__main__":
    # teste manual rapido
    con = get_connection()
    print(run_query(con, "SELECT trilha, COUNT(*) as total FROM leads GROUP BY trilha ORDER BY total DESC"))
    print(run_query(con, "SELECT resultado, COUNT(*) as total FROM interacoes_cadencia GROUP BY resultado"))