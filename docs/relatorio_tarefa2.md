# Relatório da Tarefa 2 — baseline, rótulo e corte

Gerado por `src/baseline_e_rotulo.py` a partir de `data/raw/medicoes_brutas.csv.gz` (Tarefa 1), com os limiares de `config/rotulagem.json`.

## 1. Inspeção do bruto

| Item | Valor |
|---|---|
| Registros brutos | 486.487 |
| Fluxos | 97 |
| Duplicatas (fluxo_id, timestamp) | 0 |
| RTT vazio | 21.349 |
| RTT gravado como 0 | 0 |
| Fluxos com timestamp nos dois períodos ao mesmo tempo | 0 (o período é definido pelo instante: A vai até 13/09/2026 04:32 UTC, exclusivo) |
| Fluxos sem medição no Período A | 0 |

## 2. Baseline por fluxo (só Período A)

Fluxos com ficha: **92**. Fluxos excluídos (menos de 1.500 RTT válidos no Período A): **5**.

| fluxo_id | destino_fqdn | n_rtt_validos_A | situacao |
|---|---|---|---|
| 6790\|38.191.196.19 | co-bog-as273103.anchors.atlas.ripe.net | 958 | baseline_insuficiente |
| 7147\|38.191.196.19 | co-bog-as273103.anchors.atlas.ripe.net | 955 | baseline_insuficiente |
| 7163\|38.191.196.19 | co-bog-as273103.anchors.atlas.ripe.net | 958 | baseline_insuficiente |
| 7586\|38.191.196.19 | co-bog-as273103.anchors.atlas.ripe.net | 958 | baseline_insuficiente |
| 7659\|38.191.196.19 | co-bog-as273103.anchors.atlas.ripe.net | 958 | baseline_insuficiente |

Exemplo auditável: o fluxo mais curto e o mais longo. As duas medianas são o "normal" de cada fluxo.

| fluxo_id | destino_fqdn | pais_origem | n_rtt_validos_A | mediana | MAD | jitter_tipico | perda_tipica | prop_resposta |
|---|---|---|---|---|---|---|---|---|
| 6904\|103.121.34.150 | nz-akl-as138398.anchors.atlas.ripe.net | NZ | 2.520 | 0,97 | 0,10 | 0,10 | 0,00 | 1,00 |
| 7020\|43.228.174.199 | jp-tch-as63806.anchors.atlas.ripe.net | IQ | 2.515 | 315,15 | 4,41 | 0,39 | 0,00 | 1,00 |

## 3 e 4. Métricas do Período B e rótulo

Classes no Período B (só fluxos com ficha):

| OK | RISCO | FALHA | Total |
|---|---|---|---|
| 185.651 (80,4%) | 16.383 (7,1%) | 28.820 (12,5%) | 230.854 |

Linha da tabela que disparou cada classe (parar na primeira verdadeira):

| regra | descrição | medições |
|---|---|---|
| 1 | FALHA: perda_pct ≥ 10 nesta medição | 1.567 |
| 2 | FALHA: n5_timeout ≥ 3 | 51 |
| 3 | FALHA: z_robusto ≥ 3,5 com RTT presente | 26.975 |
| 4 | FALHA: n5_aumento80 ≥ 2 | 227 |
| 5 | RISCO: desvio moderado nesta medição e n5_risco ≥ 2 | 16.383 |
| 6 | OK: nenhuma linha anterior | 185.651 |

Casos especiais: `jitter_relativo` infinito (jitter típico 0 e jitter atual > 0, tratado como ≥ 3) em 0 medições.

Três exemplos reais (o primeiro OK de caminho longo, com RTT alto e `z_robusto` baixo; um RISCO; uma FALHA de caminho curto ou de timeout):

| timestamp | fluxo_id | latencia_ms | z_robusto | aumento_pct | jitter_relativo | perda_pct | timeout_atual | n5_timeout | n5_aumento80 | n5_risco | regra | classe |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 15/09 07:53:48 | 7020\|43.228.174.199 | 321,67 | 1,00 | 2,07 | 0,23 | 0,00 | 0 | 0 | 0 | 0 | 6 | OK |
| 17/09 20:38:11 | 7729\|200.132.1.32 | 59,53 | 2,18 | 2,41 | 1,33 | 0,00 | 0 | 0 | 0 | 5 | 5 | RISCO |
| 15/09 07:33:16 | 7283\|109.230.214.3 | 143,57 | 1.633,98 | 383,23 | 0,83 | 0,00 | 0 | 0 | 2 | 0 | 3 | FALHA |

## 5. Corte temporal dentro do Período B

| Bloco | Início | Fim (exclusivo) |
|---|---|---|
| treino | 13/09/2026 04:32 UTC | 16/09/2026 16:32 UTC |
| validação | 16/09/2026 16:32 UTC | 18/09/2026 02:08 UTC |
| teste | 18/09/2026 02:08 UTC | 20/09/2026 04:32 UTC |

Embargo: as 4 primeiras medições de cada fluxo na validação e no teste ficam de fora, porque as colunas `n5_*` delas olham medições do bloco anterior.

| bloco | OK | RISCO | FALHA | total |
|---|---|---|---|---|
| treino | 95.643 | 7.512 | 12.649 | 115.804 |
| embargo | 580 | 39 | 117 | 736 |
| validacao | 35.838 | 3.687 | 6.317 | 45.842 |
| teste | 53.590 | 5.145 | 9.737 | 68.472 |

Nenhuma medição do Período A está em nenhum bloco.
