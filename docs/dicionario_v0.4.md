# Dicionário de dados v0.4 — colunas da árvore final (Tarefa 5)

Mesmas colunas do [dicionário v0.2](dicionario_v0.2.md), gerado por `src/baseline_e_rotulo.py` a partir de `data/raw/medicoes_brutas.csv.gz` (colunas brutas no [dicionário v0.1](dicionario_v0.1.md)). Os limiares estão em `config/rotulagem.json`.

## O que mudou desde a v0.2

- Nenhuma coluna nova. Baseline, rótulo e corte são os da Tarefa 2.
- A árvore final lê exatamente as 8 métricas relativas da seção 2: `z_robusto`, `aumento_pct`, `jitter_relativo`, `perda_pct`, `timeout_atual`, `n5_timeout`, `n5_aumento80`, `n5_risco`. O alvo é `classe`.
- As colunas proibidas (seção 4) não mudaram e nenhuma delas entra na árvore.
- A árvore é treinada por `src/arvore_final.py` com os parâmetros escolhidos na validação da Tarefa 4 e lidos de `results/tarefa4/metricas_validacao.json` (gini, max_depth 8, min_samples_leaf 10, ccp_alpha 0,0001, semente 42). O teste é medido uma vez.

## 1. Ficha de baseline — `data/processed/baseline_por_fluxo.csv`

Uma linha por `fluxo_id`, calculada **só com o Período A** (06/09/2026 04:32 a 13/09/2026 04:32 UTC) e depois congelada. O Período B não entra na conta.

| Coluna | Fórmula, só Período A |
|---|---|
| `fluxo_id`, `probe_id`, `dst_addr` | Identificação do fluxo |
| `destino_fqdn`, `pais_origem` | Só auditoria |
| `n_medicoes_A` | Medições do fluxo no Período A |
| `n_rtt_validos_A` | Medições com RTT presente |
| `mediana` | Mediana dos RTT válidos (ms) |
| `MAD` | mediana(\|RTT − mediana\|) dos RTT válidos (ms) |
| `IQR` | P75 − P25 dos RTT válidos (ms). Só é usado quando MAD = 0 |
| `jitter_tipico` | Mediana do jitter nas medições em que o jitter existe (ms) |
| `perda_tipica` | Mediana de `perda_pct`, inclusive timeout (%) |
| `prop_resposta` | `n_rtt_validos_A / n_medicoes_A` |
| `situacao` | `ok`, ou `baseline_insuficiente` quando há menos de 1.500 RTT válidos. Fluxo insuficiente não recebe classe |

Timeouts ficam fora da mediana e do MAD, mas continuam no dataset como evento.

Na checagem de fluxo não visto da Tarefa 5, o fluxo separado usa esta mesma ficha (Período A) e só é avaliado se tiver o piso de 1.500 RTT válidos.

## 2. Dataset rotulado — `data/processed/dataset_rotulado_B.csv.gz`

Uma linha por medição do **Período B**, só de fluxos com ficha `ok`. O Período A não é rotulado.

### Identificação e auditoria (fora da árvore)

| Coluna | Definição |
|---|---|
| `timestamp` | Instante da medição, UTC |
| `fluxo_id`, `probe_id`, `dst_addr` | Identificação do fluxo |
| `destino_fqdn`, `regiao`, `pais_origem` | Auditoria de diversidade |
| `latencia_ms`, `jitter_ms` | Valores absolutos da medição (ms), mantidos para auditoria e para a árvore de contraste |
| `mediana` | Mediana do baseline do fluxo (ms), copiada da ficha para auditoria |

### Métricas relativas (as colunas que a árvore final lê)

| Coluna | Fórmula | Vazio quando |
|---|---|---|
| `z_robusto` | (RTT atual − mediana) / (1,4826 × MAD). Se MAD = 0 e RTT = mediana: 0. Se MAD = 0 e RTT ≠ mediana: denominador = max(IQR / 1,349, 1 ms) | não há RTT |
| `aumento_pct` | (RTT atual − mediana) / mediana × 100 | não há RTT |
| `jitter_relativo` | jitter atual / `jitter_tipico`. Se os dois são 0: 1. Se o típico é 0 e o atual é maior: infinito, tratado como ≥ 3 | jitter atual vazio (o critério de jitter não dispara) |
| `perda_pct` | (enviados − recebidos) / enviados × 100 | nunca |
| `timeout_atual` | 1 se não há RTT ou `perda_pct` = 100; senão 0 | nunca |
| `n5_timeout` | Timeouts nas últimas 5 medições do fluxo, incluindo a atual (0 a 5) | nunca |
| `n5_aumento80` | Quantas das últimas 5 têm `aumento_pct` > 80 | nunca |
| `n5_risco` | Quantas das últimas 5 cumprem o critério da linha 5 da tabela de rótulo | nunca |

