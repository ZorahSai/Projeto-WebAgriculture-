# Diário da Tarefa 1 — Problema e coleta bruta (sem rótulo)

**Período:** 17/08/2026 a 17/09/2026  
**Projeto:** Preditor de degradação de rede com RTT normalizado (independente da rota)  
**Modelo desta disciplina:** árvore de decisão. Nesta tarefa não se treina árvore.

**Equipe:** WebAgriculture  
**Integrantes:** Apollo Moura De Sousa, Icaro Luiz Dellalo Silva, Ieda de Oliveira, João Pedro C. de Morais, Lucas Matteus Baptista de Godoy  
**Scrum Master da tarefa:** [a preencher pela equipe]  
**Repositório GitHub:** https://github.com/ZorahSai/Projeto-WebAgriculture-

> Esta tarefa entrega o problema e o **dado cru**. Não há classe OK, RISCO ou FALHA. Não há baseline, não há mediana e não há árvore.

### Contrato desta tarefa

| | Artefato | Onde está |
|---|---|---|
| **Sai** | RFC preenchido pelo grupo | [`docs/RFC_Preditor_Degradacao_Rede.md`](../RFC_Preditor_Degradacao_Rede.md) |
| **Sai** | Dicionário v0.1 só com colunas **brutas** | [`docs/dicionario_v0.1.md`](../dicionario_v0.1.md) |
| **Sai** | `data/raw/` + `config/` + `requirements.txt` | `data/raw/json/`, `data/raw/medicoes_brutas.csv.gz`, `config/coleta.json`, `requirements.txt` |
| **Sai** | Este diário | `docs/diarios/Tarefa1_Coleta_Bruta.md` |

---

## 1. Definição do problema

| Pergunta | Resposta do grupo |
|---|---|
| Qual evento a árvore vai classificar? | A degradação do fluxo em relação ao **próprio** normal: OK, RISCO ou FALHA. Não é "rota longa" nem "RTT acima de 100 ms". |
| O que é um fluxo? | `fluxo_id = probe_id\|dst_addr`: a Anchor de origem (`prb_id`) e o IP da Anchor de destino. O `measurement_id` fica registrado em cada linha. |
| O que é cada linha do bruto? | Uma medição ICMP desse fluxo: rajada de 3 pings do mesh de Anchors, a cada 240 s, com timestamp UTC. Ainda **sem** classe. |
| Qual horizonte fica para depois? | Detector: o estado da medição atual. Preditor: o estado 12 minutos à frente. A árvore só entra na Tarefa 3. |
| Quem usa o alerta? | Quem opera o enlace: investigar (FALHA), observar (RISCO) ou não agir (OK). |
| O que está proibido como definição de falha? | Limiar global de RTT, país, continente ou nome da rota. |

- [x] RFC do grupo preenchido a partir desta tabela: [`docs/RFC_Preditor_Degradacao_Rede.md`](../RFC_Preditor_Degradacao_Rede.md)
- [x] Dicionário v0.1 só com variáveis brutas

## 2. O que coletar (e o que não criar)

Fonte: medições públicas e contínuas de ping IPv4 entre Anchors do RIPE Atlas, **somente `GET`**. Nenhuma medição foi criada e nenhum crédito foi gasto.

| Campo | Coluna em `data/raw/medicoes_brutas.csv.gz` |
|---|---|
| `timestamp` | `timestamp` (UTC) |
| `measurement_id` | `measurement_id` |
| `probe_id` | `probe_id` |
| `dst_addr` | `dst_addr` |
| `fluxo_id` | `fluxo_id` (`probe_id\|dst_addr`) |
| RTT da rajada | `latencia_ms` (`avg`), `rtt_min_ms`, `rtt_max_ms`. Vazio se não houver resposta, **nunca 0** |
| enviados, recebidos | `enviados`, `recebidos` |
| `perda_pct` | `perda_pct` = (enviados − recebidos) / enviados × 100 |
| `jitter_ms` | `jitter_ms`: desvio-padrão amostral dos RTT da rajada, só com 2 ou mais respostas. Senão, vazio |
| `timeout_atual` | `timeout_atual` = 1 se não há RTT ou se a perda é 100% |
| país ou rota | `destino_fqdn`, `regiao`, `pais_origem`, `src_addr`: **só auditoria**, fora da futura árvore |

