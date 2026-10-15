# Diário da Tarefa 2 — Baseline do fluxo e rotulagem OK, RISCO, FALHA

**Período:** 18/09/2026 a 30/09/2026  
**Projeto:** Preditor de degradação de rede com RTT normalizado (independente da rota)

**Equipe:** WebAgriculture (Apollo Moura De Sousa, Icaro Luiz Dellalo Silva, Ieda de Oliveira, João Pedro C. de Morais, Lucas Matteus Baptista de Godoy)  
**Scrum Master da tarefa:** [a preencher pela equipe]  
**Repositório GitHub:** https://github.com/ZorahSai/Projeto-WebAgriculture-

### Contrato desta tarefa

| | Artefato | Onde está |
|---|---|---|
| **Entra** | `data/raw/` e dicionário v0.1 | `data/raw/medicoes_brutas.csv.gz`, [`docs/dicionario_v0.1.md`](../dicionario_v0.1.md) |
| **Sai** | `baseline_por_fluxo.csv` | `data/processed/baseline_por_fluxo.csv` |
| **Sai** | Dataset rotulado do Período B | `data/processed/dataset_rotulado_B.csv.gz` |
| **Sai** | Recorte temporal dentro de B | `data/processed/corte_temporal.json` (coluna `bloco` do dataset) |
| **Sai** | Dicionário v0.2 | [`docs/dicionario_v0.2.md`](../dicionario_v0.2.md) |

Código: `src/baseline_e_rotulo.py`. Limiares em `config/rotulagem.json`. Relatório completo: [`docs/relatorio_tarefa2.md`](../relatorio_tarefa2.md).

- [x] O código lê o bruto da Tarefa 1 (`data/raw/medicoes_brutas.csv.gz`), sem trocar a coleta. O trabalho foi feito em script Python, como no repositório de exemplo da professora, e não em notebook.

---

## 1. Inspeção do bruto (ainda sem rótulo)

`data/raw/` permanece intocado: o script só lê a tabela bruta e grava as saídas em `data/processed/`.

- [x] **Linhas, fluxos, duplicatas e RTT vazio:** 486.487 linhas, 97 fluxos, 0 duplicatas e 21.349 RTT vazios.
- [x] **Nenhum RTT ausente foi gravado como 0:** são 0 RTT iguais a 0.
- [x] **O Período A e o Período B não compartilham timestamp do mesmo fluxo:** o período é definido pelo instante. A termina em 13/09/2026 04:32 UTC (exclusivo) e B começa nesse mesmo instante.

**N bruto:** 486.487  
**N de fluxos:** 97  
**Evidências:** seção 1 de [`docs/relatorio_tarefa2.md`](../relatorio_tarefa2.md).

## 2. Como obter o baseline

Uma ficha por `fluxo_id`, calculada **só com o Período A**. Os timeouts ficam fora da mediana e do MAD, e o Período B não entra na conta.

- [x] **Ficha conferida num fluxo curto e num fluxo longo:**

| Fluxo | Destino (origem) | RTT válidos no A | mediana | MAD | jitter típico | perda típica | prop. resposta |
|---|---|---|---|---|---|---|---|
| `6904\|103.121.34.150` (curto) | nz-akl (NZ) | 2.520 | 0,97 ms | 0,10 ms | 0,10 ms | 0% | 1,00 |
| `7020\|43.228.174.199` (longo) | jp-tch (IQ) | 2.515 | 315,15 ms | 4,41 ms | 0,39 ms | 0% | 1,00 |

As duas medianas são o "normal" de cada fluxo, embora uma seja 300 vezes maior que a outra.

- [x] **Fluxos excluídos e o motivo:** todos tiveram menos de 1.500 RTT válidos no Período A.

