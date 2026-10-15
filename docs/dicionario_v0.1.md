# Dicionário de dados v0.1 — medições brutas (Tarefa 1)

Arquivo: `data/raw/medicoes_brutas.csv.gz`, gerado por `src/montar_tabela_bruta.py` a partir dos JSONs em `data/raw/json/`.

Cada linha é **uma medição ICMP de um fluxo**, com timestamp. Esta versão só tem colunas brutas da medição. Não há classe (OK, RISCO, FALHA), baseline, mediana nem métrica relativa: tudo isso é da Tarefa 2.

## Fonte

- **Origem dos dados:** medições públicas e contínuas de ping IPv4 entre Anchors do RIPE Atlas, obtidas só com `GET` em `/api/v2/measurements/{id}/results/`. Nenhuma medição foi criada.
- **Cobertura:** 20 destinos e 5 origens da mesma região por destino, num total de 100 pares baixados. Três deles são auto-ping (a sonda é a própria Anchor de destino) e ficam fora da tabela, como manda o Guia de Coleta. Restam 97 fluxos. Os parâmetros e as exclusões estão em `config/coleta.json`.
- **Rajada:** 3 pacotes por medição, com uma medição a cada 240 s por fluxo.
- **Períodos:** sem sobreposição entre eles.
  - **Período A** (só baseline): 06/09/2026 04:32 a 13/09/2026 04:32 UTC.
  - **Período B** (a rotular): 13/09/2026 04:32 a 20/09/2026 04:32 UTC.

## Colunas

| Coluna | Tipo / unidade | Definição | Ausente quando |
|---|---|---|---|
| `timestamp` | texto ISO 8601, UTC | Instante da medição (`timestamp` da API) | nunca |
| `periodo` | `A` ou `B` | Bloco de tempo da medição. A vai de `inicio` (inclusivo) a `fim` (exclusivo); B começa exatamente onde A termina | nunca |
| `measurement_id` | inteiro | Identificador da medição no RIPE Atlas (`msm_id`) | nunca |
| `probe_id` | inteiro | Anchor de origem (`prb_id`) | nunca |
| `dst_addr` | IPv4 | Endereço do destino | nunca |
| `fluxo_id` | texto | `probe_id\|dst_addr`. Identifica o fluxo de forma estável | nunca |
| `latencia_ms` | ms | RTT médio da rajada (`avg` da API) | nenhuma resposta. **Nunca 0**: o `-1` da API vira vazio |
| `rtt_min_ms` | ms | Menor RTT da rajada (`min`) | nenhuma resposta |
| `rtt_max_ms` | ms | Maior RTT da rajada (`max`) | nenhuma resposta |
| `enviados` | contagem | Pacotes enviados (`sent`) | nunca |
| `recebidos` | contagem | Pacotes recebidos (`rcvd`) | nunca |
| `perda_pct` | % | `(enviados − recebidos) / enviados × 100`. Sem resposta, vale 100 | nunca: registros sem `sent` (ou com `sent` = 0) ficam fora da tabela, como manda o Guia de Coleta, e a quantidade é informada pelo script |
| `jitter_ms` | ms | Desvio-padrão amostral (n − 1) dos RTTs da rajada, ignorando respostas duplicadas | menos de 2 respostas. **Nunca 0 fingindo estabilidade** |
| `timeout_atual` | 0 ou 1 | 1 se não há RTT ou se `perda_pct` = 100; senão 0. O timeout permanece na tabela | nunca |

### Colunas só para auditoria de diversidade

Estas colunas **não são variáveis do modelo** e não podem entrar na futura árvore.

| Coluna | Definição |
|---|---|
| `destino_fqdn` | Nome da Anchor de destino |
| `regiao` | Região do destino (América do Sul, América do Norte, Europa, Ásia, Oceania) |
| `pais_origem` | País da Anchor de origem |
| `src_addr` | IP de origem informado pela sonda |

## O que não está aqui

Esta versão não tem classe (OK, RISCO, FALHA), baseline, mediana, MAD, `z_robusto`, divisão em treino e teste, nem nenhuma métrica de modelo.

## Arquivos brutos

- **Resposta da API:** `data/raw/json/<destino>/m<measurement_id>_<inicio>_<fim>.json.gz` guarda a resposta exatamente como veio, compactada. Cada bloco cobre 24 h.
- **Metadados de cada bloco:** `data/raw/json/<destino>/m<measurement_id>_<inicio>_<fim>.meta.json` traz URL, parâmetros, status HTTP, quantidade de registros, horário da coleta e o SHA-256 da resposta.
- **Os JSONs não são alterados.** A tabela é refeita a partir deles com `python src/montar_tabela_bruta.py --sobrescrever`.
