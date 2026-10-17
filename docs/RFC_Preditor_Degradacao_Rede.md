# RFC: Preditor de degradação de rede com RTT normalizado

**Grupo:** WebAgriculture (Apollo Moura De Sousa, Icaro Luiz Dellalo Silva, Ieda de Oliveira, João Pedro C. de Morais, Lucas Matteus Baptista de Godoy)  
**Repositório:** https://github.com/ZorahSai/Projeto-WebAgriculture-  
**Tarefa que entrega este RFC:** Tarefa 1 (problema e coleta bruta, sem rótulo)  
**Fonte:** RFC da professora *Preditor de degradação de rede com RTT normalizado*, preenchido com o recorte, os fluxos e os números **deste** grupo.

> Um RFC formaliza o problema, o contrato dos dados e o critério de decisão **antes** de se investir no classificador. Este documento escolhe a **representação** do fenômeno (RTT normalizado por fluxo). A família do algoritmo (árvore, floresta ou outro) fica para a etapa de modelagem, escolhida na validação. Na Tarefa 1 não se treina árvore, não se calcula mediana e não se grava classe.

Este RFC é o contrato do grupo. Os números da coleta (seção 6) vêm da Tarefa 1. As regras de rótulo (seção 8) são o contrato que a Tarefa 2 aplica; os totais de OK / RISCO / FALHA já observados aparecem como nota, não como dado da ingestão.

---

## 1. Resumo

O projeto constrói um classificador de três estados — **OK**, **RISCO** e **FALHA** — para medições ICMP de pares origem–destino. O estado descreve o afastamento do fluxo em relação ao seu próprio comportamento normal, estimado num período anterior e depois congelado.

A distância da rota entra na física do RTT e na chance de haver mais saltos, congestionamento e perda. Ela **não** entra na classe. Um RTT de 180 ms pode ser o normal de um caminho transoceânico saudável; um salto de 25 ms para 58 ms pode ser degradação num caminho curto. O modelo aprende esse desvio, em conjunto com perda, jitter relativo, timeouts e persistência.

Neste grupo, o fluxo é `fluxo_id = probe_id|dst_addr`. A coleta lê o *Anchoring Mesh* público do RIPE Atlas (ping IPv4, só `GET`). Há caminhos curtos (mediana de cerca de 1 ms) e longos (mediana de cerca de 318 ms) no mesmo período.

---

## 2. Contexto e motivação

Uma rede em operação precisa distinguir quatro coisas que aparecem juntas numa série de ping:

1. **Latência estrutural.** A propagação na fibra tem limite físico. Mais quilômetros e mais roteadores aumentam o RTT mesmo com o caminho saudável. Cruzar um oceano em 150–200 ms (ou mais) é atraso esperado, não defeito. No bruto deste grupo, um fluxo NZ→nz-akl tem mediana de 0,97 ms e um fluxo IQ→jp-tch tem mediana de 317,9 ms; os dois podem estar saudáveis.
2. **Degradação.** O caminho continua respondendo, mas piorou em relação a si mesmo: RTT sobe além da variação típica, o jitter deixa de ser estável ou surge perda moderada e persistente. Causas típicas: congestionamento, enlace saturado, hardware no limite, interferência.
3. **Indisponibilidade.** Perda total ou ausência persistente de resposta. É falha independentemente da distância.
4. **Mudança de rota.** O encaminhamento troca de caminho (tromboning, failover, novo trânsito). O RTT muda de patamar e permanece estável, com perda e jitter baixos. O enlace novo pode estar saudável; o que envelheceu foi o baseline.

Tratar “RTT alto” como falha ensina geografia. Na regra absoluta antiga (OK ≤ 50 ms, FALHA > 100 ms), caminhos longos estáveis viravam FALHA permanente e um enlace curto que quadruplicasse a latência ainda podia sair como OK.

O usuário do alerta é quem opera a rede (campus, provedor ou NOC). O alerta apoia a decisão de investigar o enlace agora, observar, ou recalibrar o “normal” porque o caminho mudou.

---

## 3. Problema e evento a ser previsto

