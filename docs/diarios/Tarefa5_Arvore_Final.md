# Diário da Tarefa 5 — Árvore final e teste único

**Período:** 12/10/2026 a 25/10/2026  
**Projeto:** Preditor de degradação de rede com RTT normalizado (independente da rota)

**Equipe:**  
**Scrum Master da tarefa:**  
**Repositório GitHub:** https://github.com/ZorahSai/Projeto-WebAgriculture-

> A árvore que entra aqui é a da Tarefa 4. O baseline e o rótulo são os da Tarefa 2. O teste, guardado desde a Tarefa 2, é medido **uma vez**.
>
> Continua sendo uma árvore de decisão. O grupo entrega as regras, a matriz e o que a árvore faz num fluxo que ela não viu — desde que esse fluxo tenha a própria ficha de baseline, calculada só no período inicial dele.

### Contrato desta tarefa

| | Artefato | Origem / destino |
|---|---|---|
| **Entra** | Corte da Tarefa 2 e ficha de baseline | Tarefa 2 |
| **Entra** | Árvore ajustada e regras | Tarefa 4 |
| **Sai** | Teste único: matriz 3×3, F1 por classe, F1 macro | Entrega |
| **Sai** | Checagem de fluxo não visto, com baseline próprio | Entrega |
| **Sai** | Ficha da árvore (abaixo) e dicionário v0.4 igual às colunas usadas | Entrega |

Não há tarefa seguinte.

- [x] A profundidade não foi escolhida de novo olhando o teste
- [x] O baseline do teste não usou medição do próprio teste

---

## 1. Árvore que será medida

- [x] Critério, profundidade, mínimo de amostras na folha, colunas
- [x] Três regras em português, as mesmas da Tarefa 4 ou as revistas **antes** de abrir o teste
- [x] Confirmação de que país, IP, rota e RTT absoluto não estão na árvore

**Parâmetros:**  
- Critério: gini  
- max_depth: 8 (profundidade real obtida: 7)  
- min_samples_leaf: 10  
- ccp_alpha: 0,0001  
- Semente: 42  
- Folhas: 19  

**Colunas:**  
`z_robusto`, `aumento_pct`, `jitter_relativo`, `perda_pct`, `timeout_atual`, `n5_timeout`, `n5_aumento80`, `n5_risco`

**Regras:**

1. Se `z_robusto` ≤ 3,50 e `n5_risco` ≤ 1,50 e `perda_pct` ≤ 16,67 e `n5_aumento80` ≤ 1,50 e `n5_timeout` ≤ 2,50, então **OK**.
2. Se `z_robusto` ≤ 3,50 e `n5_risco` > 1,50 e `jitter_relativo` > 3,00 e `perda_pct` ≤ 16,67 e `n5_aumento80` ≤ 1,50, então **RISCO**.
3. Se `z_robusto` > 3,50, então **FALHA**.

---

## 2. Teste temporal (uma vez)

Fluxos conhecidos, período mais recente do Período B.

- [x] Matriz 3×3 com contagem, não só porcentagem
- [x] Precisão, recall e F1 de OK, RISCO e FALHA
- [x] F1 macro
- [x] Recall de FALHA e a troca RISCO ↔ FALHA comentados
- [x] Dois casos: um acerto em caminho longo estável (classe OK) e um erro relevante (dizer o fluxo e o timestamp)

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
- Recall de FALHA: 0,9997
- Troca RISCO ↔ FALHA: 0 casos (RISCO→FALHA = 0, FALHA→RISCO = 0)
- FALHA→OK: 3 casos
- OK→RISCO: 1 caso

**Casos:**

- **Acerto em caminho longo estável (OK):**  
  fluxo_id `6488|138.117.32.11`, timestamp `2026-09-18 02:25:38 UTC`, mediana do fluxo ≈ 153,3 ms, `z_robusto` ≈ 0,11. Classificado corretamente como OK.

- **Erro relevante (FALHA → OK):**  
  fluxo_id `7528|109.230.214.3`, timestamp `2026-09-19 02:05:04 UTC`, `z_robusto` ≈ 1,66, `n5_aumento80` = 2, `perda_pct` = 0. Real FALHA, prevista OK.

---

## 3. Fluxo que a árvore não viu

