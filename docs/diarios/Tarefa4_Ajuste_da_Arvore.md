# Diário da Tarefa 4 — Ajuste da árvore a partir do erro

**Período:** 05/10/2026 a 11/10/2026  
**Projeto:** Preditor de degradação de rede com RTT normalizado (independente da rota)

**Equipe:** WebAgriculture (Apollo Moura De Sousa, Icaro Luiz Dellalo Silva, Ieda de Oliveira, João Pedro C. de Morais, Lucas Matteus Baptista de Godoy)  
**Scrum Master da tarefa:** [a preencher pela equipe]  
**Repositório GitHub:** https://github.com/ZorahSai/Projeto-WebAgriculture-

> O rótulo e o baseline da Tarefa 2 continuam. O corte temporal continua. Esta tarefa **não troca o algoritmo**: ajusta a mesma árvore de decisão com o que a Tarefa 3 errou.
>
> Ajuste permitido: profundidade, mínimo de amostras na folha, critério (Gini ou entropia) e poda. Se entrar coluna nova, ela tem de ser outra métrica **relativa ao baseline**. País, IP, rota e RTT absoluto continuam fora.

### Contrato desta tarefa

| | Artefato | Origem / destino |
|---|---|---|
| **Entra** | Árvore da Tarefa 3, matriz e erros | `results/tarefa3/`, [`docs/relatorio_tarefa3.md`](../relatorio_tarefa3.md) |
| **Entra** | Mesmo baseline, mesmo rótulo, mesmo corte | `data/processed/` (Tarefa 2) |
| **Sai** | Árvore ajustada e tabela Tarefa 3 → Tarefa 4 | `results/tarefa4/`, [`docs/relatorio_tarefa4.md`](../relatorio_tarefa4.md) |
| **Sai** | Regras novas em português | Seção 2 abaixo |
| **Sai** | Dicionário v0.3, se nasceu coluna relativa nova | **Não nasceu.** Permanece o v0.2 |

Código: `src/ajustar_arvore.py`. Parâmetros: `config/arvore_tarefa4.json`.

**Não sai daqui:** outro tipo de modelo, mudança do teste, recálculo do baseline com o Período B.

- [x] O corte é o da Tarefa 2 (`bloco` em `dataset_rotulado_B.csv.gz`; o teste não é carregado)
- [x] Nenhuma coluna de rota entrou

---

## 1. O que o erro pediu

- [x] Citar os erros da Tarefa 3 (classe confundida, caminho longo ou curto, pico isolado virando FALHA, RISCO sumindo)
- [x] Cada mudança da árvore responde a um desses erros
- [x] Parâmetros escolhidos na validação

**Erro da Tarefa 3 → mudança na árvore:**

| Erro observado | Mudança (profundidade, folha, critério ou métrica relativa nova) |
|---|---|
| 10 FALHA da validação viraram OK. RTT atual normal (`z_robusto` negativo), mas `n5_aumento80` ≥ 2 (linha 4 do rótulo). A profundidade 6 não fechava esse caminho | `max_depth` 6 → **8**, ainda Gini, para a árvore alcançar o corte em `n5_aumento80` |
| Os mesmos 10 erros, sem árvore inchada | Entre as combinações com F1 e recall de FALHA máximos, `min_samples_leaf` **10** (19 folhas; sem isso seriam 23–24) |
| Gini vs entropia no mesmo erro | Entropia foi testada e **não zerou** os FALHA→OK (sempre restou ≥ 1). Ficou **Gini** |
| Poda: os 10 erros seriam só ruído? | Poda leve `ccp_alpha` = **0,0001** em cima da árvore já profunda: mesma F1, menos folhas. Poda com profundidade 6 devolve os 10 erros e foi descartada |
| Caminho longo estável marcado como FALHA | **Não apareceu** na validação da Tarefa 3. Nenhuma mudança por esse motivo |
| Coluna relativa nova | **Não.** `n5_aumento80` já descreve o erro |

---

## 2. Árvore ajustada

- [x] Mesmas colunas relativas, mais o que a tabela acima acrescentou (nada)
- [x] Profundidade, folhas e três regras em português
- [x] Fit só no treino (115.804 medições)