| Pergunta | Resposta do grupo |
| --- | --- |
| Qual evento será previsto? | Degradação ou indisponibilidade de um fluxo ICMP em relação ao baseline daquele fluxo. Não é “rota longa” nem “RTT acima de 100 ms”. |
| Como será definida a classe? | Regra híbrida, auditável, relativa ao fluxo: desvio robusto do RTT, aumento relativo, jitter relativo, perda e persistência. Perda de 100% ou ausência persistente de RTT é FALHA mesmo sem baseline. Os rótulos são operacionais: o modelo reproduz essa política, não um ticket de equipamento. |
| Qual é o horizonte? | Dois alvos, em momentos diferentes. **Detector:** estado da medição corrente (`classe` / `status_atual`). **Preditor:** estado 12 minutos à frente (três intervalos do mesh, de 240 s). O preditor só é útil se superar a persistência do estado atual. Na Tarefa 1 só existe o bruto, sem classe. A árvore entra na Tarefa 3 como detector. |
| Qual é a unidade de análise? | Uma medição de um fluxo, enriquecida depois com a janela causal recente do mesmo fluxo. O fluxo é `fluxo_id = probe_id\|dst_addr` (Anchor de origem `prb_id` e IP da Anchor de destino). O `measurement_id` fica na linha para auditoria. |
| O que é cada linha do bruto? | Uma rajada ICMP de 3 pings, a cada 240 s, com timestamp UTC. Ainda **sem** classe na ingestão. |

Estados:

| Classe | Significado operacional |
| --- | --- |
| **OK** | RTT, jitter e perda compatíveis com o normal daquele fluxo. Nenhuma intervenção. |
| **RISCO** | Aumento relevante e persistente de latência, jitter ou perda, ainda sem indisponibilidade. Observar e priorizar. |
| **FALHA** | Desvio extremo e persistente, perda elevada ou ausência de resposta. Investigar agora. |

Há um quarto estado **operacional**, fora do alvo supervisionado de três classes: **RECALIBRAR**. Ele marca mudança estável de patamar de RTT (rota nova saudável). Não é falha e não deve ser ensinado como FALHA.

---

## 4. Escopo

| Pergunta | Resposta do grupo |
| --- | --- |
| Recorte | Overlay lógica sobre o *Anchoring Mesh* público do RIPE Atlas (ping IPv4). 20 destinos em 7 países (BR 5, US 3, CO 3, DE 3, JP 2, NZ 2, FI 2). Cada destino tem 5 origens da mesma região (100 pares sorteados com semente 42). Três auto-pings fora (`7019 → br-pgz`, `6349 → br-poa`, `7694 → co-ptx`). Restam **97 fluxos**. A classe não usa o país nem a região. |
| Período | 06/09/2026 04:32 UTC a 20/09/2026 04:32 UTC. Sete dias de baseline (Período A) e sete dias posteriores de dataset (Período B), sem sobreposição. O fim de A é exclusivo; B começa nesse instante. |
| Dentro do escopo | Leitura de medições já existentes (`GET`); JSON bruto preservado; tabela bruta sem classe; baseline congelado por fluxo (Tarefa 2); features relativas; rótulos OK / RISCO / FALHA; split temporal; contrato para um monitor local futuro com o mesmo esquema. |
| Fora de escopo | Criar medições (`POST`) ou gastar créditos RIPE Atlas. IPv6, traceroute e HTTP na mesma coluna de latência. Limiar global de RTT (50 ms, 100 ms ou qualquer outro). País, IP ou nome da rota como feature do modelo. Balancear o dataset escolhendo rotas que “fabricam” uma classe. Preencher RTT ausente com 0. Split aleatório de linhas. Escolher o algoritmo neste RFC. Rotular o Período A. |

---

## 5. Usuários e decisão apoiada

O alerta é para quem administra o enlace monitorado.

- **FALHA:** investigar perda, timeout ou desvio extremo persistente.
- **RISCO:** observar e priorizar, sem tratar o evento como queda.
- **OK:** nenhuma intervenção.
- **RECALIBRAR:** abrir um novo período de baseline para o fluxo; não abrir chamado de falha só porque o RTT mudou de patamar.

O mesmo contrato vale para um `log_rede.csv` da instituição, depois de um aquecimento de pelo menos **1.500 amostras válidas** naquele fluxo. Sem esse aquecimento não há mediana confiável, e o modelo normalizado não opera.

---

## 6. Dados e fontes

