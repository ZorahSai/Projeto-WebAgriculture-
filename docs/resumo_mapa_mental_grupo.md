# Insumo para mapa mental — Projeto WebAgriculture

**Para o agente que for desenhar o mapa:** transforme este texto em um mapa mental hierárquico (nós + ramificações). Preserve as caixas “não confundir”. Não invente pastas, tarefas ou features que não estejam aqui. Público: integrantes do grupo (nível iniciante/intermediário). Idioma: português.

**Repositório:** https://github.com/ZorahSai/Projeto-WebAgriculture-  
**Clone local de referência:** `C:\Users\lucas\Projects\Projeto-WebAgriculture-`  
**Equipe:** Apollo Moura De Sousa, Icaro Luiz Dellalo Silva, Ieda de Oliveira, João Pedro C. de Morais, Lucas Matteus Baptista de Godoy  
**Disciplinas:** Redes de Computadores + Estrutura de Dados II + Análise de Sistemas (Scrum)  
**Apresentação prevista:** 10 a 12/11/2026

---

## 1. Frase-núcleo do projeto

Classificar cada medição de ping de um **fluxo** em **OK / RISCO / FALHA**, pelo desvio em relação ao **normal daquele fluxo**, não por RTT alto em milissegundos nem por país/rota.

- Um RTT de 200 ms pode ser **OK** num caminho longo e **FALHA** num caminho curto.
- Nome GitHub “WebAgriculture”: histórico do grupo. **Não é** um site de fazenda. É preditor de degradação de **rede**.

---

## 2. Conceitos-base (nós do mapa)

### Fluxo
- Identidade: `fluxo_id = probe_id|dst_addr`
- Origem: Anchor RIPE Atlas que dispara o ping (`probe_id`)
- Destino: IP da Anchor alvo
- 20 destinos × 5 origens da mesma região = 100 pares; 3 auto-pings fora → **97 fluxos**
- Rajada: 3 pings a cada 240 s

### Classes
- **OK:** nada a fazer
- **RISCO:** observar
- **FALHA:** investigar
- Errar FALHA é o erro mais caro (por isso não se usa só acurácia)

### Fonte dos dados
- RIPE Atlas, ping IPv4 público entre Anchors
- Só `GET` em medições já existentes (sem criar medição, sem gastar crédito)
- API: `https://atlas.ripe.net/api/v2`

### Dois eixos que as pessoas misturam (caixa “não confundir”)

**Eixo 1 — Períodos A e B (uso do tempo na coleta/rótulo)**  
Não são treino e teste.

| Período | Datas (UTC) | Papel |
|---|---|---|
| A | 06/09/2026 04:32 → 13/09/2026 04:32 (fim exclusivo) | Só **baseline** (ficha do fluxo). Sem classe. A árvore **não** treina em A. |
| B | 13/09/2026 04:32 → 20/09/2026 04:32 | Medições que **ganham rótulo**. Daqui saem treino/validação/teste. |

**Eixo 2 — Blocos treino / validação / teste (uso do tempo no modelo)**  
Todos **dentro de B**. Mesmas colunas, papéis diferentes.

| Bloco | Fração do tempo de B | Papel |
|---|---|---|
| treino | 50% (mais antigo) | `fit` da árvore |
| validação | 20% (meio) | escolher hiperparâmetros |
| teste | 30% (mais recente) | **fechado até a Tarefa 5** |
| embargo | 4 primeiras medições de cada fluxo em validação e teste | fora: as colunas `n5_*` olhariam o bloco anterior |

Datas do corte atual: treino até 16/09 16:32; validação até 18/09 02:08; teste até 20/09 04:32.

**“Alimentar o modelo”** não é um segundo CSV de outro tipo. É: pegar uma linha no **mesmo formato de features** e chamar `predict`. No futuro (dashboard): medição nova + ficha de A congelada.

**A e B não precisam ser dois arquivos brutos.** Um bruto com coluna `periodo` é o contrato da Tarefa 1. Depois da Tarefa 2, os papéis já estão em arquivos processados separados.

