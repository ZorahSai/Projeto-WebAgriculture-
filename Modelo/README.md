# Modelo — gerador sintético e árvore de decisão (ED2)

Os arquivos usam só a biblioteca padrão do Python, sem dependências.

| Arquivo | O que faz |
|---|---|
| `gerador_sintetico.py` | Gera um dataset sintético no formato do Contrato de Dados |
| `dataset_sintetico.csv` | Dataset gerado com os parâmetros padrão (1.500 registros, 5 IPs, semente 42) |
| `arvore_decisao.py` | Árvore de decisão implementada à mão: nós, folhas, corte por Gini, percurso recursivo e poda simples |
| `treinar_modelo.py` | Lê um CSV, separa treino/teste (70/30), treina, mostra a árvore e calcula a acurácia |

## Como executar

```bash
cd Modelo
python gerador_sintetico.py
python treinar_modelo.py
```

Opções:

- `python gerador_sintetico.py --registros 3000 --semente 7 --saida outro.csv` gera outro dataset. O script não sobrescreve um arquivo existente.
- `python treinar_modelo.py <csv> --max-profundidade 5 --min-amostras 10` treina com outro CSV e outros limites.
- `--salvar modelo.json` grava a árvore treinada, para o dashboard carregar com `arvore_decisao.de_dict`.

## Regras do gerador sintético

Cada IP passa por episódios de 5 a 20 medições seguidas, cada um num estado (OK, RISCO ou FALHA). Os estados se alternam em ordem aleatória, e cada um aparece uma vez a cada três episódios, o que deixa as classes equilibradas.

Em cada medição são simulados 10 pings:

- **Latência:** média dos RTTs que voltaram.
- **Perda:** fração dos pings perdidos.
- **Jitter:** média da variação entre RTTs consecutivos, a mesma fórmula da coleta real.

| Estado | RTT base (ms) | Variação (ms) | Chance de perder cada ping |
|---|---|---|---|
| OK | 2 a 40 | 0,5 a 5 | 0 a 2% |
| RISCO | 50 a 180 | 5 a 30 | 2 a 15% |
| FALHA | 150 a 500 | 20 a 80 | 15 a 60% |
| FALHA, fora do ar (35% dos episódios de FALHA) | — | — | 100% |

As faixas se sobrepõem de propósito, para a árvore não acertar 100%. Quando nenhum ping volta, a latência e o jitter ficam vazios, a mesma convenção do dataset real limpo.

## Como a árvore funciona

- **Construção (recursiva):** em cada nó, testa todos os cortes `atributo <= limiar` de `latencia_ms`, `perda_pacotes_pct` e `jitter_ms` e fica com o que deixa os dois lados mais puros (menor impureza de Gini). Para quando o nó é puro, quando chega à profundidade máxima (padrão 4), quando tem menos de 5 amostras ou quando nenhum corte melhora.
- **Poda:** um corte em que os dois lados viram folhas da mesma classe é trocado por uma folha só.
- **Classificação (percurso recursivo):** desce da raiz até uma folha seguindo as condições.
- **Valor vazio:** é tratado como latência "infinita", ou seja, sempre cai no lado `não` do corte.
- **Treino/teste:** divisão estratificada de 70%/30%, em que cada classe é dividida na mesma proporção.

A implementação foi conferida com o `DecisionTreeClassifier` do scikit-learn usando os mesmos parâmetros (`max_depth=4`, `min_samples_split=5`). As duas dão a mesma acurácia e o mesmo primeiro corte, nos dois datasets.

## Resultados (profundidade 4, semente 42)

| Dataset | Acurácia no teste | Referência (sempre a classe mais comum) | Acerto por classe (OK / RISCO / FALHA) |
|---|---|---|---|
| Sintético (1.500 registros) | 99,1% | 33,6% | 100% / 99,3% / 98,0% |
| Real multidestino (249.784 registros) | 93,8% | 87,9% | 99,9% / **4,0%** / 87,0% |

Árvore treinada no dataset sintético:

```
latencia_ms <= 44.235?
├── sim: → OK
└── não: latencia_ms <= 185.36?
    ├── sim: perda_pacotes_pct <= 35?
    │   ├── sim: jitter_ms <= 49.775?
    │   │   ├── sim: → RISCO
    │   │   └── não: → FALHA
    │   └── não: latencia_ms <= 125.83?
    │       ├── sim: → RISCO
    │       └── não: → FALHA
    └── não: → FALHA
```

**Por que o RISCO quase não é reconhecido no dado real:** no dataset real, `status_real` foi calculado em relação à média de latência de cada par origem→destino. Uma latência de 220 ms é normal num par e RISCO em outro. A árvore só enxerga a latência absoluta, então não consegue reproduzir esse critério. Esse é o principal ponto a tratar na Sprint 5, por exemplo treinando com o desvio da latência em relação à linha de base do par.