| Fonte | O que fornece | Papel |
| --- | --- | --- |
| RIPE Atlas v2, mesh de Anchors, ping IPv4 (`GET` público) | Timestamp, `measurement_id`, `probe_id`, `dst_addr`, RTT da rajada (3 pacotes), enviados/recebidos, timeout | Medição bruta. Insumo de feature e do alvo. |
| Período A, por `fluxo_id` | Mediana e MAD do RTT, jitter típico, perda típica, cobertura | Baseline congelado. **Não** é linha de treino e **não** recebe classe. |
| Período B | Features relativas, janela de cerca de 20 minutos (5 medições), classe do detector | Dataset do detector. O preditor de 12 minutos fica para etapa posterior, em arquivo separado se for construído. |

**Volume da Tarefa 1 (bruto, sem classe):**

| Item | Valor |
| --- | --- |
| Arquivo | `data/raw/medicoes_brutas.csv.gz` |
| JSON intacto | `data/raw/json/<destino>/` (280 blocos de 24 h, cada um com `.json.gz` e `.meta.json`) |
| Config | `config/coleta.json` |
| Dicionário | [`docs/dicionario_v0.1.md`](dicionario_v0.1.md) só com colunas brutas |
| Registros brutos | 486.487 (243.051 no A, 243.436 no B) |
| Fluxos | 97 |
| Destinos | 20 |
| Auto-ping fora da tabela | 15.105 registros |
| Sobreposição A∩B no mesmo fluxo | 0 |
| Duplicatas (`fluxo_id` + `timestamp`) | 0 |
| Timeouts (`timeout_atual` = 1) | 21.349 |
| RTT gravado como 0 | 0 |
| RTT (mín / mediana / máx) | 0,71 / 68,22 / 1.326,44 ms |
| Fluxos com &lt; 1.500 RTT válidos no A | 5 (todos para `co-bog-as273103`, ~958 RTT válidos) |

Cadência nativa do mesh: **240 segundos**. Jitter da amostra é o desvio-padrão amostral dos RTTs da rajada somente quando há pelo menos duas respostas; com 0 ou 1 resposta o jitter fica vazio.

Caminhos curtos e longos no mesmo período (RTT mediano no bruto):

| Tipo | Fluxo | Origem → destino | Mediana |
| --- | --- | --- | --- |
| Curto | `6904\|103.121.34.150` | NZ → nz-akl | 0,97 ms |
| Curto | `6659\|156.154.122.254` | BR → br-sao | 1,28 ms |
| Longo | `7628\|103.40.209.7` | AZ → jp-tyo | 310,0 ms |
| Longo | `7020\|43.228.174.199` | IQ → jp-tch | 317,9 ms |

O material sobre distância das rotas recomenda, para um agente local, rajadas de 10 a 20 pings espaçados de 1 segundo a cada 5 minutos, jitter no sentido da RFC 3550 e um baseline de cerca de 5 dias. Esse desenho é o contrato do **monitor local futuro**. A coleta deste projeto não o replica: o mesh já amostra a cada 4 minutos com 3 pacotes, a leitura é somente `GET`, e um ping contínuo a cada segundo criaria carga inútil. Sete dias em cada período cobrem um ciclo semanal e ficam acima de 1.500 amostras por fluxo (salvo os cinco de Bogotá).

**Nota após a Tarefa 2 (não faz parte da ingestão):** 92 fluxos com ficha; 5 excluídos sem mediana inventada; 230.854 medições rotuladas em B (80,4% OK, 7,1% RISCO, 12,5% FALHA); arquivo `data/processed/dataset_rotulado_B.csv.gz`. Esse desbalanceamento é o fenômeno: a malha passa a maior parte do tempo no próprio normal.

---

## 7. Custo dos erros

| Tipo de erro | O que significa | Consequência |
| --- | --- | --- |
| Falso negativo de FALHA | Indisponibilidade ou desvio extremo persistente classificado como OK ou RISCO | O enlace degrada sem investigação. É o erro mais grave. |
| Falso negativo de RISCO | Início de saturação tratado como OK | Atraso na priorização. Grave, e mais difícil porque RISCO é a classe rara. |
| Falso positivo de FALHA | Rota longa saudável, pico isolado ou mudança estável de caminho rotulados como queda | Fadiga de alerta e chamado indevido. Foi o modo de falha da regra absoluta. |
| Falso positivo de RISCO | Oscilação normal do fluxo disparando alerta | Ruído operacional. A persistência (2 de 5 medições) existe para cortar pico isolado. |

