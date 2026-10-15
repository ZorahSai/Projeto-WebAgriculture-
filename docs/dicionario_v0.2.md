# Dicionário de dados v0.2 — baseline, métricas relativas e classe (Tarefa 2)

Gerado por `src/baseline_e_rotulo.py` a partir de `data/raw/medicoes_brutas.csv.gz`, cujas colunas brutas estão no [dicionário v0.1](dicionario_v0.1.md). Os limiares estão em `config/rotulagem.json`.

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

### Métricas relativas (as colunas que a árvore pode ler)

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

## 4. Colunas proibidas na árvore

Estas colunas **não podem entrar na árvore oficial**:

- `pais_origem`, `regiao`, `destino_fqdn`: país e rota.
- `dst_addr`, `probe_id`, `fluxo_id`: IP e identificação do fluxo.
- `latencia_ms`, `jitter_ms`, `mediana`: RTT e jitter absolutos, que não substituem as métricas relativas.
- `regra`, `classe`, `bloco`: a classe é o alvo, e `regra` e `bloco` são auditoria.