As janelas de 5 medições só usam o Período B. Nas 4 primeiras medições de cada fluxo, a janela tem menos de 5 medições.

### Classe

| Coluna | Definição |
|---|---|
| `regra` | Linha da tabela de rótulo que disparou (1 a 6), para auditoria |
| `classe` | `OK`, `RISCO` ou `FALHA`. É o **alvo** da árvore, nunca uma coluna de entrada |
| `bloco` | `treino`, `validacao`, `teste` ou `embargo` (corte temporal, seção 3) |

Tabela de rótulo: para na primeira linha verdadeira.

| Ordem | Classe | Condição |
|---|---|---|
| 1 | FALHA | `perda_pct` ≥ 10 nesta medição |
| 2 | FALHA | `n5_timeout` ≥ 3 |
| 3 | FALHA | `z_robusto` ≥ 3,5 nesta medição, com RTT presente |
| 4 | FALHA | `n5_aumento80` ≥ 2 |
| 5 | RISCO | nesta medição, pelo menos um destes: 2 ≤ `z_robusto` < 3,5, ou 30 ≤ `aumento_pct` ≤ 80, ou `jitter_relativo` ≥ 3; e `n5_risco` ≥ 2 |
| 6 | OK | nenhuma linha anterior. Pico isolado também é OK |

## 3. Corte temporal — `data/processed/corte_temporal.json`

Dentro do Período B, em ordem de tempo e com as mesmas datas para todos os fluxos: o treino é o trecho mais antigo (50%), a validação o do meio (20%) e o teste o mais recente (30%). As datas e o N de cada bloco estão no arquivo e em `docs/relatorio_tarefa2.md`.

As 4 primeiras medições de cada fluxo na validação e no teste ficam em `embargo`, fora dos dois blocos, porque as colunas `n5_*` delas olham medições do bloco anterior.

Na Tarefa 5 a árvore final é treinada só no bloco `treino` e medida uma vez no bloco `teste`.

## 4. Colunas proibidas na árvore

Estas colunas **não podem entrar na árvore oficial**:

- `pais_origem`, `regiao`, `destino_fqdn`: país e rota.
- `dst_addr`, `probe_id`, `fluxo_id`: IP e identificação do fluxo.
- `latencia_ms`, `jitter_ms`, `mediana`: RTT e jitter absolutos, que não substituem as métricas relativas.
- `regra`, `classe`, `bloco`: a classe é o alvo, e `regra` e `bloco` são auditoria.

## 5. Saídas da Tarefa 5 — `results/tarefa5/`

Geradas por `python src/arvore_final.py`.

### `arvore_final.txt`

Regras da árvore final em texto (`export_text` do scikit-learn), com os nomes das 8 colunas relativas.

### `metricas_teste.json`

| Chave | Conteúdo |
|---|---|
| `parametros` | `criterion`, `max_depth`, `min_samples_leaf`, `ccp_alpha`, `random_state`, lidos da Tarefa 4 |
| `colunas` | As 8 métricas relativas usadas |
| `profundidade_real`, `folhas` | Profundidade obtida e número de folhas da árvore treinada |
| `n_treino`, `n_teste` | Linhas nos blocos `treino` e `teste` |
| `teste` | `f1_macro`, `acuracia`, `por_classe` (`precisao`, `recall`, `f1`, `suporte` de OK, RISCO e FALHA) e `matriz` 3×3 em contagem (linhas = real, colunas = previsto, ordem OK, RISCO, FALHA) |
| `casos` | `longo_ok` e `curto_ok` (acerto OK no fluxo de maior e de menor mediana) e `erros` (todas as medições de teste classificadas errado), cada um com `fluxo_id`, `timestamp`, `mediana_ms`, `latencia_ms`, classe real e prevista, `regra_rotulo` e as 8 colunas |
| `fluxo_nao_visto` | `fluxo_id`, `avaliado`, `n_rtt_validos_A`, `mediana_A`, `MAD_A`, `fora_do_treino`, `n_teste`, `reais`, `previstos` e `metricas` (mesmo formato de `teste`). Quando não é avaliado, traz `motivo` |

`mediana_ms` e `latencia_ms` aparecem nos casos só para auditoria; a árvore não as lê.