A métrica principal é o **F1 macro**, com recall de FALHA e a confusão RISCO↔FALHA reportados à parte. Acurácia isolada é enganosa com ~80% de OK. O limiar de decisão do modelo, quando houver probabilidade, escolhe-se na validação; o teste é usado uma vez (Tarefa 5).

---

## 8. Abordagem proposta

O tipo de modelo adequado é o **Modelo RTT normalizado**: um único modelo treinado com muitos fluxos, cada um descrito pelo desvio em relação ao seu baseline. Um modelo por fluxo exigiria série e manutenção próprias para cada caminho. Um modelo único com RTT absoluto confunde distância com falha.

Caminho, sem escolha de algoritmo neste RFC:

ingestão do mesh (JSON bruto preservado) → Período A só para baseline → congelamento → features relativas no Período B → rótulo híbrido → split temporal → baselines de regra (persistência e classe majoritária) → classificador → limiar na validação → model card.

No repositório: `src/coletar_bruto.py` e `src/montar_tabela_bruta.py` (Tarefa 1) → `src/baseline_e_rotulo.py` (Tarefa 2) → `src/treinar_arvore.py` (Tarefa 3, árvore CART). A escolha da árvore é da etapa de modelagem, não deste RFC.

### 8.1 O que a distância explica

A distância aumenta a chance de falha de entrega porque o pacote atravessa mais saltos, acumula atraso de propagação e fica exposto a mais pontos de congestionamento. Congestionamento, cabo, conector, interferência e hardware continuam sendo causas mesmo em rota curta.

Por isso o RTT médio bruto não classifica. Ele mistura o comprimento do caminho com o incidente. O que classifica é o comportamento estatístico do RTT **daquele** fluxo, junto com perda e instabilidade (jitter), sustentados no tempo.

Exemplos que o modelo tem de tratar como OK quando estáveis:

| Caminho neste grupo | RTT mediano observado | Leitura |
| --- | --- | --- |
| NZ → nz-akl (`6904`) | 0,97 ms | Normal baixo, intra-região. |
| BR → br-sao (`6659`) | 1,28 ms | Normal curto. |
| DE / NL → de-mai (`6655`) | 7,22 ms | Normal europeu curto. |
| IQ → jp-tch (`7020`) | 317,9 ms | Normal do fluxo longo. 318 ms estável não é FALHA. |

O caso didático do material de rotas (caminho tromboning com RTT estável perto de 180 ms contra 5–15 ms no caminho direto) é mudança de encaminhamento, tratada na seção 8.5, não como falha de hardware.

### 8.2 Baseline por fluxo

O baseline é uma ficha por `fluxo_id`, calculada **só no Período A** e depois congelada. O Período B não entra nessa conta e não é rotulado com estatística calculada nele.

| Passo | O que fazer |
| --- | --- |
| 1 | Separar o fluxo. Ordenar as medições pelo timestamp. |
| 2 | Cortar o tempo. Período A: 06/09/2026 04:32 UTC até 13/09/2026 04:32 UTC (fim exclusivo). Período B: esse instante até 20/09/2026 04:32 UTC. Sem amostra nos dois períodos. |
| 3 | Marcar RTT válido. Entra na ficha só a medição com RTT presente. RTT ausente e perda de 100% ficam de fora da mediana e do MAD. Continuam no dataset como evento de timeout. |
| 4 | Exigir volume. Menos de 1.500 RTT válidos no Período A: o fluxo é `baseline_insuficiente` e não recebe classe. |
| 5 | Calcular a ficha e gravar uma linha em `data/processed/baseline_por_fluxo.csv`. Não recalcular com o Período B. |

| Campo da ficha | Fórmula, só com o Período A |
| --- | --- |
| `mediana` | mediana dos RTT válidos |
| `MAD` | mediana(\|RTT − mediana\|) dos RTT válidos |
| `IQR` | P75 − P25 dos RTT válidos; só entra na conta se MAD = 0 |
| `jitter_tipico` | mediana do jitter nas medições com jitter presente |
| `perda_tipica` | mediana de `perda_pct` em todas as medições do período, inclusive timeout |
| `prop_resposta` | medições com RTT válido / medições do período |

A média e o desvio-padrão clássicos descrevem a mesma ideia (janela de normalidade da rota), mas picos inflam a média e o desvio e alargam o “normal” até engolir a falha. O escore robusto é a versão estável da regra dos três sigmas:

\[
z_{\mathrm{robusto}} = \frac{x - \mathrm{mediana}}{1{,}4826 \times \mathrm{MAD}}
\]