---

## 3. Lógica ponta a ponta (pipeline)

```
RIPE Atlas
  → JSON bruto intacto (gzip + meta)
  → tabela bruta (A+B, sem classe)
  → ficha por fluxo (só A)
  → dataset rotulado (só B)
  → árvore oficial (fit só no treino de B)
```

### Tarefa 1 — Problema e coleta bruta (sem rótulo)
- **Scripts:** `src/coletar_bruto.py`, `src/montar_tabela_bruta.py`, `src/relatorio_qualidade.py`
- **Config:** `config/coleta.json`
- **Sai:** `data/raw/json/`, `data/raw/medicoes_brutas.csv.gz`, `docs/dicionario_v0.1.md`, `docs/relatorio_qualidade_tarefa1.md`
- Regras: RTT ausente = vazio (nunca 0); timeout permanece; país/rota só auditoria; coleta idempotente; HTTP com retry.
- Números: 486.487 linhas; 97 fluxos; RTT mediano ~68 ms; caminhos de ~1 ms até ~318 ms.
- Ainda **não** há OK/RISCO/FALHA, mediana nem árvore.

### Tarefa 2 — Baseline + rótulo + corte
- **Script:** `src/baseline_e_rotulo.py`
- **Config:** `config/rotulagem.json`
- **Sai:** `data/processed/baseline_por_fluxo.csv`, `dataset_rotulado_B.csv.gz`, `corte_temporal.json`, `docs/dicionario_v0.2.md`, `docs/relatorio_tarefa2.md`

**Ficha (só A), por fluxo:** mediana, MAD, IQR, jitter típico, perda típica, prop. resposta.  
Piso: 1.500 RTT válidos no A. 5 fluxos para Bogotá ficaram `baseline_insuficiente` (não se inventa mediana). 92 fluxos com ficha.

**Métricas relativas (em B, com a ficha congelada):**
- `z_robusto` = (RTT − mediana) / (1,4826 × MAD)
- `aumento_pct`, `jitter_relativo`, `perda_pct`, `timeout_atual`
- Janela 5: `n5_timeout`, `n5_aumento80`, `n5_risco`

**Tabela de rótulo (para na primeira linha verdadeira):**
1. FALHA se `perda_pct` ≥ 10
2. FALHA se `n5_timeout` ≥ 3
3. FALHA se `z_robusto` ≥ 3,5 (com RTT)
4. FALHA se `n5_aumento80` ≥ 2
5. RISCO se critério moderado nesta medição **e** `n5_risco` ≥ 2
6. OK (pico isolado também é OK)

Contagem em B: OK 185.651 (80,4%) / RISCO 16.383 (7,1%) / FALHA 28.820 (12,5%).

**Limitação da regra (não é bug de código):** mudança de patamar de rota (ex. fluxo `7399 → de-mdt`) vira FALHA em massa pela linha 3. Caso “RECALIBRAR” do RFC. MAD muito pequeno também dispara fácil.

**Proibido na árvore:** país, região, IP, `probe_id`, `fluxo_id`, nome do destino, `latencia_ms`/`jitter_ms`/`mediana` absolutos, `regra`, `classe` (alvo, não feature), `bloco`.

### Tarefa 3 — Primeira árvore
- **Script:** `src/treinar_arvore.py`
- **Config:** `config/arvore.json`
- **Sai:** `results/tarefa3/` + `docs/relatorio_tarefa3.md`

**8 colunas oficiais:** `z_robusto`, `aumento_pct`, `jitter_relativo`, `perda_pct`, `timeout_atual`, `n5_timeout`, `n5_aumento80`, `n5_risco`  
**Alvo:** `classe`  
**Modelo:** CART, Gini, `random_state=42`  
**Grade:** `max_depth` 2–12; `min_samples_leaf` 1, 10, 50, 200; escolhe pela F1 macro na validação; empate próximo (≤ 0,005) fica a de **menos folhas**.  
**Fit só no treino** (115.804 linhas). Teste nem é carregado.  
Árvore escolhida: profundidade 6, 17 folhas, raiz `z_robusto ≤ 3,5`. F1 macro validação ≈ 0,9996.

