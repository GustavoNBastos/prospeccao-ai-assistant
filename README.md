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

## Como Rodar Localmente

*(seção a ser preenchida conforme a aplicação for implementada)*

## Limitações Conhecidas

*(seção a ser preenchida ao longo do desenvolvimento)*