Desenho da coleta:

- **Destinos e origens:** 20 Anchors de destino em 7 países (BR 5, US 3, CO 3, DE 3, JP 2, NZ 2, FI 2). Cada destino tem 5 Anchors de origem da mesma região, num total de 100 pares, sorteados com semente 42 no `Coleta de Dados/coleta_multidestino.ipynb`.
- **Auto-ping excluído:** três pares mediam a própria Anchor de destino (`7019 → br-pgz`, `6349 → br-poa` e `7694 → co-ptx`, com RTT perto de 0,2 ms). Pela seção 5 do Guia de Coleta, eles ficaram de fora. O motivo está marcado em `config/coleta.json`. Restam **97 fluxos**.
- **Blocos de download:** um dia por pedido (`bloco_horas` = 24), 280 blocos ao todo (20 destinos × 14 dias).

Regras da coleta:

- [x] **Vários fluxos, com caminho curto e caminho longo no mesmo período:** os RTTs medianos vão de 0,97 ms (NZ → nz-akl) a 317,9 ms (IQ → jp-tch).
- [x] **A diversidade geográfica está documentada e não virou classe:** a região e o país ficam só em colunas de auditoria.
- [x] **Dois blocos de tempo contíguos e sem sobreposição:**
  - Período A: 06/09/2026 04:32 a 13/09/2026 04:32 UTC.
  - Período B: 13/09/2026 04:32 a 20/09/2026 04:32 UTC.
  - Cada linha recebe o período pelo instante da medição. O fim de A é exclusivo.
- [x] **Timeout permanece no arquivo:** são 21.349 medições com `timeout_atual` = 1.
- [x] **JSON bruto preservado:**
  - As respostas da API estão em `data/raw/json/<destino>/m<id>_<início>_<fim>.json.gz`, com os bytes originais compactados.
  - Cada bloco tem um `.meta.json` com URL, parâmetros, status HTTP e SHA-256.
  - A tabela é refeita a partir desses arquivos, sem alterá-los.
- [x] **Parâmetros em `config/coleta.json`:** períodos, probes, destinos, exclusões, timeout e número de tentativas.
- [x] **HTTP com timeout e nova tentativa em erro transitório:** 120 s e 4 tentativas, para timeout, 429 e 5xx.
- [x] **Coleta idempotente:** rodar de novo não baixa um bloco que já existe. Isso foi testado: a segunda execução não baixou nenhum dos 280 arquivos.
- [x] **`requirements.txt` da coleta.**

**Evidências:**
- Código: `src/coletar_bruto.py` (coleta), `src/montar_tabela_bruta.py` (tabela) e `src/relatorio_qualidade.py` (relatório).
- Configuração: `config/coleta.json`.
- Commits: https://github.com/ZorahSai/Projeto-WebAgriculture-/commits/main/docs/RFC_Preditor_Degradacao_Rede.md (RFC) e https://github.com/ZorahSai/Projeto-WebAgriculture-/commits/main/src (coleta).

## 3. Relatório de qualidade — ainda sem classe

Relatório completo: [`docs/relatorio_qualidade_tarefa1.md`](../relatorio_qualidade_tarefa1.md).