**Por que F1 quase 1:** o rótulo da Tarefa 2 **é** uma regra sobre essas 8 colunas. A árvore reaprende a política, não uma falha de equipamento confirmada.

**Árvores de contraste (não são o modelo):**
- Relativas + RTT absoluto: continua usando `z_robusto`; ms não acrescentam.
- Só absolutos (`latencia_ms`, `jitter_ms`, perda, timeout): corta em ms fixos; F1 cai para ~0,51 (aprende comprimento do caminho).

### Ainda não existe
- Dashboard em tempo real (objetivo do README: ping local + simulação OK/RISCO/FALHA)
- Avaliação no **teste** (Tarefa 5)
- Preditor “12 minutos à frente” (horizonte deixado para depois; hoje é **detector da medição atual**)
- RFC do grupo preenchido no diário da Tarefa 1 (checkbox em aberto)

### Linha paralela ED2 (`etapas_anteriores/modelo_sintetico/`)
- Árvore CART **escrita à mão** + gerador sintético
- Usa latência/perda/jitter **absolutos**
- No dado real antigo, RISCO quase some — exatamente o problema que `src/` resolve com métricas relativas
- **Não** substitui a Tarefa 3

---

## 4. Organização do GitHub / pastas

```
Projeto-WebAgriculture-/
├── README.md                          ← mapa do projeto (como rodar Tarefas 1–3)
├── requirements.txt                   ← requests, pandas, numpy, scikit-learn
├── config/                            ← parâmetros FORA do código
│   ├── coleta.json                    ← períodos, destinos, sondas, API
│   ├── rotulagem.json                 ← piso, regras, corte 50/20/30, embargo
│   └── arvore.json                    ← colunas oficiais/proibidas, grade, semente 42
├── src/                               ← pipeline oficial Tarefas 1–3
│   ├── coletar_bruto.py
│   ├── montar_tabela_bruta.py
│   ├── relatorio_qualidade.py
│   ├── baseline_e_rotulo.py
│   └── treinar_arvore.py
├── data/
│   ├── raw/
│   │   ├── json/<destino>/            ← resposta da API intacta (.json.gz + .meta.json)
│   │   └── medicoes_brutas.csv.gz     ← A+B, coluna periodo, SEM classe
│   └── processed/
│       ├── baseline_por_fluxo.csv     ← ficha só de A
│       ├── dataset_rotulado_B.csv.gz  ← B rotulado + coluna bloco
│       └── corte_temporal.json
├── results/tarefa3/
│   ├── arvore_oficial.txt
│   ├── grade_validacao.csv
│   └── metricas_validacao.json
├── docs/
│   ├── dicionario_v0.1.md / v0.2.md
│   ├── relatorio_qualidade_tarefa1.md
│   ├── relatorio_tarefa2.md / relatorio_tarefa3.md
│   └── diarios/                       ← contratos e checklists das tarefas
│       ├── Tarefa1_Coleta_Bruta.md
│       ├── Tarefa2_Baseline_e_Rotulagem.md
│       └── Tarefa3_Arvore_Inicial.md
└── etapas_anteriores/                ← HISTÓRICO (não usar nas Tarefas 1–5)
    ├── modelo_sintetico/              ← ED2 (árvore na mão + sintético)
    ├── coleta_de_dados/               ← notebooks e coletas antigas
    ├── memorando_de_decisao/          ← escolha RIPE Atlas vs Kaggle
    └── Anchors.txt                    ← destinos; agora estão em config/coleta.json
```