| Fluxo | Destino | RTT válidos no A | Situação |
|---|---|---|---|
| `6790\|38.191.196.19` | co-bog-as273103 | 958 | baseline_insuficiente |
| `7147\|38.191.196.19` | co-bog-as273103 | 955 | baseline_insuficiente |
| `7163\|38.191.196.19` | co-bog-as273103 | 958 | baseline_insuficiente |
| `7586\|38.191.196.19` | co-bog-as273103 | 958 | baseline_insuficiente |
| `7659\|38.191.196.19` | co-bog-as273103 | 958 | baseline_insuficiente |

**Fluxos com ficha:** 92  
**Fluxos excluídos:** 5, todos para a Anchor de Bogotá, que respondeu pouco no Período A. Não foi inventada mediana para eles.  
**Exemplo auditável:** fluxo curto `6904 → nz-akl`, mediana de 0,97 ms; fluxo longo `7020 → jp-tch`, mediana de 315,15 ms.

## 3. Métricas de cada medição do Período B

Calculadas com a ficha congelada de cada `fluxo_id`, com as fórmulas e os casos especiais da Tarefa 2 (ver [`docs/dicionario_v0.2.md`](../dicionario_v0.2.md)):
- `z_robusto`, `aumento_pct`, `jitter_relativo`, `perda_pct` e `timeout_atual`.
- `n5_timeout`, `n5_aumento80` e `n5_risco`, contados nas últimas 5 medições do fluxo, incluindo a atual.

Decisões registradas:
- **RTT ausente:** `z_robusto` e `aumento_pct` ficam vazios, e `timeout_atual` = 1.
- **MAD = 0:** os casos foram tratados, mas nenhum fluxo com ficha teve MAD = 0.
- **Jitter típico = 0:** nenhuma medição caiu no caso de jitter típico 0 com jitter atual maior que 0.
- **Janelas `n5_*`:** usam só medições do Período B. Nas 4 primeiras medições de cada fluxo, a janela tem menos de 5 medições.

## 4. Tabela de rotulagem — parar na primeira linha verdadeira

Contagem por linha da tabela que disparou:

| Ordem | Classe | Medições |
|---|---|---|
| 1 | FALHA (`perda_pct` ≥ 10) | 1.567 |
| 2 | FALHA (`n5_timeout` ≥ 3) | 51 |
| 3 | FALHA (`z_robusto` ≥ 3,5) | 26.975 |
| 4 | FALHA (`n5_aumento80` ≥ 2) | 227 |
| 5 | RISCO | 16.383 |
| 6 | OK | 185.651 |

- [x] **Três exemplos auditáveis**, com linhas reais do Período B:

| Caso | Timestamp (UTC) | Fluxo | Mediana do fluxo | RTT | `z_robusto` | `aumento_pct` | `jitter_relativo` | perda | `n5_risco` | Linha que disparou | Classe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| OK de caminho longo | 15/09 07:53:48 | `7020\|43.228.174.199` (IQ → jp-tch) | 315,15 ms | 321,67 ms | 1,00 | 2,07 | 0,23 | 0% | 0 | 6 | **OK** |
| RISCO | 17/09 20:38:11 | `7729\|200.132.1.32` (AR → br-poa) | 58,14 ms | 59,53 ms | 2,18 | 2,41 | 1,33 | 0% | 5 | 5 | **RISCO** |
| FALHA de caminho curto | 15/09 07:33:16 | `7283\|109.230.214.3` (HN → us-mia) | 29,71 ms | 143,57 ms | 1.633,98 | 383,23 | 0,83 | 0% | 0 | 3 | **FALHA** |

Leitura dos três casos:
- **OK de caminho longo:** 321 ms seria FALHA numa regra absoluta, mas está a só 1 desvio robusto do normal desse fluxo.
- **RISCO:** `z_robusto` entre 2 e 3,5 nesta medição, e as 5 últimas medições cumprem o critério de risco.
- **FALHA de caminho curto:** o RTT quase quintuplicou em relação ao normal do fluxo.

