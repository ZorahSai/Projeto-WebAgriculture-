# Diário da Tarefa 5 — Árvore final e teste único

**Período:** 12/10/2026 a 25/10/2026  
**Projeto:** Preditor de degradação de rede com RTT normalizado (independente da rota)

**Equipe:** WebAgriculture (Apollo Moura De Sousa, Icaro Luiz Dellalo Silva, Ieda de Oliveira, João Pedro C. de Morais, Lucas Matteus Baptista de Godoy)  
**Scrum Master da tarefa:** Lucas Matteus Baptista de Godoy  
**Repositório GitHub:** https://github.com/ZorahSai/Projeto-WebAgriculture-

> A árvore que entra aqui é a da Tarefa 4. O baseline e o rótulo são os da Tarefa 2. O teste, guardado desde a Tarefa 2, é medido **uma vez**.
>
> Continua sendo uma árvore de decisão. O grupo entrega as regras, a matriz e o que a árvore faz num fluxo que ela não viu — desde que esse fluxo tenha a própria ficha de baseline, calculada só no período inicial dele.

### Contrato desta tarefa

| | Artefato | Origem / destino |
|---|---|---|
| **Entra** | Corte da Tarefa 2 e ficha de baseline | Tarefa 2 (`data/processed/corte_temporal.json`, `data/processed/baseline_por_fluxo.csv`) |
| **Entra** | Árvore ajustada e regras | Tarefa 4 (`results/tarefa4/metricas_validacao.json`, `results/tarefa4/arvore_ajustada.txt`) |
| **Sai** | Teste único: matriz 3×3, F1 por classe, F1 macro | `results/tarefa5/metricas_teste.json` |
| **Sai** | Checagem de fluxo não visto, com baseline próprio | `results/tarefa5/metricas_teste.json` (chave `fluxo_nao_visto`) |
| **Sai** | Ficha da árvore (abaixo) e dicionário v0.4 igual às colunas usadas | Este diário e `docs/dicionario_v0.4.md` |

Não há tarefa seguinte.

- [x] A profundidade não foi escolhida de novo olhando o teste (o script `src/arvore_final.py` lê os parâmetros de `results/tarefa4/metricas_validacao.json`)
- [x] O baseline do teste não usou medição do próprio teste (mediana e MAD só do Período A)

---

## 1. Árvore que será medida

- [x] Critério, profundidade, mínimo de amostras na folha, colunas
- [x] Três regras em português, as mesmas da Tarefa 4 ou as revistas **antes** de abrir o teste
- [x] Confirmação de que país, IP, rota e RTT absoluto não estão na árvore

**Parâmetros (escolhidos na validação da Tarefa 4, sem reescolha):**  
- Critério: gini  
- max_depth: 8 (profundidade real obtida: 7)  
- min_samples_leaf: 10  
- ccp_alpha: 0,0001  
- Semente: 42  
- Folhas: 19  
- Treino: 115.804 medições | Teste: 68.472 medições

**Colunas (só métricas relativas ao baseline do fluxo):**  
`z_robusto`, `aumento_pct`, `jitter_relativo`, `perda_pct`, `timeout_atual`, `n5_timeout`, `n5_aumento80`, `n5_risco`

País, região, FQDN, `dst_addr`, `probe_id`, `fluxo_id`, `latencia_ms`, `jitter_ms` e `mediana` não entram na árvore (ver §4 do `docs/dicionario_v0.4.md`).

**Regras (limiares exatos da árvore em `results/tarefa4/arvore_ajustada.txt` e `results/tarefa5/arvore_final.txt`):**

1. Se `z_robusto` ≤ 3,501 e `n5_risco` ≤ 1,5 e `perda_pct` ≤ 16,665 e `n5_aumento80` ≤ 1,5 e `n5_timeout` ≤ 2,5, então **OK**.
2. Se `z_robusto` ≤ 3,501 e `n5_risco` > 1,5 e `jitter_relativo` > 2,997 (≈ 3) e `perda_pct` ≤ 16,665 e `n5_aumento80` ≤ 1,5, então **RISCO**.
3. Se `z_robusto` > 3,501, então **FALHA**.

---

## 2. Teste temporal (uma vez)

Fluxos conhecidos, trecho mais recente do Período B (30% final, com embargo das 4 primeiras medições de cada fluxo).

- [x] Matriz 3×3 com contagem, não só porcentagem
- [x] Precisão, recall e F1 de OK, RISCO e FALHA
- [x] F1 macro
- [x] Recall de FALHA e a troca RISCO ↔ FALHA comentados
- [x] Casos: acerto OK em caminho longo, acerto OK em caminho curto e os erros relevantes (fluxo e timestamp)

**Matriz:**

