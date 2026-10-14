# Projeto-WebAgriculture-
PROJETO  – PREDITOR DE FALHA/RISCO EM DISPOSITIVOS DE REDE (com modelo de predição em árvore)
Visão Geral:
Projeto integrador entre Redes de Computadores, Estrutura de Dados II e Análise de Sistemas, desenvolvido com a
metodologia Scrum, com as três disciplinas trabalhando em paralelo através de um contrato de dados definido no início
do projeto. Início: semana de 17/08/2026. Apresentação: 10 a 12/11/2026. A disciplina de Redes gera um arquivo de
log com métricas reais de monitoramento de dispositivos, usado para treinar uma árvore de decisão. A disciplina de
Estrutura de Dados II constrói o modelo e um dashboard em tempo real que classifica dispositivos ao vivo, combinando
monitoramento real (ping) com um modo de simulação de eventos para garantir a demonstração de todas as classes
(OK, RISCO, FALHA). E Análise de Sistemas prepara e organiza o projeto quanto aos seus requisitos mínimos.

Objetivo:
Desenvolver, de forma iterativa e incremental via Scrum, uma aplicação que treine uma árvore de decisão a partir de
um log histórico de rede e disponibilize um dashboard capaz de classificar dispositivos em tempo real, monitorando a
rede local e permitindo injetar eventos simulados sob demanda

## Dataset oficial

**`Coleta de Dados/PROCESSADO/dataset_pares_multidestino_limpo.csv`** é a base usada para treinar a árvore de decisão.

- Fonte: API pública do RIPE Atlas, com medições contínuas de ping entre Anchors (decisão registrada no memorando de decisão).
- Janela: 03/10/2026 22:06 UTC a 10/10/2026 22:06 UTC (7 dias), com uma medição a cada 240 s por par.
- Cobertura: 20 Anchors de destino em 7 países (BR, US, CO, DE, JP, NZ, FI), com 5 origens da mesma região por destino. São 100 pares e 249.784 registros.
- Classes (`status_real`): OK 87,9% · RISCO 5,4% · FALHA 6,7%, calculadas em relação à linha de base de cada par.

| Coluna | Descrição |
|---|---|
| `timestamp` | Instante da medição (UTC) |
| `par_id` | Identificador do par: `<prb_id de origem>-><Anchor de destino>` |
| `destino_fqdn`, `regiao_destino` | Anchor de destino e sua região |
| `prb_id`, `pais_origem`, `ip` | Sonda (Anchor) de origem, país e endereço IPv4 |
| `latencia_ms` | RTT médio do ping. Fica vazio quando todos os pacotes se perdem |
| `perda_pacotes_pct` | Percentual de pacotes perdidos |
| `jitter_ms` | Média da variação entre RTTs consecutivos. Fica vazio quando todos os pacotes se perdem |
| `status_real` | Rótulo: `OK`, `RISCO` ou `FALHA` |

A Anchor `co-bog-as273103` (Bogotá) ficou fora do ar durante toda a janela. Seus registros foram mantidos como `FALHA` e respondem por cerca de 75% dessa classe. As decisões de limpeza estão na Seção 8 de `coleta_multidestino.ipynb`.

## Estrutura do repositório

```
├── 1 - Template_Memorando_de_Decisao.md   Memorando: escolha da fonte de dados (RIPE Atlas x dataset do Kaggle)
├── memorando-de-decisao/                  Testes das opções A e B, recomendação e riscos
├── Anchors.txt                            Anchors de destino escolhidas pela equipe
└── Coleta de Dados/
    ├── Coleta_de_dados.ipynb              Entrega 1: coleta one-off das medições 210957734 e 210958049
    ├── passo_a_passo_fluxo.ipynb          Tutorial: como achar Anchor de destino, medição e sondas de origem
    ├── coleta_destino_unico.ipynb         Coleta contínua de 20 pares para um único destino (BH)
    ├── coleta_multidestino.ipynb          Coleta contínua de 100 pares para 20 destinos (gera o dataset oficial)
    ├── limpar_dataset_multidestino.py     Script que gera o dataset limpo a partir da cópia do .rar
    ├── RAW/                               Saídas brutas das coletas
    │   ├── ID1_*, ID2_*                       Coleta one-off (JSON, tabela e metadados)
    │   ├── dataset_pares_contrato.csv         Saída de coleta_destino_unico.ipynb
    │   └── dataset_pares_multidestino.rar     Saída de coleta_multidestino.ipynb (sem limpeza)
    └── PROCESSADO/
        └── dataset_pares_multidestino_limpo.csv   Dataset oficial
```

Os JSONs brutos de cada destino da coleta multidestino e o `pares_selecionados.json` ficaram no Google Drive (`MyDrive/ripe_atlas/raw/`). A Seção 10 de `coleta_multidestino.ipynb` explica como refazer a coleta na mesma janela.

## Como executar

Os notebooks rodam no Google Colab, que salva os arquivos no Drive, ou localmente, salvando em `./ripe_atlas/`. Dependências: `pandas`, `numpy` e `requests`. As consultas à API do RIPE Atlas são públicas e não exigem chave.

Para gerar o dataset limpo a partir da cópia do `.rar`, extraia `dataset_pares_multidestino.csv` e rode:

```bash
python "Coleta de Dados/limpar_dataset_multidestino.py" caminho/para/dataset_pares_multidestino.csv
```

O script não sobrescreve um arquivo de saída que já exista.
