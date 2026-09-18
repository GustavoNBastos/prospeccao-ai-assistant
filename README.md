# Assistente de Prospecção e Vendas B2B

Projeto da disciplina **AI Factory: Building Intelligent Systems** (PUC-PR, Graduação 4D), desenvolvido em três etapas usando a metodologia Challenge Based Learning (CBL).

## Declaração do Desafio (CBL)

**Grande Ideia**
Eficiência e inteligência comercial na prospecção B2B, reduzindo a dependência de conhecimento tácito disperso entre vendedores.

**Pergunta Essencial**
Como a tecnologia pode ajudar equipes de SDR/BDR a tomar decisões melhores em tempo real durante a prospecção, sem depender exclusivamente da experiência individual de cada vendedor?

**Desafio**
Criar um assistente inteligente que responda dúvidas sobre playbooks de vendas e técnicas de contorno de objeções, consulte o histórico de leads e o andamento de cadências de prospecção, e sirva de base para, nas próximas etapas, prever a probabilidade de conversão de um lead e orquestrar agentes autônomos capazes de sugerir a próxima melhor ação comercial.

**Justificativa Pessoal**
Minha trajetória profissional ao longo dos últimos anos me aproximou cada vez mais da tecnologia e das diferentes formas de comércio e negociação que o mercado oferece. Atuando há mais de 4 anos como profissional sênior de Desenvolvimento de Contas para grandes empresas de tecnologia, sempre observei que boa parte do processo de prospecção, seja Outbound ou Inbound, consumia um tempo desproporcional dos vendedores com tarefas operacionais, tempo que poderia estar sendo usado para vender de fato ou construir relacionamento com potenciais clientes. Montar listas extensas de contatos, pesquisar cada conta manualmente e decidir a abordagem certa em meio a uma agenda cheia de reuniões era um desafio recorrente. Foi dessa vivência que nasceu a ideia deste projeto: substituir grande parte desse trabalho manual e analítico por um assistente capaz de personalizar e disparar e mails, mensagens de WhatsApp e LinkedIn, além de analisar cada lead e indicar a melhor forma de atendê lo.

## Status do Projeto

- [ ] Etapa 1: Interface, dados estruturados e RAG (entrega semana 6)
- [ ] Etapa 2: Modelo de ML, agentes e observabilidade (entrega semana 10)
- [ ] Etapa 3: Segurança, deploy e documentação final (entrega semana 13)

## Stack Tecnológica

- **Interface**: Streamlit
- **Dados estruturados**: DuckDB
- **RAG**: ChromaDB + embeddings (sentence-transformers)
- **LLM**: Anthropic Claude
- **Observabilidade** (Etapa 2): Langfuse
- **Testes** (Etapa 2): DeepEval

## Estrutura do Repositório

```
prospeccao-ai-assistant/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── data/
│   ├── leads.csv
│   └── interacoes_cadencia.csv
├── docs/
│   ├── playbook_vendas.md
│   ├── matriz_objecoes.md
│   └── guia_icp_qualificacao.md
├── src/
│   ├── db.py
│   ├── rag.py
│   ├── llm.py
│   ├── prompts.py
│   └── ingest.py
└── scripts/
    └── gerar_dados_sinteticos.py
```

##Como Rodar Localmente

Clone o repositório e entre na pasta do projeto.

Crie e ative um ambiente virtual:
   python -m venv venv
   .\venv\Scripts\Activate   # Windows (PowerShell)
   source venv/bin/activate  # Linux/Mac

Instale as dependências:
   pip install -r requirements.txt
Copie .env.example para .env e preencha com sua chave de API da Anthropic:
   ANTHROPIC_API_KEY=sua_chave_aqui
Gere os dados sintéticos (ou use os já versionados em data/):
   python scripts/gerar_dados_sinteticos.py
(Opcional) Teste as camadas isoladamente:
   python src/db.py
   python src/rag.py
   python src/llm.py
Rode a aplicação:
   streamlit run app.py

Acesse http://localhost:8501 no navegador.

##Limitações Conhecidas

Os dados de leads e interações são sintéticos, gerados por script (scripts/gerar_dados_sinteticos.py), inspirados na lógica real de segmentação por trilha, mas sem corresponder a leads reais.

O RAG usa a função de embedding padrão do ChromaDB (modelo local all-MiniLM-L6-v2), sem ajuste fino para o domínio específico de prospecção B2B.

Não há ainda modelo preditivo de conversão de lead (previsto para a Etapa 2).

Não há agentes autônomos orquestrados nem observabilidade (Langfuse) ou testes automatizados (DeepEval), também previstos para a Etapa 2.

Não há camada de segurança/guardrails contra prompt injection ou vazamento de dado sensível (previsto para a Etapa 3).
O histórico da conversa existe apenas durante a sessão do Streamlit (session_state), sem persistência entre execuções.