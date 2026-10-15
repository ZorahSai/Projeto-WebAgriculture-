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

## Preditor de degradação com RTT normalizado (Tarefas 1 a 3)

A versão atual do projeto segue as Tarefas 1, 2 e 3 e o RFC "Preditor de degradação de rede com RTT normalizado". Cada medição de ping é classificada como **OK**, **RISCO** ou **FALHA** pelo desvio em relação ao normal **do próprio fluxo**, e não por um limite fixo de RTT. Um RTT alto, sozinho, não indica falha.

- **Fonte:** medições públicas de ping IPv4 entre Anchors do RIPE Atlas, só com `GET`, sem criar medição nem gastar crédito.
- **Fluxos:** `fluxo_id = probe_id|dst_addr`. São 20 destinos com 5 origens da mesma região, num total de 100 pares. Três pares são auto-ping e ficam de fora, o que deixa 97 fluxos. Os RTTs medianos vão de cerca de 1 ms a 318 ms, ou seja, há caminhos curtos e longos.
- **Período A** (só baseline): 06/09/2026 04:32 a 13/09/2026 04:32 UTC.
- **Período B** (rotulado): 13/09/2026 04:32 a 20/09/2026 04:32 UTC.

| Etapa | Script | Saída | Relatório |
|---|---|---|---|
| Tarefa 1: coleta bruta, sem rótulo | `src/coletar_bruto.py`, `src/montar_tabela_bruta.py`, `src/relatorio_qualidade.py` | `data/raw/json/` (respostas da API, intactas) e `data/raw/medicoes_brutas.csv.gz` | [`docs/relatorio_qualidade_tarefa1.md`](docs/relatorio_qualidade_tarefa1.md), [`docs/dicionario_v0.1.md`](docs/dicionario_v0.1.md) |
| Tarefa 2: baseline, rótulo e corte | `src/baseline_e_rotulo.py` | `data/processed/baseline_por_fluxo.csv`, `dataset_rotulado_B.csv.gz`, `corte_temporal.json` | [`docs/relatorio_tarefa2.md`](docs/relatorio_tarefa2.md), [`docs/dicionario_v0.2.md`](docs/dicionario_v0.2.md) |
| Tarefa 3: primeira árvore e árvore de contraste | `src/treinar_arvore.py` | `results/tarefa3/` | [`docs/relatorio_tarefa3.md`](docs/relatorio_tarefa3.md) |

Os diários das três tarefas, com a parte técnica preenchida, estão em [`docs/diarios/`](docs/diarios/).

Os parâmetros ficam em `config/`, fora do código:
- `config/coleta.json`: períodos, destinos, sondas e exclusões.
- `config/rotulagem.json`: piso do baseline, limiares da tabela de rótulo e corte temporal.
- `config/arvore.json`: colunas permitidas e proibidas, critério, semente e grade de parâmetros.

### Como executar

Na raiz do repositório:

```bash
pip install -r requirements.txt
python src/coletar_bruto.py
python src/montar_tabela_bruta.py
python src/relatorio_qualidade.py
python src/baseline_e_rotulo.py
python src/treinar_arvore.py
```

Cada script tem um comportamento definido quando roda de novo:
- **`coletar_bruto.py`:** não baixa de novo um bloco que já existe.
- **Scripts que geram tabela:** recusam sobrescrever uma saída existente sem `--sobrescrever`.
- **`treinar_arvore.py`:** não carrega o bloco de teste, que fica fechado até a Tarefa 5.

## Material das etapas anteriores (histórico)

Estas pastas registram as entregas anteriores e **não são usadas** pelas Tarefas 1 a 3.

| Pasta / arquivo | O que é | Por que não é usado agora |
|---|---|---|
| `1 - Template_Memorando_de_Decisao.md`, `memorando-de-decisao/` | Memorando: escolha do RIPE Atlas no lugar do dataset do Kaggle | Decisão já tomada. A fonte continua sendo o RIPE Atlas |
| `Anchors.txt` | As 20 Anchors de destino escolhidas pela equipe | Os mesmos destinos estão em `config/coleta.json` |
| `Coleta de Dados/Coleta_de_dados.ipynb` | Entrega 1: coleta one-off das medições 210957734 e 210958049 | Medição one-off, sem série temporal |
| `Coleta de Dados/passo_a_passo_fluxo.ipynb` | Tutorial: como achar Anchor, medição e sondas | Material de estudo |
| `Coleta de Dados/coleta_destino_unico.ipynb`, `coleta_multidestino.ipynb` | Coletas contínuas de outubro (um destino; 20 destinos) | Uma janela só (sem Períodos A e B). O jitter é a média das diferenças, não o desvio-padrão. O rótulo usa média e desvio da própria janela. O `coleta_multidestino.ipynb` continua sendo a origem do sorteio dos 100 pares |
| `Coleta de Dados/RAW/`, `Coleta de Dados/PROCESSADO/`, `limpar_dataset_multidestino.py` | Saídas dessas coletas e a limpeza do dataset multidestino | Substituídas por `data/` |