O fator 1,4826 torna o MAD comparável ao desvio-padrão quando a distribuição é aproximadamente normal. Assim, os gatilhos “cerca de 2 desvios” e “cerca de 3 desvios” sobrevivem, sem herdar a sensibilidade da média.

Se MAD = 0 e a latência corrente é a mediana, \(z = 0\). Caso contrário usa-se \(\max(\mathrm{IQR}/1{,}349,\, 1\,\mathrm{ms})\), para não dividir por zero.

Limiares de cálculo: `config/rotulagem.json`.

### 8.3 Features

Cada linha do modelo leva o vetor relativo, não o mapa:

\[
X = [\text{latência relativa},\, z_{\mathrm{robusto}},\, \text{perda},\, \text{jitter relativo},\, \text{timeouts},\, \text{persistência}]
\]

```text
latencia_relativa    = latencia_atual / mediana_A
aumento_pct          = (latencia_atual - mediana_A) / mediana_A * 100
z_robusto            = (latencia_atual - mediana_A) / (1,4826 * MAD_A)
jitter_relativo      = jitter_atual / jitter_tipico_A
```

Uma razão de latência igual a 1,0 é “no normal” tanto para NZ→nz-akl quanto para IQ→jp-tch. Persistência olha as últimas janelas do mesmo fluxo (cinco medições, ~20 minutos): `n5_timeout`, `n5_aumento80`, `n5_risco`.

País, IP, `probe_id`, `fluxo_id`, região, FQDN, `latencia_ms` absoluta, `jitter_ms` absoluto e `mediana` ficam de fora da árvore oficial: a árvore aprenderia “Japão = FALHA” ou “RTT > 150 ms = FALHA” e o contrato quebraria no log local.

RTT ausente permanece vazio, com `timeout_atual = 1`. Zero milissegundo seria um OK falso.

Lista oficial da Tarefa 3 (já alinhada a este RFC): `z_robusto`, `aumento_pct`, `jitter_relativo`, `perda_pct`, `timeout_atual`, `n5_timeout`, `n5_aumento80`, `n5_risco`. Ver `config/arvore.json` e [`docs/dicionario_v0.2.md`](dicionario_v0.2.md).

### 8.4 Regra de rotulagem

A classe nasce de uma política explícita. Calculam-se as métricas e aplica-se a **primeira linha verdadeira**. Não há empate: FALHA ganha de RISCO, e RISCO ganha de OK. Na Tarefa 1 esta tabela **não é aplicada**; o bruto permanece sem classe.

**Métricas, por fluxo, com o baseline do Período A congelado.**

| Métrica | Fórmula | Valor que entra na regra |
| --- | --- | --- |
| `mediana` | mediana dos RTT válidos do Período A | ms |
| `MAD` | mediana(\|RTT − mediana\|) | ms |
| `z_robusto` | (RTT atual − mediana) / (1,4826 × MAD) | sem unidade |
| `aumento_pct` | (RTT atual − mediana) / mediana × 100 | % |
| `jitter_relativo` | jitter atual / jitter típico do baseline | sem unidade |
| `perda_pct` | (enviados − recebidos) / enviados × 100 | % |
| `timeout_atual` | 1 se não há RTT ou `perda_pct` = 100; senão 0 | 0 ou 1 |
| `n5_timeout` | quantos timeouts nas últimas 5 medições deste fluxo, incluindo a atual | 0 a 5 |
| `n5_aumento80` | quantas das últimas 5 têm `aumento_pct` > 80 | 0 a 5 |
| `n5_risco` | quantas das últimas 5 cumprem o critério de risco da linha 5 | 0 a 5 |

Casos de conta:

| Situação | O que fazer |
| --- | --- |
| RTT ausente | Não calcular `z_robusto` nem `aumento_pct`. `timeout_atual` = 1. Não preencher RTT com 0. |
| MAD = 0 e RTT atual = mediana | `z_robusto` = 0 |
| MAD = 0 e RTT atual ≠ mediana | Denominador = max(IQR / 1,349, 1 ms) |
| Jitter atual vazio (menos de 2 respostas) | O critério de jitter não dispara |
| Jitter típico = 0 e jitter atual = 0 | `jitter_relativo` = 1 |
| Jitter típico = 0 e jitter atual > 0 | Tratar como `jitter_relativo` ≥ 3 |
| Menos de 1.500 RTT válidos no Período A | Não rotular. Fluxo `baseline_insuficiente` |