**Parâmetros finais candidatos (ainda não é o teste):** Gini; `max_depth` = 8; `min_samples_leaf` = 10; `ccp_alpha` = 0,0001; profundidade real 7; 19 folhas; semente 42.

**Regras:**

1. Se `z_robusto` ≤ 3,5 e `n5_risco` ≤ 1,5 e `perda_pct` ≤ 16,7 e `n5_aumento80` ≤ 1,5 e `n5_timeout` ≤ 2,5, então **OK** (88.757 medições do treino, 100% OK).
2. Se `z_robusto` ≤ 3,5 e `n5_risco` > 1,5 e `jitter_relativo` > 3 e `perda_pct` ≤ 16,7 e `n5_aumento80` ≤ 1,5, então **RISCO** (4.371 medições do treino, 100% RISCO).
3. Se `z_robusto` > 3,5 (ou vazio), então **FALHA** (11.959 medições do treino, 100% FALHA).

A árvore completa está em `results/tarefa4/arvore_ajustada.txt`. A Tarefa 5 parte desta árvore.

---

## 3. Comparação na validação

| | F1 macro | Recall de FALHA | Recall de RISCO |
|---|---|---|---|
| Árvore da Tarefa 3 | 0,9996 | 0,9984 | 1,0000 |
| Árvore desta tarefa | 1,0000 | 1,0000 | 1,0000 |

- [x] Se não houve ganho, dizer o que foi tentado e descartado — **houve ganho** nos 10 FALHA→OK (10 → 0). Tentativas descartadas: profundidade 6; entropia; profundidade 10 (F1 igual, mais folhas); coluna nova.
- [x] Matriz 3×3 da árvore desta tarefa, na validação

| real \ previsto | OK | RISCO | FALHA |
|---|---|---|---|
| **OK** | 35.837 | 1 | 0 |
| **RISCO** | 0 | 3.687 | 0 |
| **FALHA** | 0 | 0 | 6.317 |

**Leitura do ganho (ou da falta de ganho):**

A Tarefa 3 já reaprendia a tabela de rótulo; faltava o ramo da linha 4 (`n5_aumento80`). Subir a profundidade fecha os 10 FALHA que viravam OK, sem RTT absoluto e sem rota. O recall de FALHA vai de 0,9984 para 1,0000. Resta 1 OK→RISCO. Continua sendo a política da Tarefa 2, não falha confirmada em equipamento. Relatório: [`docs/relatorio_tarefa4.md`](../relatorio_tarefa4.md).

---

## 4. Revisão com o docente

**O que foi mostrado:** o relatório da Tarefa 4, a tabela Tarefa 3 → Tarefa 4 e a árvore em `results/tarefa4/`.  
**O que foi pedido para ajustar antes da Tarefa 5:** [a preencher depois da revisão com o docente]

---

## 5. Scrum e diário

- [ ] Board atualizado [a preencher pela equipe]

| Integrante | O que fiz nesta tarefa | Dificuldades | O que pretendo manter/ajustar |
|---|---|---|---|
| Apollo Moura De Sousa | [a preencher] | [a preencher] | [a preencher] |
| Icaro Luiz Dellalo Silva | [a preencher] | [a preencher] | [a preencher] |
| Ieda de Oliveira | [a preencher] | [a preencher] | [a preencher] |
| João Pedro C. de Morais | [a preencher] | [a preencher] | [a preencher] |
| Lucas Matteus Baptista de Godoy | Implementei o ajuste da árvore (`src/ajustar_arvore.py`, `config/arvore_tarefa4.json`, `results/tarefa4/`) a partir dos 10 FALHA→OK da Tarefa 3, preenchi o diário e o relatório, sem abrir o teste e sem coluna de rota. | Ligar cada hiperparâmetro a um erro concreto, e não só “subir a profundidade porque a F1 sobe”. Entropia e poda com profundidade 6 pareciam ajuste, mas devolviam FALHA→OK. | Manter a árvore Gini profunda o suficiente para a linha 4. A Tarefa 5 usa esta árvore no teste. O 1 OK→RISCO residual fica documentado, sem inventar feature de rota. |