**Como rodar (raiz do repo):**
```bash
pip install -r requirements.txt
python src/coletar_bruto.py          # pula bloco que já existe
python src/montar_tabela_bruta.py    # precisa --sobrescrever se o CSV já existe
python src/relatorio_qualidade.py
python src/baseline_e_rotulo.py      # idem --sobrescrever
python src/treinar_arvore.py         # não carrega o teste
```
A coleta já está no GitHub; na prática começa-se dos scripts de tabela/rótulo/árvore.

---

## 5. Notebook da professora vs este repo

**Arquivo:** `Arvore_e_random_forest_didatico.ipynb` (material didático, etapa 8 de ML).

O que ele ensina (método, válido para o futuro):
- Pipeline: problema → dados → features → split temporal → modelo → grade → treino → avaliação → diagnóstico → persistência
- Um arquivo `dataset_final.csv` com coluna `split` (treino/validação/teste) — **não** dois datasets de tipos diferentes
- Tirar IDs e `timestamp` de `X` (vazamento)
- `GridSearchCV` + `PredefinedSplit` + `scoring=f1_macro`
- `class_weight`, Random Forest, avaliar no **teste**, `joblib`
- 21 features de **outro** pipeline (razões p95/p99, janelas w3/w6/w12, TTL)

O que **não** deve ser copiado para as Tarefas 1–3:
- Trocar as 8 métricas relativas pelas 21 features / TTL
- Abrir o teste agora
- `refit=True` em treino+validação (o diário da 3 exige `fit` só no treino)
- Random Forest na entrega da primeira árvore
- Tratar A e B como se fossem os `split` do notebook

**Decisão já tomada na revisão:** o código das Tarefas 1–3 está coerente com os diários/RFC deste projeto. **Não mudar agora** para “ficar igual ao notebook”. O notebook entra nas etapas seguintes (comparar árvore × floresta, nota no teste).

---

## 6. O que conversamos (contexto para o grupo)

1. Pedido de tour do código; o workspace era a pasta home; GitHub CLI instalado; login device (`31C8-D77F`). O código **não** aparece no GitHub Mobile: é o código do PC para autorizar o `gh`.
2. Conta: **SuperLucas2000**. Repos próprios (ESTUDO, Exercicios-Java, GymPartner, etc.). O Web Agriculture é colaboração: **ZorahSai/Projeto-WebAgriculture-**.
3. Tour: arquitetura, fluxos 1–3, como rodar, primeira alteração sugerida (classificador mínimo / fatia do dashboard, sem mexer na coleta).
4. Cruzamento com o notebook da professora: Tarefas 1–3 OK; não reescrever o treino no estilo etapa 8.
5. Dúvida A vs B como dois datasets: **não** no bruto; **sim** nos papéis; processado já separado.
6. Dúvida “1 CSV treino e outro para alimentar o modelo”: **não**. Mesmo schema; papéis split/bloco; A não é treino.

---

## 7. Sugestão de níveis do mapa mental

1. **Raiz:** Preditor de degradação de rede (OK / RISCO / FALHA) por fluxo  
2. **Ramo Objetivo** — o que é fluxo, o que é classe, o que é proibido como definição de falha  
3. **Ramo Não confundir** — A/B vs treino/val/teste vs “alimentar o modelo” vs notebook etapa 8  
4. **Ramo Pipeline** — T1 coleta → T2 baseline/rótulo/corte → T3 árvore → (futuro) T5 teste + dashboard  
5. **Ramo GitHub** — `config` / `src` / `data/raw` / `data/processed` / `results` / `docs` / `Modelo` / histórico  
6. **Ramo Modelo oficial** — 8 features, Gini, fit no treino, contraste absoluto vs relativo  
7. **Ramo Limitações** — F1 alta porque reaprende a regra; mudança de patamar; teste fechado; dashboard inexistente  
8. **Ramo Próximos passos** — não abrir teste; não copiar 21 features; RF e GridSearchCV depois; dashboard classificando linha no formato da Tarefa 2  

Nós visuais úteis: uma seta “A → ficha congelada”; uma seta “B → dataset_rotulado → árvore”; um cadeado no bloco teste; um X vermelho em “RTT > 100 ms = falha”.