- [x] Registros por `fluxo_id`: de 4.486 a 5.040, com cerca de 2.520 por período, o que corresponde a 360 por dia.
- [x] Início e fim de cada fluxo: entre 06/09 04:32 e 20/09 04:31 UTC, detalhados por fluxo no relatório.
- [x] Campos ausentes: 21.349 RTT vazios (timeouts) e 22.304 jitters vazios (menos de 2 respostas). Nenhum RTT foi gravado como 0.
- [x] Duplicatas: 0 (mesmo `fluxo_id` e `timestamp`).
- [x] Timeouts: 21.349.
- [x] RTT e perda descritos sem dizer OK, RISCO ou FALHA:
  - RTT: mínimo 0,71 ms, mediana 68,22 ms, máximo 1.326,44 ms.
  - Perda: mínimo 0%, mediana 0%, máximo 100%.

**N de registros brutos:** 486.487 (243.051 no Período A e 243.436 no Período B). Também ficaram fora da tabela 15.105 registros dos três fluxos de auto-ping. Nenhum registro sem pacotes enviados foi encontrado.  
**N de fluxos:** 97, em 20 destinos.  
**Caminho curto e caminho longo presentes:**
- **Curtos:** 6904 → nz-akl (NZ, 0,97 ms), 6659 → br-sao (BR, 1,28 ms), 6904 → nz-npl (NZ, 5,66 ms).
- **Longos:** 6505 → jp-tch (GE, 309,5 ms), 7628 → jp-tyo (AZ, 310,0 ms), 7020 → jp-tch (IQ, 317,9 ms).

**Observação para a Tarefa 2:** os 5 fluxos para `co-bog-as273103` (Bogotá) tiveram cerca de 958 RTTs válidos no Período A. Ficam abaixo do piso de 1.500 e não vão receber classe.

## 4. Scrum

- [ ] Product Owner = docente; Scrum Master da tarefa; time de desenvolvimento [a preencher pela equipe]
- [ ] Board com To do / Doing / Done [a preencher pela equipe]
- [x] Pelo menos 3 histórias (rascunho abaixo; a equipe pode ajustar)

**Histórias:**
1. Como analista de rede, quero coletar medições de ping de vários fluxos, com caminhos curtos e longos, para ter dados que não confundam distância com falha.
2. Como analista de rede, quero preservar a resposta bruta da API com os timeouts e sem RTT igual a 0, para poder auditar e refazer qualquer tabela.
3. Como cientista de dados, quero separar o Período A do Período B sem rotular nada, para que o baseline da Tarefa 2 não use as medições que serão rotuladas.

**Link do board:** [a preencher pela equipe]

## 5. Diário de bordo

| Integrante | O que fiz nesta tarefa | Dificuldades | O que pretendo manter/ajustar |
|---|---|---|---|
| Apollo Moura De Sousa | [a preencher] | [a preencher] | [a preencher] |
| Icaro Luiz Dellalo Silva | [a preencher] | [a preencher] | [a preencher] |
| Ieda de Oliveira | [a preencher] | [a preencher] | [a preencher] |
| João Pedro C. de Morais | [a preencher] | [a preencher] | [a preencher] |
| Lucas Matteus Baptista de Godoy | [a preencher] | [a preencher] | [a preencher] |

Dificuldades técnicas registradas, para a equipe aproveitar no diário:
- Três pares eram auto-ping e foram identificados pelo RTT de cerca de 0,2 ms.
- A Anchor de Bogotá respondeu pouco no Período A.
- O jitter precisou ser guardado com 6 casas decimais, para que o arredondamento não criasse jitter igual a 0.

## 6. Evidências gerais

- Link do RFC: https://github.com/ZorahSai/Projeto-WebAgriculture-/blob/main/docs/RFC_Preditor_Degradacao_Rede.md
- Link do dicionário v0.1: https://github.com/ZorahSai/Projeto-WebAgriculture-/blob/main/docs/dicionario_v0.1.md
- Link dos commits: https://github.com/ZorahSai/Projeto-WebAgriculture-/commits/main
- Link de `data/raw/` e do `config/`: https://github.com/ZorahSai/Projeto-WebAgriculture-/tree/main/data/raw e https://github.com/ZorahSai/Projeto-WebAgriculture-/tree/main/config