- [x] **Contagem no Período B:** OK 185.651 (80,4%), RISCO 16.383 (7,1%) e FALHA 28.820 (12,5%), num total de 230.854.
- [x] **A classe não foi definida por "RTT > 100 ms" nem pelo nome da rota:** a tabela só usa métricas relativas à ficha do fluxo.
- [x] **O Período A não foi rotulado.**
- [x] **O dicionário v0.2 lista as colunas proibidas na árvore:** país, região, IP, `probe_id`, `fluxo_id`, nome do destino e RTT ou jitter absolutos.

**Contagem OK / RISCO / FALHA:** 185.651 / 16.383 / 28.820  
**Evidências:** as três linhas da tabela acima e a seção 3 de [`docs/relatorio_tarefa2.md`](../relatorio_tarefa2.md).

**Observação para as tarefas seguintes (limitação da regra, não erro de código):** a linha 3 (`z_robusto` ≥ 3,5) dispara 94% das FALHAs. Em dois tipos de fluxo isso marca FALHA sem degradação real:
- **Mudança de patamar.** No fluxo `7399|91.198.196.228` (LU → de-mdt), a mediana passou de 7,2 ms no Período A para 13,1 ms no Período B, estável, sem perda e com jitter normal. As 2.495 medições do Período B saíram FALHA. É o caso RECALIBRAR (mudança de rota) da seção 8.5 do RFC.
- **MAD muito pequeno.** No fluxo `7049|170.238.235.214` (VE → br-for), o MAD é 0,09 ms, e um aumento de cerca de 1 ms já passa de 3,5 desvios.

## 5. Recorte para a árvore (ainda sem treinar)

O recorte é feito dentro do Período B, com as mesmas datas para todos os fluxos e em ordem de tempo:

- [x] **Ordem dos blocos:** o treino é o trecho mais antigo, a validação o do meio e o teste o mais recente.
- [x] **Proporção:** 50% / 20% / 30% do tempo. Todos os blocos ficaram com RISCO, então a proporção não precisou ser ajustada.
- [x] **Nenhum registro do Período A no treino.**
- [x] **Corte com data e N de cada bloco** (tabela abaixo).

Também usamos um **embargo**: as 4 primeiras medições de cada fluxo na validação e no teste (736 linhas) ficam fora dos blocos. As colunas `n5_*` delas olham medições do bloco anterior. O RFC (seção 9) pede essa folga entre os blocos.

| Bloco | Início (UTC) | Fim (UTC, exclusivo) | N | OK | RISCO | FALHA |
|---|---|---|---|---|---|---|
| treino | 13/09/2026 04:32 | 16/09/2026 16:32 | 115.804 | 95.643 | 7.512 | 12.649 |
| validação | 16/09/2026 16:32 | 18/09/2026 02:08 | 45.842 | 35.838 | 3.687 | 6.317 |
| teste | 18/09/2026 02:08 | 20/09/2026 04:32 | 68.472 | 53.590 | 5.145 | 9.737 |
| embargo | — | — | 736 | 580 | 39 | 117 |

**Corte (datas e N de treino / validação / teste):** 16/09 16:32 e 18/09 02:08 UTC; N de 115.804 / 45.842 / 68.472.

## 6. Scrum e diário

- [ ] Board atualizado [a preencher pela equipe]

**Link do board:** [a preencher pela equipe]

| Integrante | O que fiz nesta tarefa | Dificuldades | O que pretendo manter/ajustar |
|---|---|---|---|
| Apollo Moura De Sousa | [a preencher] | [a preencher] | [a preencher] |
| Icaro Luiz Dellalo Silva | [a preencher] | [a preencher] | [a preencher] |
| Ieda de Oliveira | [a preencher] | [a preencher] | [a preencher] |
| João Pedro C. de Morais | [a preencher] | [a preencher] | [a preencher] |
| Lucas Matteus Baptista de Godoy | [a preencher] | [a preencher] | [a preencher] |