**Regra de rótulo. Parar na primeira linha verdadeira.**

| Ordem | Classe | Condição |
| --- | --- | --- |
| 1 | **FALHA** | `perda_pct` ≥ 10 nesta medição (inclui 33%, 67% e 100% da rajada de 3 pacotes) |
| 2 | **FALHA** | `n5_timeout` ≥ 3 |
| 3 | **FALHA** | `z_robusto` ≥ 3,5 nesta medição, com RTT presente |
| 4 | **FALHA** | `n5_aumento80` ≥ 2 |
| 5 | **RISCO** | nesta medição, pelo menos um destes: `2 ≤ z_robusto < 3,5`, ou `30 ≤ aumento_pct ≤ 80`, ou `jitter_relativo ≥ 3`; **e** `n5_risco` ≥ 2 |
| 6 | **OK** | nenhuma linha anterior; pico isolado também fica OK |

Leitura: um único desvio moderado não vira RISCO. Dois desvios moderados nas últimas cinco medições viram RISCO. `z_robusto` ≥ 3,5 vira FALHA já na medição corrente. Perda de um pacote em três (≥ 33%) vira FALHA na hora, porque 33 ≥ 10.

`status_absoluto` (OK ≤ 50 ms, FALHA > 100 ms) **não** entra nesta tabela.

Regra crítica, independente do baseline:

```text
perda = 100% ou ausência persistente de RTT  =>  FALHA
```

Com 3 pacotes ICMP, a perda observável é 0%, 33%, 67% ou 100%. Faixas de 0,5% e 2% do material de voz/vídeo não aparecem nesta amostra. Um teto global de jitter em milissegundos repetiria o erro do teto global de RTT; o que entra no rótulo é o jitter dividido pelo jitter do próprio baseline.

Quando o monitor local passar a usar rajadas de 10 a 20 pacotes, a perda pode descer à granularidade mais fina, sempre comparada também à perda típica do fluxo. O espírito permanece: perda e instabilidade disparam alerta; o valor bruto do RTT não dispara sozinho.

### 8.5 Mudança de rota

Se o RTT muda de patamar e **permanece estável**, com perda próxima de zero e jitter baixo por uma janela longa (no material, mais de uma hora; na cadência de 4 minutos, da ordem de 15 amostras), a evidência é de novo encaminhamento, não de saturação.

```text
se |z_robusto| alto
   e perda próxima do normal do fluxo
   e jitter_relativo baixo
   por uma janela sustentada (ordem de 1 hora)
então RECALIBRAR
senão aplicar a regra híbrida da seção 8.4
```

RECALIBRAR descarta a ficha antiga e abre um novo período de baseline (o material sugere 24–48 h; o piso de 1.500 amostras válidas continua). Queda de RTT estável (fim de um tromboning) segue a mesma regra. Essas janelas não devem entrar como FALHA no treino.

O dataset rotulado do Período B **ainda não** separa esse estado. Introduzir a coluna é decisão de revisão de rótulos, só com o passado de cada fluxo, sem usar o período de teste.

Caso já observado neste grupo (Tarefa 2): fluxo `7399|91.198.196.228` (LU → de-mdt) passou de mediana 7,2 ms no A para 13,1 ms estável no B, sem perda e com jitter normal; as 2.495 medições do B saíram FALHA pela linha 3. É o viés que RECALIBRAR pretende corrigir.

O fluxo é o par probe e endereço de destino. Troca de IP é outro fluxo e exige baseline próprio.

### 8.6 Como o modelo deve ser lido

O modelo não aprende que RTT alto significa falha. Aprende que risco ou falha ocorrem quando o comportamento recente do fluxo se afasta do normal daquele mesmo fluxo, com perda, instabilidade ou ausência de resposta, e que um patamar novo porém estável pede recalibração.

Para um fluxo nunca visto, o procedimento é de calibração, não de retreino: observa-se o período inicial, congela-se a ficha e só então se aplicam as features relativas. Sem esse período o modelo não opera naquele fluxo.

---

## 9. Avaliação

Dois protocolos, com resultados separados.

**Protocolo A — tempo.** Dentro do Período B, o passado treina, um bloco posterior valida e o bloco mais recente testa. Sem sorteio de linhas. Janelas com lag (`n5_*`) respeitam uma folga (embargo de 4 medições) entre os blocos. Qualquer imputação, escala ou balanceamento aprende-se só no treino. Proporção de partida 50% / 20% / 30% dentro de B.

