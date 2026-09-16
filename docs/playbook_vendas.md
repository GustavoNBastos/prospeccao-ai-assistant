# Playbook de Vendas - Prospecção B2B de Dados, Nuvem e IA

## 1. Visão Geral do Processo

Este playbook orienta SDRs e BDRs na condução de cadências de prospecção outbound e inbound, cobrindo abordagem inicial, qualificação, contorno de objeções e passagem de bastão para Account Executive.

O funil segue os estágios: **Novo → Qualificando → Qualificado → Reunião Agendada**. Um lead pode ser marcado como **Perdido** em qualquer etapa, com motivo registrado.

## 2. Segmentação por Trilha

Cada lead é classificado em uma trilha, de acordo com o cargo e o tipo de dor que ele resolve. Isso define a oferta a ser trabalhada e o tom da abordagem.

| Trilha | Perfil | Oferta Principal | Tom de Abordagem |
|---|---|---|---|
| **T-INFRA** | Coordenador de TI, Infraestrutura, Suporte | Outsourcing e alocação de especialistas | Direto, operacional, foco em "falta de gente" |
| **T-GESTAO** | Gerente de TI, IT Manager, Gestor | Otimização de nuvem e licenciamento | Foco em custo de ambiente e capacidade do time |
| **T-DADOS** | Analista de Dados, Data Engineer, Head de Dados | Plataforma de dados e governança | Técnico, com prova de escala e arquitetura |
| **T-EXEC** | CTO, Diretor de Tecnologia, CISO, VP | Modernização e IA em produção | Curto, executivo, foco em ROI |
| **T-FIN** | CFO, Gerente Financeiro, Compras | FinOps e contrato único | Foco em custo total (TCO) e simplificação de contrato |
| **T-PROD** | Product Manager, Head de Produto | IA embarcada no produto | Foco em caso de uso e experiência do usuário final |

**Regra de ouro**: nunca leve discurso de plataforma de dados e IA para T-INFRA e T-GESTAO na primeira abordagem. Esses perfis têm orçamento operacional, não de transformação. A entrada certa é sempre pela dor concreta (falta de gente, custo de ambiente) e, ao longo da conversa, buscar o direcionamento para quem decide investimento maior.

## 3. Modo de Execução: Lead a Lead vs Account-Based

Quando uma mesma empresa tem **4 ou mais leads** na base, o modo de execução muda para **Account-Based**:

1. Eleja uma **entrada principal** (o cargo mais sênior disponível na conta).
2. Escolha no máximo **dois contatos de apoio**, preferencialmente de trilhas diferentes.
3. Espace o contato entre pessoas da mesma empresa em pelo menos **3 dias**.
4. Nunca use a mesma mensagem para duas pessoas da mesma conta.
5. Se alguém responder, **pausar a cadência dos demais contatos da conta** e conduzir a conversa centralizada.

Empresas com até 3 leads seguem cadência normal, lead a lead.

## 4. Estrutura de Cadência por Trilha

| Trilha | Toques | Duração | Canal de Abertura | Observação |
|---|---|---|---|---|
| T-INFRA | 6 | 12 dias | E-mail, WhatsApp a partir do 3º toque | Mensagens curtas e diretas |
| T-GESTAO | 8 | 15 dias | LinkedIn + E-mail | Cadência completa, alternando canais |
| T-DADOS | 7 | 15 dias | E-mail técnico | Priorizar prova de escala e arquitetura |
| T-EXEC | 5 | 18 dias | E-mail curto | Sem WhatsApp antes do 4º toque (~D10) |
| T-FIN | 4 | 12 dias | E-mail | Falar apenas de custo e contrato |
| T-PROD | 4 | 12 dias | LinkedIn | Ancorar em caso de uso no produto |

## 5. Blocos de Abordagem por Frente de Oferta

**Migração e Otimização de Nuvem**
O ponto de dor recorrente não é a migração em si, mas o "depois": ambiente replicado com o mesmo desperdício de antes. A oferta inclui redesenho de consumo durante a migração, de forma que o custo do ambiente já mude a partir do segundo mês, com planejamento de janela de corte para não impactar a operação.

**Outsourcing e Alocação de Especialistas**
Quando o gargalo do cliente é capacidade de execução, e não ferramenta, a alocação de especialista sênior (dados, cloud ou IA) entra como despesa de projeto, sem necessidade de abrir headcount novo e sem o tempo de recrutamento tradicional (em geral 2 a 3 meses).

**Plataforma de Dados e Governança**
Unificação de ingestão, armazenamento (lakehouse) e tratamento de dado em uma fundação única, com governança e linhagem desde o início, reduzindo o número de ferramentas a sustentar e acelerando a entrada de novos casos de uso.

**IA Aplicada e Agentes**
O caso de uso e a camada de dado são tratados juntos, com agentes conectados aos sistemas já existentes do cliente. Essa combinação é o que diferencia um projeto que fica em piloto de um projeto que chega à operação contínua.

**FinOps e Licenciamento**
Revisão de consumo de nuvem e consolidação de licenciamento em contrato único, reduzindo a fragmentação entre múltiplos fornecedores e simplificando a gestão de SLA.

## 6. Critérios de Passagem para Account Executive (AE)

Um lead está pronto para passagem quando:
- Está em uma trilha compatível com a oferta discutida (T-DADOS, T-EXEC ou T-FIN em estágio avançado).
- Confirmou dor específica e teve reunião marcada.
- `icp_fit_score` maior ou igual a 4.
- Não há sinalização de "já tem parceiro atendendo" sem espaço de complementaridade identificado.

## 7. Boas Práticas de Volume

Em contas com concentração alta de leads (Account-Based), não disparar mais de 40 a 50 mensagens por dia para o mesmo domínio de e-mail, para preservar a taxa de entregabilidade.