|            | Prev. OK | Prev. RISCO | Prev. FALHA |
|------------|----------|-------------|-------------|
| **Real OK**     | 53.589   | 1           | 0           |
| **Real RISCO**  | 0        | 5.145       | 0           |
| **Real FALHA**  | 3        | 0           | 9.734       |

**F1 macro no teste:** 0,9999

**Por classe:**
- **OK:** Precisão 0,9999 | Recall 1,0000 | F1 1,0000 (n = 53.590)
- **RISCO:** Precisão 0,9998 | Recall 1,0000 | F1 0,9999 (n = 5.145)
- **FALHA:** Precisão 1,0000 | Recall 0,9997 | F1 0,9998 (n = 9.737)

**Comentários:**
- Recall de FALHA: 0,9997 (3 de 9.737 FALHA foram previstas OK).
- Troca RISCO ↔ FALHA: 0 casos (RISCO→FALHA = 0, FALHA→RISCO = 0).
- FALHA→OK: 3 casos. OK→RISCO: 1 caso.
- Na validação da Tarefa 4 a árvore não teve FALHA→OK; no teste apareceram 3. O erro mais grave para o detector (FALHA vista como OK) é raro, mas existe.

**Casos de acerto:**

- **Caminho longo estável (OK):** fluxo_id `7020|43.228.174.199`, timestamp `2026-09-18 08:21:53 UTC`, mediana do fluxo 315,148 ms, latência 315,179 ms, `z_robusto` 0,0047, `aumento_pct` 0,01%, `jitter_relativo` 0,36. Real OK (regra 6), previsto OK.
- **Caminho curto estável (OK):** fluxo_id `6904|103.121.34.150`, timestamp `2026-09-18 18:25:54 UTC`, mediana do fluxo 0,971 ms, latência 0,971 ms, `z_robusto` 0, `jitter_relativo` 0,55. Real OK (regra 6), previsto OK.

Os dois caminhos têm medianas que diferem mais de 300 vezes e caem na mesma folha OK, porque a árvore só olha o desvio relativo ao baseline de cada fluxo.

**Erros (todos os 4 do teste):**

| Fluxo | Timestamp (UTC) | Real → Previsto | Valores | Regra do rótulo / mediana |
|---|---|---|---|---|
| `7423\|103.40.209.7` | 2026-09-19 21:47:05 | OK → RISCO | `z_robusto` 1,99978, `aumento_pct` 7,72, `jitter_relativo` 2,61, `n5_risco` 2 | regra 6 / 90,726 ms |
| `7528\|109.230.214.3` | 2026-09-19 02:05:04 | FALHA → OK | `z_robusto` 1,659, `aumento_pct` 7,48, `jitter_relativo` 1,26, `perda_pct` 0, `n5_aumento80` 2, `n5_risco` 4 | regra 4 / 24,637 ms |
| `7586\|200.26.232.6` | 2026-09-18 13:36:17 | FALHA → OK | `z_robusto` 1,851, `perda_pct` 33,33, `n5_risco` 2 | regra 1 / 159,183 ms |
| `7659\|143.208.160.10` | 2026-09-18 17:31:04 | FALHA → OK | `z_robusto` 1,792, `jitter_relativo` vazio (NaN), `perda_pct` 66,67, `n5_risco` 2 | regra 1 / 171,546 ms |

**Por que erraram:**
- Os três FALHA→OK têm `n5_risco` > 1,5, `jitter_relativo` ≤ 2,997 e 1,620 < `z_robusto` ≤ 2,000. Eles caem no ramo das linhas 29–32 da árvore, que termina em OK testando só `aumento_pct` ≤ 29,506. Esse ramo **não testa** `perda_pct` nem `n5_aumento80`. No treino quase não havia FALHA nessa região, então a árvore não abriu o corte ali.
  - `7528` virou FALHA pela regra 4 (`n5_aumento80` = 2), que esse ramo não olha.
  - `7586` e `7659` viraram FALHA pela regra 1 (`perda_pct` ≥ 10), que esse ramo também não olha.
- O OK→RISCO de `7423` tem `z_robusto` 1,99978, colado no corte de 2,000. Um centésimo acima e ele caía no ramo z > 2,000, onde a folha é RISCO; abaixo, cai na região onde a árvore já está decidindo entre OK e RISCO pelo `aumento_pct`. É um erro de borda, não de lógica.

---

## 3. Fluxo que a árvore não viu

Separar um ou mais `fluxo_id` inteiros que não estejam no treino. A ficha desse fluxo sai só do período inicial dele (o mesmo piso: 1.500 RTT válidos; abaixo disso o fluxo não é avaliado).

- [x] O fluxo novo não aparece no treino
- [x] A mediana e o MAD não usam o trecho avaliado
- [x] Dizer se um caminho longo estável permaneceu OK e se uma degradação foi marcada RISCO ou FALHA
- [x] Se não houver fluxo sobrando com baseline suficiente, escrever isso e não forçar a conta