Neste grupo o Protocolo A já está gravado em `data/processed/corte_temporal.json` (treino 115.804, validação 45.842, teste 68.472, embargo 736). O bloco de teste permanece fechado até a Tarefa 5.

**Protocolo B — fluxos novos.** Grupos inteiros por `fluxo_id`. Nenhum fluxo de teste aparece no treino. O baseline do fluxo de teste sai só do período inicial dele. O conjunto de teste precisa continuar cobrindo caminho curto e caminho longo. Este protocolo ainda não foi executado.

Métricas: matriz 3×3, precisão, recall e F1 por classe, F1 macro, e o mesmo corte por fluxo. Comparar o preditor de 12 minutos (quando existir) com a regra que copia o estado atual. Sem ganho sobre a persistência, a entrega declara o sistema como **detector**, e o nome “preditor” não se sustenta sozinho.

---

## 10. Riscos e limitações

- Rótulos heurísticos. O modelo aprende a política de degradação, não uma falha confirmada em log de roteador.
- Anchors são melhor provisionados que um CPE de campus. Perda e jitter de último quilômetro ficam sub-representados. O log local continua necessário para a rede da instituição.
- Amostras do mesmo fluxo a cada 4 minutos são autocorrelacionadas. Os protocolos de split são a mitigação; um split aleatório inflaria o resultado.
- Rajada de 3 pacotes estima mal o jitter. O jitter relativo ainda assim entra em RISCO; a RFC 3550 fica reservada ao agente local, quando a rajada tiver pacotes suficientes.
- Baseline fixo de 7 dias não acompanha deriva lenta nem troca de rota. A seção 8.5 é a correção prevista; até lá, uma mudança estável de caminho pode ser rotulada como desvio extremo (já visto em `7399 → de-mdt`). MAD muito pequeno (ex. 0,09 ms) também dispara FALHA com aumento de ~1 ms.
- Sete mais sete dias cobrem um ciclo semanal em cada período, não a estabilidade entre semanas.
- A 12 minutos o futuro ainda é, em grande parte, o estado atual.
- Cinco fluxos para Bogotá foram excluídos em vez de receber mediana inventada.
- RISCO é raro. F1 macro e o suporte dessa classe precisam aparecer no relatório; rebalancear por rota ensinaria o mapa de novo.
- F1 próxima de 1 na Tarefa 3 (validação) não prova falha de equipamento: a árvore reaprende a tabela da seção 8.4, que usa as mesmas 8 colunas.

---

## 11. Critérios de sucesso

1. Nenhum fluxo de teste contribui para o próprio baseline, e nenhuma feature usa país, IP ou rota.
2. No teste temporal, o detector separa OK, RISCO e FALHA com F1 macro acima da classe majoritária, e o recall de FALHA fica explícito.
3. O preditor de 12 minutos, se for entregue, supera a persistência do estado atual no mesmo teste. Se não superar, a entrega declara o sistema como detector.
4. No teste por fluxos novos, depois do aquecimento, um caminho longo estável não colapsa em FALHA e um caminho curto degradado não colapsa em OK.
5. Exemplos auditáveis neste grupo: IQ→jp-tch estável como OK; um fluxo curto com aumento persistente como RISCO ou FALHA; timeout persistente como FALHA; um patamar novo e estável encaminhado a RECALIBRAR quando essa regra estiver ativa.
6. Dicionário e `config/` alinhados às colunas que o modelo de fato consome.
7. Tarefa 1: RFC, dicionário v0.1, `data/raw/` e `config/coleta.json` publicados; bruto sem classe.

---

## 12. Alternativas consideradas

