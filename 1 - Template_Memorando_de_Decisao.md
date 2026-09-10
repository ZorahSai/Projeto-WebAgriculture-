# Memorando de Decisão — Fonte de Dados do Projeto


| Campo | Informação |
|---|---|
| Curso / Disciplina | `[Ciencia da Computação / Estrutura de Dados II]` |
| Projeto integrador | `[PREDITOR DE FALHA/RISCO EM DISPOSITIVOS DE REDE ]` |
| Orientador(a) | `[Andréa/Denise/Luis]` |
| Data de entrega desta etapa | `[07/09/2026]` |
| Integrantes do grupo | `[Apollo Moura De Sousa/Icaro Luiz Dellalo Silva/Ieda de Oliveira/João Pedro C. de Morais/Lucas Matteus Baptista de Godoy]` |

---

> Preencha cada seção com o que você encontrou na pesquisa. Não deixe nenhum campo com o texto entre colchetes — substitua pelo seu conteúdo. Toda informação levantada nas Opções A e B precisa indicar a fonte de onde veio.

## 1. Situação

[Decidir de qual fonte vamos extrair os dados para utilizar em nosso sistema]

## 2. Opção A — Dataset real

- **Origem / link:** [ Kaggle – "Network Traffic Dataset Captured through Wireshark", publicado por Deavanathan (https://www.kaggle.com/datasets/deavanathan/network-traffic-dataset-captured-through-wireshark)]
- **Formato:** [ CSV (Captured_packets.csv, 16,28 MB), captura de pacotes via Wireshark em máquina Windows, interface Wi-Fi]
- **Período coberto:** [ não informado — apenas timestamps Epoch (Unix time)]
- **Campos disponíveis:** [ 19 colunas, incluindo time, src_ip, dst_ip, protocol, packet_length, tcp_src_port, tcp_dst_port, ttl, tcp_flags, window_size, ack_rtt (RTT real do ACK)]
- **Licença de uso:** [ MIT]

**Resumo do que foi encontrado:**

O dataset "Network Traffic Dataset Captured through Wireshark", disponível no Kaggle sob licença MIT, contém uma captura real de pacotes de rede feita via Wireshark em uma máquina Windows conectada por Wi-Fi, totalizando 19 colunas e um arquivo de 16,28 MB (Captured_packets.csv). O tráfego capturado é majoritariamente TCP (78%) e TLSv1.3 (18%), com protocolos de descoberta de serviço local como MDNS, SSDP e DHCP também presentes. Não há indicação de período/data da captura, apenas timestamps em Unix time

## 3. Opção B — API do RIPE Atlas

- **Documentação consultada (link):** [https://atlas.ripe.net/docs/apis/rest-api-reference/]

- **Autenticação exigida:** [Através de uma chave de API (API Key) gerada na conta do usuário, que deve ser incluída nos parâmetros da requisição ou no cabeçalho (header) HTTP para autorizar a criação ou acesso a dados restritos.]

- **Como se cria uma medição:** [A criação é feita enviando uma requisição HTTP POST (em formato JSON) para a API. No payload (corpo da requisição), primeiro devemos definir o tipo de medição (Ping, Traceroute, DNS, TLS, HTTP, NTP); segundo, especificar o objetivo (alvo/host remoto ou endereço IP) e o tempo/frequência; e terceiro, definir quais sondas (probes) realizarão o teste.]

- **Como se consultam os resultados:** [Após a execução pelas sondas, os resultados são consultados via requisições HTTP GET direcionadas ao endpoint específico da medição (ex: /api/v2/measurements/{id}/results/), que retornará os dados em formato estruturado (JSON). Também é possível consumir os dados via WebSockets.]

**Resumo do que foi encontrado:**

A API REST do RIPE Atlas é uma interface programática voltada para interagir com a maior rede mundial de medições ativas da internet, mantida pelo RIPE NCC. Ela permite automatizar o monitoramento da infraestrutura de rede global por meio de sondas físicas e virtuais, acessando recursos públicos ou protegidos por API Keys.
A API facilita a análise e o monitoramento automatizado do desempenho e da conectividade da Internet em diferentes regiões do mundo, permitindo integrações com outros sistemas. As suas principais funções incluem:
Criação e gestão de Medições: Permite disparar testes sob demanda e gerenciar medições recorrentes via requisições HTTP programadas.
Consulta de Metadados e Status: Facilita a busca de informações detalhadas sobre a rede, como localização e disponibilidade das sondas.
Acesso a Resultados em Tempo Real: Oferece suporte a WebSockets e conexões persistentes para capturar resultados em streaming e eventos de conectividade instantaneamente, além da extração tradicional de resultados via chamadas GET para análise posterior.

## 4. Comparação

| Critério | Opção A — Dataset real | Opção B — API RIPE Atlas |
|---|---|---|
| Controle sobre a coleta |Baixo (os dados são estáticos e pré-coletados por terceiros) |Alto (permite consultar medições e sondas ativas sob demanda) |
| Diversidade geográfica |Limitada ao escopo fixo e restrito do arquivo de captura original | Altíssima (conta com uma rede global de sondas distribuídas mundialmente)|
| Custo / complexidade de implementação |Baixo (implementação direta via Pandas lendo um arquivo CSV local) |Médio/Alto (envolve requisições HTTP, tratamento de JSON aninhado e parsing de estruturas complexas) |
| Tempo até os primeiros dados estarem disponíveis |Instantâneo (assim que o download do dataset é concluído) |Rápido, porém dependente da resposta e estabilidade da API em tempo real |

## 5. Recomendação

A opção B é a mais recomendada por ter uma diversidade geográfica real, o que garante que os dados de RTT serão medidos em pontos distintos da internet

## 6. Justificativa

A Opção B foi escolhida principalmente pelo tipo de dado que sua fonte é capaz de capturar: o RIPE Atlas mede RTT, perda de pacotes e jitter entre pontos distintos da internet, via uma rede global de sondas — alinhado diretamente ao que o projeto se propõe a captar, transmissões de pacotes entre pontos remotos. Já a Opção A é uma captura de tráfego local (Wireshark), um tipo de dado diferente, além de não ter diversidade geográfica.

## 7. Riscos e limitações

Riscos
- Dependência da API: se o RIPE Atlas apresentar problemas, o sistema não consegue obter os dados. 
- Problemas de conexão: o código possui tratamento básico de erros, mas não conta com mecanismos mais completos de recuperação.  
- Dados limitados: uma única medição isolada pode não representar corretamente a qualidade da conexão. 
- Classificação rígida: por considerar pequenas perdas de pacotes mesmo quando são pequenas, pode fazer o sistema indicar uma situação de falha. 
- Dados de teste: parte da análise utiliza registros inseridos manualmente no código. 

Limitações
- Medições externas: já que o RIPE atlas tem suas medições feitas por sondas, os resultados podem representar outros pontos da internet, não do usuário específico. 
- Poucos indicadores: o sistema trabalha principalmente com latência, perda de pacotes e jitter. 
- Jitter simplificado: o cálculo considera apenas a variação entre RTTs consecutivos. 
- Amostra pequena: apenas três registros são utilizados na demonstração final. 



## 8. Contribuição Individual dos Integrantes

### Integrante 1 — `[Apollo Moura De Sousa]`
- **O que fez nesta etapa:** `[Pesquisou sobre Dataset real]`
- **Tempo dedicado (aprox.):** `[1h08min]`
- **Evidência da contribuição** *(print de conversa, rascunho, e-mail, documento compartilhado etc.)*:
`[ https://www.kaggle.com/datasets/deavanathan/network-traffic-dataset-captured-through-wireshark?resource=download]` 
`[kaggle.com/datasets/deavanathan/network-traffic-dataset-captured-through-wireshark]`

### Integrante 2 — `[Icaro Luiz Dellalo Silva]`
- **O que fez nesta etapa:** `[Redigiu o texto explicando os Riscos e limitações ]`
- **Tempo dedicado (aprox.):** `[1h]`
- **Evidência da contribuição** *(print de conversa, rascunho, e-mail, documento compartilhado etc.)*:
`[https://github.com/ZorahSai/Projeto-WebAgriculture-/blob/main/memorando-de-decisao/Riscos%20e%20Limita%C3%A7%C3%B5es.docx]` 

### Integrante 3 — `[Ieda de Oliveira]`
- **O que fez nesta etapa:** `[Fez a Comparação entre o Dataset real (Kaggle) e a API do RIPE ATLAS]`
- **Tempo dedicado (aprox.):** `[3h30]`
- **Evidência da contribuição** *(print de conversa, rascunho, e-mail, documento compartilhado etc.)*: 
`[Subiu 2 arquivos do google Colab no repositório, pasta Memorando]`
`[https://github.com/ZorahSai/Projeto-WebAgriculture-/tree/main/memorando-de-decisao]` 
`[arquivo "Opção A" refere se ao teste do Dataset real (Kaggle)]`
`[arquivo "Opção B" refere se ao teste do API do RIPE ATLAS]`
`[ https://www.kaggle.com/datasets/deavanathan/network-traffic-dataset-captured-through-wireshark?resource=download]`
### Integrante 4 — `[João Pedro C. de Morais]`
- **O que fez nesta etapa:** `[Pesquisou sobre a API do RIPE ATLAS]`
- **Tempo dedicado (aprox.):** `[2h30]`
- **Evidência da contribuição** *(print de conversa, rascunho, e-mail, documento compartilhado etc.)*: 
`[https://atlas.ripe.net/]` 
`[https://atlas.ripe.net/docs/apis/rest-api-manual/]`

### Integrante 5 — `[Lucas Matteus Baptista de Godoy ]`
- **O que fez nesta etapa:** `[Desenvolveu o texto referente a Recomendação e a Justificativa]`
- **Tempo dedicado (aprox.):** `[40min]`
- **Evidência da contribuição** *(print de conversa, rascunho, e-mail, documento compartilhado etc.)*: 
`[https://github.com/ZorahSai/Projeto-WebAgriculture-/blob/main/memorando-de-decisao/Recomenda%C3%A7%C3%A3o_Justificativa.md]` 
`[https://github.com/ZorahSai/Projeto-WebAgriculture-/tree/main/memorando-de-decisao]`

---
## Fontes consultadas

1. [ https://www.kaggle.com/datasets/deavanathan/network-traffic-dataset-captured-through-wireshark?resource=download ]
2. [ https://atlas.ripe.net/]
3. [ https://atlas.ripe.net/docs/apis/rest-api-manual/]