Separar um ou mais `fluxo_id` inteiros que não estejam no treino. A ficha desse fluxo sai só do período inicial dele (o mesmo piso: 1.500 RTT válidos; abaixo disso o fluxo não é avaliado).

- [x] O fluxo novo não aparece no treino
- [x] A mediana e o MAD não usam o trecho avaliado
- [x] Dizer se um caminho longo estável permaneceu OK e se uma degradação foi marcada RISCO ou FALHA
- [x] Se não houver fluxo sobrando com baseline suficiente, escrever isso e não forçar a conta

**Fluxos separados:**  
`6420|23.237.111.10`

**Resultado:**  
O fluxo não entrou no treino. No trecho de teste desse fluxo (752 medições) a acurácia foi 1,0000. Distribuição real e prevista idênticas: OK 505, FALHA 144, RISCO 103.  
O baseline (mediana e MAD) veio exclusivamente do Período A, sem uso do trecho avaliado. A árvore manteve a classificação correta tanto nos períodos estáveis (OK) quanto nas degradações (RISCO/FALHA).

---

## 4. O que declarar

- [x] Se a árvore só repete a tabela de rótulo, dizer isso: o rótulo foi feito com as mesmas métricas, então a árvore está aprendendo a política, não um ticket de roteador
- [x] Se o alvo for o estado 12 minutos à frente, comparar com a regra “repetir a classe atual”. Sem ganho nessa comparação, o entregável é um **detector** do estado atual, não um preditor
- [x] Limitações: baseline fixo não acompanha troca de rota; rajada curta estima mal o jitter; Anchors não são a rede do campus

**Declaração:**  
A árvore reproduz com altíssima fidelidade a política de rótulo definida na Tarefa 2 (regras híbridas baseadas em `z_robusto`, `n5_*`, perda e jitter relativo). Por isso o desempenho no teste é quase perfeito. Ela funciona como um **detector do estado atual** do fluxo, não como um preditor de estado futuro.  

Não foi feita comparação com a regra “repetir a classe atual” para horizonte de 12 minutos, pois o entregável desta tarefa é a avaliação da árvore como classificador do estado presente.  

**Limitações:**
- O baseline é fixo (Período A) e não acompanha mudança estável de rota (estado RECALIBRAR).
- A rajada curta de pings estima mal o jitter.
- Os Anchors do RIPE Atlas não representam a rede do campus.

---

## 5. Ficha da árvore

| Campo | Conteúdo |
|---|---|
| Problema | Classe OK, RISCO ou FALHA pelo desvio ao baseline do fluxo |
| Unidade | Uma medição de um `fluxo_id` no Período B |
| Baseline | Período A, mediana e MAD, piso de 1.500 RTT válidos |
| Colunas | `z_robusto`, `aumento_pct`, `jitter_relativo`, `perda_pct`, `timeout_atual`, `n5_timeout`, `n5_aumento80`, `n5_risco` |
| Árvore | Critério gini, max_depth 8 (real 7), min_samples_leaf 10, ccp_alpha 0,0001, 19 folhas, semente 42 |
| Teste (uma vez) | F1 macro 0,9999; recall de FALHA 0,9997 |
| O que ela não faz | Não classifica distância. Não opera em fluxo sem ficha. Não prediz estado futuro. |
| Como reproduzir | `requirements.txt`, scripts em `src/`, `config/arvore_tarefa4.json`, corte em `data/processed/corte_temporal.json` |

---

## 6. Scrum e diário

- [ ] Board atualizado

| Integrante | O que fiz nesta tarefa | Dificuldades | O que pretendo manter/ajustar |
|---|---|---|---|
| | | | |

---

## Rubrica — Tarefa 5 (0 a 4,0)

| Critério | Peso | Nota máxima | Nota | Observações |
|---|---|---|---|---|
| Árvore final legível | 1,0 | Regras em português, colunas relativas, parâmetros da Tarefa 4 | | |
| Teste único | 1,5 | Matriz 3×3 em contagem, F1 por classe, F1 macro, casos curto/longo; teste não escolheu a árvore | | |
| Fluxo novo com baseline próprio | 1,0 | Ficha só no período inicial; ou limitação declarada se faltou fluxo | | |
| Ficha + diário | 0,5 | Ficha preenchida e diário de todos | | |
| **Total** | **4,0** | | **___ / 4,0** | |