| Alternativa | Consequência que levou à rejeição |
| --- | --- |
| Limiar global de RTT (50/100 ms) | A classe vira distância. Rota longa estável fica sempre em FALHA; rota curta pode degradar e continuar OK. |
| Um modelo só com RTT absoluto misturando todos os fluxos | O algoritmo usa o comprimento do caminho como atalho. A árvore de contraste da Tarefa 3 confirmou isso (F1 macro 0,51). |
| Um modelo separado por fluxo | Válido para um único enlace, caro em dados e manutenção para um preditor reutilizável. |
| Média e desvio-padrão como estatística do baseline | A intuição (2 e 3 sigmas) é certa; média e desvio são arrastados pelos picos. Mediana e MAD preservam a escala via 1,4826. |
| Jitter absoluto de 20/50 ms e perda de 0,5/2% como lei universal | Jitter absoluto reintroduz a distância. Perda de 0,5% não é observável em rajada de 3 pacotes. |
| Baseline de 5 dias com 15 pings a cada 5 minutos num único alvo | Adequado a um app de um enlace. Esta coleta precisa de muitos fluxos, série já existente e zero crédito. |
| Preencher timeout com 0 ms | 0 ms parece latência excelente. |
| k-means sobre o RTT, ou percentil global do lote | O alvo deixa de ser uma política operacional. |
| Split aleatório de linhas | Janelas vizinhas do mesmo fluxo caem em treino e teste. |
| Superamostrar rotas longas para “balancear” FALHA | Com limiar relativo, rota longa estável é justamente o OK que o modelo precisa ver. |
| IPv4 e IPv6 na mesma coluna `latencia_ms` | Dois regimes físicos no mesmo número. |
| Medições próprias no RIPE Atlas (`POST`) | Crédito, série curta e viés da sonda de quem coleta. |

---

## 13. Perguntas em aberto

1. A coluna RECALIBRAR entra numa re-rotulagem do Período B antes do treino, ou só no monitor em operação? Até a resposta, o treino usa as três classes já gravadas e documenta o viés de mudança de rota.
2. Os limiares (z = 2 e 3,5, aumento de 30% e 80%, jitter relativo ≥ 3, perda ≥ 10%) podem ser ajustados na validação. O teste não escolhe limiar.
3. Baseline móvel causal (somente os 14 ou 28 dias anteriores a t) substitui a ficha fixa quando houver série mais longa que 7+7.
4. Qual classificador entra no pipeline decide-se na validação, contra persistência e classe majoritária. A Tarefa 3 usou árvore CART; Random Forest permanece opção de etapa posterior.
5. No agente local, o tamanho da rajada (10 a 20 pacotes) e o uso da RFC 3550 dependem de uma coleta própria; não alteram o contrato do CSV já fechado.
6. O Protocolo B (fluxos novos) ainda não foi executado.

---

## 14. Encadeamento

| Etapa | Produz | A etapa seguinte usa |
| --- | --- | --- |
| Tarefa 1 — Coleta | JSON bruto, `medicoes_brutas.csv.gz` dos Períodos A e B, **sem classe**, dicionário v0.1, este RFC | Este bruto |
| Tarefa 2 — Baseline e rótulo | `baseline_por_fluxo.csv`, `dataset_rotulado_B.csv.gz`, `corte_temporal.json`, dicionário v0.2 | Estes rótulos e estas features |
| Divisão | Protocolo A (tempo) gravado; Protocolo B (fluxos) ainda aberto | O mesmo split em todo retreino |
| Tarefa 3 — Modelo (detector) | Árvore oficial só no treino, contraste absoluto vs relativo, relatório na validação | Teste fechado até a Tarefa 5 |
| Tarefa 5 / dashboard | Avaliação no teste; classificar medição nova com a ficha congelada | — |

Não se rotula o período que estimou o baseline. Não se sorteia linha para o teste final. A e B não são “treino” e “arquivo para alimentar o modelo”: A é a ficha; B é o dataset rotulado, do qual saem treino, validação e teste.

---

## Referências internas do grupo

| Artefato | Caminho |
| --- | --- |
| Este RFC | `docs/RFC_Preditor_Degradacao_Rede.md` |
| Diário da Tarefa 1 | [`docs/diarios/Tarefa1_Coleta_Bruta.md`](diarios/Tarefa1_Coleta_Bruta.md) |
| Dicionário v0.1 (bruto) | [`docs/dicionario_v0.1.md`](dicionario_v0.1.md) |
| Dicionário v0.2 (rótulo) | [`docs/dicionario_v0.2.md`](dicionario_v0.2.md) |
| Relatório de qualidade | [`docs/relatorio_qualidade_tarefa1.md`](relatorio_qualidade_tarefa1.md) |
| Coleta | `config/coleta.json`, `src/coletar_bruto.py`, `src/montar_tabela_bruta.py` |
| Rotulagem | `config/rotulagem.json`, `src/baseline_e_rotulo.py` |
| Árvore | `config/arvore.json`, `src/treinar_arvore.py` |
