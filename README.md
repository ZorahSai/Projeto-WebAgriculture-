# 📡 Preditor de Degradação de Rede com RTT Normalizado

> **Projeto Integrador** — Redes de Computadores · Estrutura de Dados II · Análise de Sistemas
> Preditor de falha/risco em dispositivos de rede, com modelo de predição em árvore de decisão.

🌐 **Apresentação no ar:** [zorahsai.github.io/Projeto-WebAgriculture-](https://zorahsai.github.io/Projeto-WebAgriculture-/)

🎬 **Vídeo:** [pitch de 90 segundos](docs/pitch/webagriculture-90s.mp4) · [transcrição](docs/pitch/transcricao.md)

📄 **Artigo complementar:** [comparação de modelos para previsão a 12 minutos](https://iedahirari.github.io/artigo-preditor-redes/)

![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-árvore%20de%20decisão-F7931E?logo=scikitlearn&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-dados-150458?logo=pandas&logoColor=white)
![RIPE Atlas](https://img.shields.io/badge/RIPE%20Atlas-API%20pública-0B5394)
![Scrum](https://img.shields.io/badge/metodologia-Scrum-6DB33F)

---

## 📌 Sumário

1. [Sobre o Projeto](#1--sobre-o-projeto)
2. [Alinhamento com as Disciplinas](#2--alinhamento-com-as-disciplinas)
3. [Cronograma](#3--cronograma)
4. [Metodologia](#4--metodologia)
5. [Pipeline (Tarefas 1 a 5)](#5--pipeline-tarefas-1-a-5)
6. [Situação da Implementação](#6--situação-da-implementação)
7. [Estrutura do Repositório](#7--estrutura-do-repositório)
8. [Tecnologias](#8--tecnologias)
9. [Como Executar](#9--como-executar)
10. [Documentação](#10--documentação)
11. [Material das Etapas Anteriores](#11--material-das-etapas-anteriores)
12. [Autores](#12--autores)

---

## 1. 📖 Sobre o Projeto

### Visão Geral

Projeto integrador entre **Redes de Computadores**, **Estrutura de Dados II** e **Análise de Sistemas**, desenvolvido com a metodologia **Scrum**. As três disciplinas trabalham em paralelo a partir de um **contrato de dados** definido no início do projeto.

A disciplina de Redes gera um log com métricas reais de monitoramento de dispositivos, usado para treinar uma árvore de decisão. Estrutura de Dados II constrói o modelo e um dashboard em tempo real que classifica dispositivos ao vivo, combinando monitoramento real (ping) com um modo de simulação de eventos que garante a demonstração de todas as classes (**OK**, **RISCO**, **FALHA**). Análise de Sistemas prepara e organiza o projeto quanto aos seus requisitos mínimos.

### Objetivo

Desenvolver, de forma iterativa e incremental via Scrum, uma aplicação que treine uma árvore de decisão a partir de um log histórico de rede e disponibilize um dashboard capaz de classificar dispositivos em tempo real, monitorando a rede local e permitindo injetar eventos simulados sob demanda.

### Pergunta central

> Um RTT alto, sozinho, **não** indica falha. A degradação é medida pelo desvio em relação ao normal **do próprio fluxo**.

---

## 2. 🎓 Alinhamento com as Disciplinas

| Disciplina | Contribuição |
|---|---|
| 🌐 **Redes de Computadores** | Coleta de medições reais de ping (RIPE Atlas), definição de fluxo, baseline por fluxo e métricas de RTT, jitter e perda |
| 🌳 **Estrutura de Dados II** | Árvore de decisão (treino, ajuste, poda, teste único) e dashboard de classificação |
| 📋 **Análise de Sistemas** | Requisitos, RFC, dicionário de dados versionado, diários de tarefa e organização Scrum |

---

## 3. 🗓️ Cronograma

| Marco | Data |
|---|---|
| Início do projeto | semana de 17/08/2026 |
| Período A — baseline | 06/09/2026 04:32 → 13/09/2026 04:32 UTC |
| Período B — rotulado | 13/09/2026 04:32 → 20/09/2026 04:32 UTC |
| Apresentação | 10 a 12/11/2026 |

---

## 4. 🔬 Metodologia

- **Fonte:** medições públicas de ping IPv4 entre Anchors do RIPE Atlas, acessadas só com `GET`, sem criar medição nem gastar crédito.
- **Fluxo:** `fluxo_id = probe_id|dst_addr`. São 20 destinos com 5 origens da mesma região, num total de 100 pares. Três pares são auto-ping e ficam de fora, o que deixa **97 fluxos**.
- **Diversidade de caminhos:** os RTTs medianos vão de cerca de **1 ms a 318 ms**, ou seja, há caminhos curtos e longos.
- **Baseline:** calculado por fluxo no Período A, que não é rotulado.
- **Rótulo:** cada medição do Período B recebe **OK**, **RISCO** ou **FALHA** pelo desvio em relação ao baseline do próprio fluxo, e não por um limite fixo de RTT.
- **Corte temporal:** treino, validação e teste são separados no tempo. O teste fica fechado até a árvore final (Tarefa 5).

O detalhamento está no RFC do grupo: [Preditor de degradação de rede com RTT normalizado](docs/RFC_Preditor_Degradacao_Rede.md).

---

## 5. ⚙️ Pipeline (Tarefas 1 a 5)

```text
 RIPE Atlas (API pública, só GET)
            │
            ▼
 ┌──────────────────────┐   T1  coletar_bruto · montar_tabela_bruta · relatorio_qualidade
 │  Coleta bruta        │   → data/raw/json/ · data/raw/medicoes_brutas.csv.gz
 └──────────┬───────────┘
            ▼
 ┌──────────────────────┐   T2  baseline_e_rotulo
 │  Baseline + rótulo   │   → baseline_por_fluxo.csv · dataset_rotulado_B.csv.gz
 │  + corte temporal    │     · corte_temporal.json
 └──────────┬───────────┘
            ▼
 ┌──────────────────────┐   T3  treinar_arvore
 │  Primeira árvore     │   → results/tarefa3/
 │  + árvore contraste  │
 └──────────┬───────────┘
            ▼
 ┌──────────────────────┐   T4  ajustar_arvore
 │  Ajuste pelo erro    │   → results/tarefa4/
 └──────────┬───────────┘
            ▼
 ┌──────────────────────┐   T5  arvore_final
 │  Árvore final        │   → results/tarefa5/
 │  + teste único       │
 └──────────────────────┘
```

| Etapa | Script | Saída | Relatório |
|---|---|---|---|
| **Tarefa 1:** coleta bruta, sem rótulo | `src/coletar_bruto.py`, `src/montar_tabela_bruta.py`, `src/relatorio_qualidade.py` | `data/raw/json/` (respostas da API, intactas) e `data/raw/medicoes_brutas.csv.gz` | [RFC](docs/RFC_Preditor_Degradacao_Rede.md), [qualidade](docs/relatorio_qualidade_tarefa1.md), [dicionário v0.1](docs/dicionario_v0.1.md) |
| **Tarefa 2:** baseline, rótulo e corte | `src/baseline_e_rotulo.py` | `data/processed/baseline_por_fluxo.csv`, `dataset_rotulado_B.csv.gz`, `corte_temporal.json` | [relatório](docs/relatorio_tarefa2.md), [dicionário v0.2](docs/dicionario_v0.2.md) |
| **Tarefa 3:** primeira árvore e árvore de contraste | `src/treinar_arvore.py` | `results/tarefa3/` | [relatório](docs/relatorio_tarefa3.md) |
| **Tarefa 4:** ajuste da árvore a partir do erro | `src/ajustar_arvore.py` | `results/tarefa4/` | [relatório](docs/relatorio_tarefa4.md) |
| **Tarefa 5:** árvore final e teste único | `src/arvore_final.py` | `results/tarefa5/` | [dicionário v0.4](docs/dicionario_v0.4.md), [diário](docs/diarios/Tarefa5_Arvore_Final.md) |

### Parâmetros (fora do código)

| Arquivo | Conteúdo |
|---|---|
| `config/coleta.json` | Períodos, destinos, sondas e exclusões |
| `config/rotulagem.json` | Piso do baseline, limiares da tabela de rótulo e corte temporal |
| `config/arvore.json` | Colunas e grade da primeira árvore (Tarefa 3) |
| `config/arvore_tarefa4.json` | Grade de ajuste (profundidade, folha, Gini/entropia, poda) |

---

## 6. ✅ Situação da Implementação

| Código | Entrega | Status |
|:---:|---|:---:|
| T1 | Coleta bruta, tabela e relatório de qualidade | ✅ |
| T2 | Baseline por fluxo, rotulagem e corte temporal | ✅ |
| T3 | Primeira árvore e árvore de contraste | ✅ |
| T4 | Ajuste da árvore a partir do erro | ✅ |
| T5 | Árvore final e teste único | ✅ |
| — | Apresentação web (GitHub Pages) | ✅ |

---

## 7. 🗂️ Estrutura do Repositório

```text
Projeto-WebAgriculture-/
├── config/                  # parâmetros de coleta, rotulagem e árvore (JSON)
├── data/
│   ├── raw/                 # respostas da API e tabela bruta
│   └── processed/           # baseline, dataset rotulado e corte temporal
├── docs/
│   ├── apresentacao.html    # site de apresentação (GitHub Pages)
│   ├── index.html           # redireciona para a apresentação
│   ├── RFC_Preditor_Degradacao_Rede.md
│   ├── relatorio_*.md       # relatórios das tarefas
│   ├── dicionario_v*.md     # dicionário de dados versionado
│   └── diarios/             # diários das Tarefas 1 a 5
├── results/
│   ├── tarefa3/
│   ├── tarefa4/
│   └── tarefa5/
├── src/                     # scripts do pipeline (Tarefas 1 a 5)
├── etapas_anteriores/       # histórico das entregas anteriores (não usado nas Tarefas 1 a 5)
│   ├── coleta_de_dados/     # notebooks e coletas antigas
│   ├── modelo_sintetico/    # protótipo com dataset sintético
│   ├── memorando_de_decisao/# memorando RIPE Atlas × Kaggle
│   └── Anchors.txt          # Anchors de destino escolhidas
├── requirements.txt
└── README.md
```

---

## 8. 🛠️ Tecnologias

| Tecnologia | Uso |
|---|---|
| **Python 3** | Linguagem do pipeline |
| **pandas / NumPy** | Tabelas, baseline e rotulagem |
| **scikit-learn** | Árvore de decisão, grade de ajuste e métricas |
| **requests** | Leitura da API pública do RIPE Atlas |
| **RIPE Atlas** | Fonte das medições de ping entre Anchors |
| **HTML / CSS / JS** | Apresentação publicada no GitHub Pages |
| **Git + GitHub** | Versionamento e publicação |

As versões estão em [`requirements.txt`](requirements.txt).

---

## 9. ▶️ Como Executar

Na raiz do repositório:

```bash
pip install -r requirements.txt
python src/coletar_bruto.py
python src/montar_tabela_bruta.py
python src/relatorio_qualidade.py
python src/baseline_e_rotulo.py
python src/treinar_arvore.py
python src/ajustar_arvore.py
python src/arvore_final.py
```

Cada script tem um comportamento definido quando roda de novo:

- **`coletar_bruto.py`:** não baixa de novo um bloco que já existe.
- **Scripts que geram tabela:** recusam sobrescrever uma saída existente sem `--sobrescrever`.
- **`treinar_arvore.py` e `ajustar_arvore.py`:** não carregam o bloco de teste, que ficou fechado até a Tarefa 4.
- **`arvore_final.py`:** abre o teste uma única vez, com os parâmetros lidos de `results/tarefa4/metricas_validacao.json`.

Para ver a apresentação localmente, abra [`docs/apresentacao.html`](docs/apresentacao.html) no navegador.

---

## 10. 📚 Documentação

| Documento | Descrição |
|---|---|
| [RFC](docs/RFC_Preditor_Degradacao_Rede.md) | Proposta técnica do preditor com RTT normalizado |
| [Relatório de qualidade (T1)](docs/relatorio_qualidade_tarefa1.md) | Cobertura e qualidade da coleta bruta |
| [Relatório T2](docs/relatorio_tarefa2.md) | Baseline, rotulagem e corte temporal |
| [Relatório T3](docs/relatorio_tarefa3.md) | Primeira árvore e contraste |
| [Relatório T4](docs/relatorio_tarefa4.md) | Ajuste da árvore |
| [Dicionário v0.1](docs/dicionario_v0.1.md) · [v0.2](docs/dicionario_v0.2.md) · [v0.4](docs/dicionario_v0.4.md) | Dicionário de dados versionado |
| [Diários](docs/diarios/) | Diários das Tarefas 1 a 5 |
| [Resumo do mapa mental](docs/resumo_mapa_mental_grupo.md) | Síntese do mapa mental do grupo |

---

## 11. 🗃️ Material das Etapas Anteriores

Estas pastas registram as entregas anteriores e **não são usadas** pelas Tarefas 1 a 5.

| Pasta / arquivo | O que é | Por que não é usado agora |
|---|---|---|
| `etapas_anteriores/memorando_de_decisao/` | Memorando: escolha do RIPE Atlas no lugar do dataset do Kaggle | Decisão já tomada. A fonte continua sendo o RIPE Atlas |
| `etapas_anteriores/Anchors.txt` | As 20 Anchors de destino escolhidas pela equipe | Os mesmos destinos estão em `config/coleta.json` |
| `etapas_anteriores/coleta_de_dados/Coleta_de_dados.ipynb` | Entrega 1: coleta one-off das medições 210957734 e 210958049 | Medição one-off, sem série temporal |
| `etapas_anteriores/coleta_de_dados/passo_a_passo_fluxo.ipynb` | Tutorial: como achar Anchor, medição e sondas | Material de estudo |
| `etapas_anteriores/coleta_de_dados/coleta_destino_unico.ipynb`, `coleta_multidestino.ipynb` | Coletas contínuas de outubro (um destino; 20 destinos) | Uma janela só (sem Períodos A e B). O jitter é a média das diferenças, não o desvio-padrão. O rótulo usa média e desvio da própria janela. O `coleta_multidestino.ipynb` continua sendo a origem do sorteio dos 100 pares |
| `etapas_anteriores/coleta_de_dados/RAW/`, `PROCESSADO/`, `limpar_dataset_multidestino.py` | Saídas dessas coletas e a limpeza do dataset multidestino | Substituídas por `data/` |
| `etapas_anteriores/modelo_sintetico/` | Protótipo com gerador de dataset sintético e árvore própria | Substituído pelo pipeline com dados reais em `src/` |

---

## 12. 👥 Autores

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/apollomoura"><img src="https://github.com/apollomoura.png?size=100" width="100" alt="Apollo Moura De Sousa"/></a><br/>
      <b>Apollo Moura De Sousa</b><br/>
      <a href="https://github.com/apollomoura">GitHub</a> · <a href="https://www.linkedin.com/in/apollo-moura-215306320/">LinkedIn</a>
    </td>
    <td align="center">
      <a href="https://github.com/clicaro"><img src="https://github.com/clicaro.png?size=100" width="100" alt="Icaro Luiz Dellalo Silva"/></a><br/>
      <b>Icaro Luiz Dellalo Silva</b><br/>
      <a href="https://github.com/clicaro">GitHub</a> · <a href="https://www.linkedin.com/in/icaro-dellalo/">LinkedIn</a>
    </td>
    <td align="center">
      <a href="https://github.com/iedahirari"><img src="https://github.com/iedahirari.png?size=100" width="100" alt="Ieda de Oliveira"/></a><br/>
      <b>Ieda de Oliveira</b><br/>
      <a href="https://github.com/iedahirari">GitHub</a> · <a href="https://www.linkedin.com/in/ieda-oliveira/">LinkedIn</a>
    </td>
    <td align="center">
      <a href="https://github.com/ZorahSai"><img src="https://github.com/ZorahSai.png?size=100" width="100" alt="João Pedro C. de Morais"/></a><br/>
      <b>João Pedro C. de Morais</b><br/>
      <a href="https://github.com/ZorahSai">GitHub</a> · <a href="https://www.linkedin.com/in/jo%C3%A3o-pedro-06724430b/">LinkedIn</a>
    </td>
    <td align="center">
      <a href="https://github.com/SuperLucas2000"><img src="https://github.com/SuperLucas2000.png?size=100" width="100" alt="Lucas Matteus Baptista de Godoy"/></a><br/>
      <b>Lucas Matteus Baptista de Godoy</b><br/>
      <a href="https://github.com/SuperLucas2000">GitHub</a> · <a href="https://www.linkedin.com/in/lucasmatteus/">LinkedIn</a>
    </td>
  </tr>
</table>

---

<p align="center">Projeto acadêmico — 2026</p>

## Uso do modelo e verificação

Para apenas reempacotar os artefatos existentes e verificar o contrato:

```sh
python -m pip install -r entrega/requirements.txt
python entrega/carregar_modelo.py
python src/empacotar_entrega.py
python -m unittest discover -s tests -v
```

Esse caminho não roda novamente a coleta, não ajusta a árvore e não reabre o bloco de teste. `src/exportar_entrega.py` continua sendo o exportador com treino; use `empacotar_entrega.py` quando só quiser fechar o ZIP existente.