**Fluxo separado:**  
`6420|23.237.111.10`

**Ficha (só Período A):** 2.519 RTT válidos (acima do piso de 1.500), mediana 55,713 ms, MAD 0,135 ms. O script confere o piso antes de avaliar.

**Resultado:**  
A árvore foi treinada de novo sem nenhuma medição desse fluxo (confirmado no JSON: `fora_do_treino = true`). No trecho de teste do fluxo (752 medições) a acurácia foi 1,0000. Distribuição real e prevista idênticas: OK 505, FALHA 144, RISCO 103.  
O caminho estável permaneceu OK e as degradações foram marcadas RISCO ou FALHA como no rótulo. O baseline (mediana e MAD) veio só do Período A, sem uso do trecho avaliado.

---

## 4. O que declarar

- [x] Se a árvore só repete a tabela de rótulo, dizer isso: o rótulo foi feito com as mesmas métricas, então a árvore está aprendendo a política, não um ticket de roteador
- [x] Se o alvo for o estado 12 minutos à frente, comparar com a regra “repetir a classe atual”. Sem ganho nessa comparação, o entregável é um **detector** do estado atual, não um preditor
- [x] Limitações: baseline fixo não acompanha troca de rota; rajada curta estima mal o jitter; Anchors não são a rede do campus

**Declaração:**  
A árvore reproduz com altíssima fidelidade a política de rótulo da Tarefa 2 (regras híbridas sobre `z_robusto`, `n5_*`, perda e jitter relativo). O rótulo foi feito com as mesmas colunas que a árvore usa, por isso o desempenho no teste é quase perfeito: ela aprendeu a política, não um evento real de rede.

O alvo do projeto é o estado **atual** da medição, não o estado 12 minutos à frente, como definido na RFC (`docs/RFC_Preditor_Degradacao_Rede.md`). Por isso a comparação com “repetir a classe atual” não se aplica, e o entregável é um **detector** do estado atual. Prever o estado futuro fica como trabalho futuro.

**Limitações:**
- O baseline é fixo (Período A) e não acompanha mudança estável de rota (estado RECALIBRAR).
- A rajada curta de pings estima mal o jitter.
- Os Anchors do RIPE Atlas não representam a rede do campus.
- O ramo OK das linhas 29–32 da árvore não testa perda nem `n5_aumento80`, o que explica os 3 FALHA→OK do teste.

---

## 5. Ficha da árvore

| Campo | Conteúdo |
|---|---|
| Problema | Classe OK, RISCO ou FALHA pelo desvio ao baseline do fluxo |
| Unidade | Uma medição de um `fluxo_id` (`probe\|dst`) no Período B |
| Baseline | Período A (06/09/2026 04:32 a 13/09/2026 04:32 UTC), mediana e MAD, piso de 1.500 RTT válidos |
| Colunas | `z_robusto`, `aumento_pct`, `jitter_relativo`, `perda_pct`, `timeout_atual`, `n5_timeout`, `n5_aumento80`, `n5_risco` (ver `docs/dicionario_v0.4.md`) |
| Árvore | Critério gini, max_depth 8 (real 7), min_samples_leaf 10, ccp_alpha 0,0001, 19 folhas, semente 42 |
| Teste (uma vez) | F1 macro 0,9999; recall de FALHA 0,9997; 4 erros em 68.472 medições |
| O que ela não faz | Não classifica distância. Não opera em fluxo sem ficha. Não prediz estado futuro. |
| Como reproduzir | `pip install -r requirements.txt` e `python src/arvore_final.py` na raiz. Parâmetros lidos de `results/tarefa4/metricas_validacao.json`; corte em `data/processed/corte_temporal.json`; saídas em `results/tarefa5/` |

---

## 6. Scrum e diário

- [ ] Board atualizado [a preencher pela equipe]

| Integrante | O que fiz nesta tarefa | Dificuldades | O que pretendo manter/ajustar |
|---|---|---|---|
| Apollo Moura De Sousa | | | |
| Icaro Luiz Dellalo Silva | | | |
| Ieda de Oliveira | | | |
| João Pedro C. de Morais | | | |
| Lucas Matteus Baptista de Godoy | | | |

---

## Rubrica — Tarefa 5 (0 a 4,0)

| Critério | Peso | Nota máxima | Nota | Observações |
|---|---|---|---|---|
| Árvore final legível | 1,0 | Regras em português, colunas relativas, parâmetros da Tarefa 4 | | |
| Teste único | 1,5 | Matriz 3×3 em contagem, F1 por classe, F1 macro, casos curto/longo; teste não escolheu a árvore | | |
| Fluxo novo com baseline próprio | 1,0 | Ficha só no período inicial; ou limitação declarada se faltou fluxo | | |
| Ficha + diário | 0,5 | Ficha preenchida e diário de todos | | |
| **Total** | **4,0** | | **___ / 4,0** | |
