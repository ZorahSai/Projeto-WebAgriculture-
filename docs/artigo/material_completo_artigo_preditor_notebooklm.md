# Pacote completo — artigo preditor de redes (WebAgriculture)

Documento único para o NotebookLM: use este arquivo para gerar **vídeo explicativo** e **mapa mental**.

**Idioma:** português do Brasil.  
**Público:** os 5 integrantes do grupo (Apollo, Icaro, Ieda, João Pedro, Lucas), estudantes, nível iniciante.  
**Tom do vídeo:** didático, simples, sem fórmulas. Não misturar o detector das Tarefas 1–4 com o preditor do artigo.  
**Mapa mental:** use a árvore da Parte 0 como esqueleto; os detalhes vêm das Partes 1 e 2.

**Artigo:** https://iedahirari.github.io/artigo-preditor-redes/  
**Repo do artigo:** https://github.com/iedahirari/artigo-preditor-redes  
**Repo do projeto:** https://github.com/ZorahSai/Projeto-WebAgriculture-  
**Apresentação:** até 8 minutos, abrindo o HTML (sem slides).  
**Autores (ordem alfabética):** Apollo Moura De Sousa, Icaro Luiz Dellalo Silva, Ieda de Oliveira, João Pedro C. de Morais, Lucas Matteus Baptista de Godoy. Publicado em 18/10/2026.

---

# Parte 0 — Esqueleto para o mapa mental

- Artigo preditor de degradação de rede
  - Em uma frase
    - Pergunta: olhando o ping de agora, a classe daqui a 12 minutos será OK, RISCO ou FALHA?
    - Régua: persistência (“vai continuar como agora”)
    - Conclusão: quase não dá prever o início de FALHA
    - Recomendação: árvore como detector de curto prazo, não bola de cristal
  - Dois trabalhos que não se misturam
    - GitHub Tarefas 1–4 = detector da classe atual
    - Artigo = tentativa de preditor 12 minutos à frente
    - Mesmos pings RIPE Atlas nos dois
  - Conceitos
    - Ping / RTT (alto não é falha sozinho)
    - Fluxo (92 caminhos)
    - OK / RISCO / FALHA (política do projeto, não ticket de roteador)
    - Baseline (semana 1 = normal; semana 2 = rótulos)
    - 8 atributos relativos (sem IP, país, RTT em ms)
    - Alvo = classe 3 medições depois (~12 min)
    - Persistência
    - F1 macro (não acurácia)
    - Início de FALHA (1.990 no teste)
    - Overfitting
  - Três modelos
    - Árvore de decisão (perguntas, 16 folhas, F1 0,759, 0,56 ms)
    - Random Forest (voto em paralelo, F1 0,763, 15,7 ms)
    - XGBoost (fila e correção, F1 0,765, treino 7 s)
  - Experimento
    - RIPE Atlas, 92 fluxos
    - Split no tempo (treino / validação / teste uma vez)
    - Classe muda só 13,5% das vezes
  - Números do teste (66.702 medições)
    - XGBoost 0,765 vs persistência 0,753 (+0,012)
    - Modelos empatam entre si (diferença 0,006)
    - Inícios de FALHA: 4 em 1.990
    - Alarmes falsos: ~446 vs 2.008 da persistência
    - Caminhos longos fáceis; curtos difíceis
  - Recomendação e limitações
    - Escolha: árvore (auditar + latência)
    - Alternativa: floresta/XGBoost se a meta for menos alarme falso
    - Nenhum antecipa FALHA com estes 8 atributos
    - Rótulo é política; janela curta; anchors ≠ campus
  - Apresentação de 8 minutos no HTML
    - Apollo: problema + 4 números do topo
    - Icaro: árvore e Figura 1
    - Ieda: floresta e XGBoost
    - João Pedro: experimento
    - Lucas: resultados, recomendação e fecho

---

# Parte 1 — Material de estudo

Para quem: os 5 integrantes do WebAgriculture.  
Leia isto antes do roteiro. Não precisa decorar o HTML inteiro. Na apresentação, cada pessoa fala em cima da seção do artigo que já está na tela; só rola para baixo.

## 1. Em uma frase

O artigo pergunta: **olhando o ping de agora, dá para saber se daqui a 12 minutos o caminho estará OK, RISCO ou FALHA?**

Comparam três programas que “aprendem com exemplos” (árvore, floresta e XGBoost) com a regra mais burra possível: **“daqui a 12 minutos vai estar como está agora”** (isso se chama **persistência**).

Conclusão do artigo: **quase não dá.** Os modelos empatam entre si e ganham muito pouco da persistência. **Ninguém avisa o início de uma FALHA.** O que eles fazem melhor é perceber quando uma falha **já está acabando**, e assim disparam menos alarme falso.

Por isso o grupo recomenda a **árvore de decisão** não como “bola de cristal”, e sim como **detector com um olhinho no curto prazo**: rápida, dá para ler as regras, e quase tão boa quanto os modelos grandes.

## 2. Não misture os dois trabalhos

| | Projeto no GitHub (Tarefas 1–4) | Artigo |
|---|---|---|
| Pergunta | Qual é a classe **desta** medição? | Qual será a classe **daqui a 12 minutos**? |
| Nome honesto | **Detector** | Tentativa de **preditor** |
| Modelos | Uma árvore (Tarefas 3 e 4) | Árvore + Random Forest + XGBoost |
| Régua | Validação; teste ainda fechado na Tarefa 4 | Persistência + teste único |
| Dados | Os mesmos pings RIPE Atlas do grupo | Os mesmos, com alvo = classe 3 medições à frente |

Se alguém perguntar “vocês já preveem o futuro?”: **não com confiança.** O artigo mostra isso com números.

A F1 perto de 1,0 das Tarefas 3 e 4 é o detector **reaprendendo a regra da classe atual**. A F1 ~0,76 do artigo é prever a classe **futura**. São perguntas diferentes.

## 3. Palavras que todo mundo precisa saber

**Ping / RTT.** Tempo de ida e volta do pacote. RTT alto **não** é falha sozinho: Iraque→Japão ~315 ms todo dia pode ser saudável; Auckland de 1 ms para 12 ms pode ser problema.

**Fluxo.** Um caminho: origem → destino. No artigo: 92 fluxos (os que tinham baseline).

**OK / RISCO / FALHA.** Nada a fazer / observar / investigar. A classe vem da **regra do projeto** (desvio em relação ao normal daquele fluxo), não de um log de roteador quebrado.

**Baseline.** Primeira semana: “o que é normal neste fluxo” (mediana e MAD). Segunda semana: as medições que entram no modelo.

**Os 8 atributos.** Tudo relativo ao normal do fluxo. Sem país, sem IP, sem RTT em milissegundos (senão o modelo aprende geografia).

- `z_robusto` — quantos “desvios típicos” o RTT está acima do normal
- `aumento_pct` — % acima do normal
- `jitter_relativo` — instabilidade agora ÷ instabilidade típica
- `perda_pct`, `timeout_atual` — perda nesta rajada
- `n5_*` — nas últimas 5 medições: timeouts, aumentos > 80%, desvios moderados

**Alvo do artigo.** Classe do **mesmo fluxo 3 medições depois** (3 × 240 s ≈ 12 min).

**Persistência.** Previsão = classe de agora. Acerta sempre que nada muda (a classe só muda em 13,5% das vezes). Erra **todas** as mudanças. Não acerta **nenhum** início de FALHA.

**F1 macro.** Média do F1 de OK, RISCO e FALHA, com o **mesmo peso** para as três. Não use acurácia: dizer sempre OK já acerta ~78% e não serve.

**Início de FALHA.** Agora **não** está FALHA, daqui a 12 min **estará**. São 1.990 no teste. É o que um preditor de verdade precisaria acertar.

**Overfitting.** O modelo decora o treino e piora em dado novo. Na árvore: profundidade enorme → F1 0,998 no treino e 0,618 na validação.

## 4. Os três modelos (ideia, sem fórmula)

### Árvore de decisão

Faz perguntas do tipo “`z_robusto` ≤ 3,4?” até chegar numa folha (OK, RISCO ou FALHA).

Mesmo com 3 níveis, já aprende regras que um operador entende:

- Desvio grande e estável → a FALHA continua.
- Desvio grande com jitter alto e sem repetição → era um pico, tende a voltar a OK.
- 77% das medições: a rede está no próprio normal → OK.

**Prós:** dá para ler; muito rápida (0,56 ms por ping).  
**Contras:** se ficar profunda demais, decora.  
**No artigo:** profundidade 4, 16 folhas. F1 no teste **0,759**.

### Random Forest (floresta)

Muitas árvores, cada uma treina num sorteio dos dados e só vê alguns atributos por pergunta. No fim, **votação**. Uma árvore sozinha oscila; a média oscila menos (reduz variância).

**Prós:** mais estável.  
**Contras:** lenta para um ping de cada vez (15,7 ms); não dá para mostrar o caminho de um alerta.  
**No artigo:** F1 **0,763**.

### XGBoost (boosting)

Árvores **em fila**: cada uma tenta corrigir o erro da anterior. A previsão é a **soma**.

**Prós:** em tabelas, costuma ser o mais forte.  
**Contras:** mais ajuste; treino mais lento (7 s).  
**No artigo:** F1 **0,765** — o maior, por um fio.

Frase para guardar: **floresta = várias árvores em paralelo (voto). Boosting = árvores em sequência (correção).**

## 5. Números para não errar na fala

Quatro números do topo do HTML (a tese do artigo):

- **+0,012** de F1 macro do melhor modelo (XGBoost 0,765) sobre a persistência (0,753)
- **4 de 1.990** inícios de FALHA anunciados com 12 minutos de antecedência
- **446** alarmes falsos de FALHA na Random Forest e no XGBoost, contra 2.008 da persistência
- **0,56 ms** latência da árvore por medição (XGBoost 1,5 ms, Random Forest 15,7 ms)

Teste: **66.702** medições.

| Modelo | F1 macro | Inícios de FALHA anunciados | Alarmes falsos de FALHA |
|---|---|---|---|
| Árvore | 0,759 | 4 de 1.990 | 650 |
| Random Forest | 0,763 | 3 de 1.990 | 446 |
| XGBoost | 0,765 | 4 de 1.990 | 446 |
| Persistência | 0,753 | 0 de 1.990 | 2.008 |

- Melhor modelo vs persistência: **+0,012** de F1. Pouquinho.
- Três modelos entre si: diferença **0,006** — ruído de uma execução.
- Caminhos **longos** são fáceis (~0,85 de F1). **Curtos** são difíceis (~0,54); neles a persistência até ganha.
- Ninguém trata caminho longo como problema → os atributos relativos funcionaram.
- O ganho real dos modelos está no **fim** das falhas (cortar alarme quando o pico já vai passar), não no **começo**.

## 6. A recomendação (o “e daí?”)

**Escolhemos a árvore**, como detector de curto prazo, **não** como preditor de falha futura.

Por quê?

1. Quase o mesmo F1 do XGBoost.
2. Única que o operador lê (“RTT a mais de 3,4 desvios e jitter baixo → a falha deve continuar”).
3. Mais rápida.

Se o objetivo fosse **menos alarme falso**, floresta ou XGBoost (446 vs 650).  
Se o objetivo fosse **avisar FALHA 12 min antes**, **nenhum** resolve com estes 8 atributos.

O RFC do projeto já dizia: sem ganho claro sobre a persistência, declara-se **detector**.

O exemplo da professora (horizonte ~4 minutos e janelas mais longas) conseguiu anunciar 14,6% dos inícios de FALHA. Com 8 atributos e 12 minutos, esse ganho desaparece.

## 7. Limitações (se o professor perguntar)

- O rótulo é **política**, não ticket de roteador. Os modelos aprendem a prever essa regra.
- Uma semente, um corte no tempo — os 0,006 entre modelos não são “vitória”.
- Só 5 medições de memória; falha que começa sem aviso não aparece.
- Mudança de rota (ex. 7 ms → 13 ms estável) a regra marca FALHA o tempo todo. Isso infla a persistência das falhas.
- Período curto: uma semana de rótulos.
- Anchors do RIPE não são a rede do campus (datacenters bem conectados).

## 8. Como estudar em 30 minutos

1. Ler as seções 1–6 deste guia (10 min).
2. Abrir o artigo e só olhar: Figura 1 (árvore), Figura 6 (overfitting), Tabela 3 (resultados), o box de Recomendação (10 min).
3. Ler **só o seu bloco** do roteiro em voz alta, com cronômetro (5–8 min).
4. Combinar a passagem de um integrante para o outro (quem fala a última frase).

## 9. Respostas prontas

**“Então o artigo fracassou?”**  
Não. Mostrar que 12 minutos com estes atributos **não antecipam FALHA** é o resultado. O RFC já previa: sem ganho sobre a persistência, o sistema é detector.

**“Por que não usaram RTT em ms?”**  
Porque o modelo aprenderia “caminho longo = problema”. O projeto inteiro existe para evitar isso.

**“Por que não Random Forest, se tem menos alarme falso?”**  
Critério do grupo: **auditar o alerta** e latência. Se a prioridade fosse fadiga de alerta, a floresta ganharia — o artigo diz isso.

**“Isso vale para a rede da faculdade?”**  
Não sabemos. Anchors são datacenters. Campus pode ser outro comportamento. Limitação explícita.

**“A Tarefa 4 não tinha F1 1,0?”**  
Aquela F1 é o **detector da classe atual** reaprendendo a regra. O artigo prevê a classe **futura**. São perguntas diferentes; o F1 cai para ~0,76.

---

# Parte 2 — Roteiro de apresentação no HTML (máximo 8 minutos)

Não há slides. A tela inteira é o artigo:

- Online: https://iedahirari.github.io/artigo-preditor-redes/
- Local: arquivo `artigo preditor de redes.html` (se as figuras não carregarem, use o link)

**5 pessoas × cerca de 1 min 25 s.** Se alguém passar de 1 min 40 s, o grupo estoura 8 minutos.

Falem **devagar**, um número por vez. **Não leiam o artigo.** O HTML é o quadro; vocês apontam e explicam.

## Quem aponta o quê (ordem do próprio artigo)

| # | Quem | Onde o HTML deve estar | Tempo |
|---|---|---|---|
| 1 | Apollo Moura De Sousa | Título + 4 números do topo + “O problema” | 1 min 25 s |
| 2 | Icaro Luiz Dellalo Silva | Modelo 1 · Árvore de Decisão (Figura 1) | 1 min 25 s |
| 3 | Ieda de Oliveira | Random Forest + XGBoost (Figuras 2 e 3) | 1 min 25 s |
| 4 | João Pedro C. de Morais | O experimento (Tabela 2 + Figura 5) | 1 min 25 s |
| 5 | Lucas Matteus Baptista de Godoy | Resultados (Tabela 3) + Recomendação | 1 min 40 s |

A ordem das falas **é a ordem da página**. Só rola para baixo. Ninguém volta.

## Como abrir a tela (2 minutos antes)

1. Abra o artigo no Chrome ou Edge, tela cheia (F11).
2. Zoom 125% (no notebook, 150% se a sala for grande).
3. Fiquem no topo. Os quatro números (+0,012, 4 de 1.990, 446, 0,56 ms) precisam caber na tela junto com o título.
4. Não abra as caixas cinzas “Aprofundamento” (Gini, fórmulas). Não role o código Python. Não abra as Referências.
5. Um celular marca o tempo. Aos 1:20 de cada bloco (no Lucas, 1:30), levanta a mão.

Quem controla o scroll: quem está falando. No último segundo da fala, role até o título da seção do próximo e solte o mouse.

Figuras largas (Figura 1, matrizes): deslize a barra dentro da figura, ou clique nela para abrir grande. Não gaste tempo nisso no ensaio.

## Mapa da página no ensaio

Role nesta ordem e pare nestes pontos:

- topo → Apollo
- seção O problema → Apollo (fim)
- seção Árvore de Decisão → Icaro (Figura 1)
- seção Random Forest → Ieda (Figura 2)
- seção XGBoost → Ieda (Figura 3)
- seção O experimento → João (Tabela 2, Figura 5)
- seção Resultados no teste → Lucas (Tabela 3)
- seção Recomendação → Lucas (box)

Se alguém se perder, o índice do artigo tem exatamente esses nomes. Clique no índice só se o scroll falhar.

## Abertura — 15 segundos — Apollo, ainda no topo

Aponte o título. Não leia o subtítulo inteiro.

Fala:

Somos o grupo WebAgriculture. Este artigo usa os pings do nosso projeto integrador para testar se dá para prever a qualidade de um caminho da internet 12 minutos antes. Spoiler: quase não dá — e isso também é resultado.

## Bloco 1 — Apollo — o problema — 1 min 25 s

Tela: topo. Aponte com o cursor os quatro números, um de cada vez, depois role só até o título “O problema: avisar antes que o caminho degrade”. Pare no segundo parágrafo (OK / RISCO / FALHA). Não desça até a árvore.

Fala:

Estes quatro números já são a tese. O melhor modelo ganha só +0,012 de F1 da regra burra. Dos 1.990 inícios de falha, anunciamos 4. O que os modelos fazem bem é cortar alarme falso: 446 contra 2.008. E a árvore responde em meio milissegundo.

Quem opera uma rede quer saber se o caminho está OK, RISCO ou FALHA. RTT alto sozinho não é falha: Iraque–Japão com 315 ms pode estar saudável; Auckland de 1 ms para 12 ms pode estar ruim. A classe compara o ping com o normal daquele mesmo fluxo.

Saber a classe de agora é o detector do nosso GitHub. Aqui a pergunta muda: olhando só o agora, qual será a classe daqui a 12 minutos? A régua é a persistência: “vai continuar como está”.

Icaro mostra o primeiro modelo, a árvore.

Não fale: MAD, z_robusto, Período A/B, 97 vs 92 fluxos.  
Não role: índice, autores, Referências.

## Bloco 2 — Icaro — árvore de decisão — 1 min 25 s

Tela: clique no título “Modelo 1 · Árvore de Decisão” (ou role até ele). Deixe visíveis os três bullets e, se couber, a Figura 1. Se a figura estiver cortada, deslize um pouco para a direita só para mostrar raiz → folhas. Não abra “Aprofundamento: Gini”. Não leia “nó, folha, poda”.

Fala:

Uma árvore é uma sequência de perguntas. Cada caminho termina numa folha: OK, RISCO ou FALHA.

Mesmo com 3 níveis, ela já diz coisas que um operador entende. Desvio grande e estável → a FALHA continua. Desvio grande com jitter alto e sem repetição → era um pico, tende a voltar a OK. O resto do tempo, a rede está no próprio normal — 77% das medições.

Aponte a Figura 1, mesmo que pequena. Verde, amarelo, vermelho nas folhas: a previsão para daqui a 12 minutos, não a classe de agora.

Se a árvore cresce demais, ela decora o treino: F1 0,998 no passado e 0,618 em dado novo. Por isso a árvore que usamos no artigo tem profundidade 4 e 16 folhas. É a mais rápida e a única que dá para auditar pergunta por pergunta.

Ieda mostra os outros dois, que juntam muitas árvores.

Não fale: Gini, ccp_alpha, scikit-learn.  
Não clique: zoom da figura em outra aba (perde tempo).

## Bloco 3 — Ieda — floresta e boosting — 1 min 25 s

Tela: role para “Modelo 2 · Random Forest”. Aponte a Figura 2 (número de árvores × F1). Depois role para “Modelo 3 · XGBoost” e pare na Figura 3 (dois diagramas: bagging à esquerda, boosting à direita). Não fique na Figura 4 (taxas de aprendizado). Não leia a Tabela 1 linha a linha — se der, 5 segundos no título “Os três lado a lado” no fim da fala.

Fala:

Random Forest: dezenas de árvores diferentes e votação. Cada uma vê um sorteio dos dados. Uma árvore sozinha oscila; a média oscila menos. Com mais árvores, a faixa de F1 fica estreita. No teste, F1 0,763. Preço: 15,7 ms por ping e não dá para mostrar o caminho de um alerta.

XGBoost: as árvores entram em fila. Cada uma tenta corrigir o erro da anterior. A previsão é a soma. F1 0,765, o maior. Treino mais lento: 7 segundos.

Frase única: floresta = paralelo e voto. Boosting = fila e correção.

Os três usam os mesmos dados e o mesmo esforço de ajuste. João Pedro mostra como o experimento foi montado.

Não fale: bootstrap, fórmula de variância, early stopping, 452 árvores, SHAP, Figura 4.

## Bloco 4 — João Pedro — o experimento — 1 min 25 s

Tela: role para “O experimento”. Mostre em sequência, sem parar no código:

1. Primeiro parágrafo (RIPE Atlas, 92 fluxos)
2. Tabela 2 (os 8 atributos) — aponte só a frase abaixo: RTT em ms, país e IP ficam de fora
3. Figura 5 (quase tudo OK)
4. O parágrafo do 13,5% e dos 1.990 inícios de FALHA

Pule “O código, em três trechos” inteiro. Pule a Figura 6 (overfitting) — o Icaro já falou nisso.

Fala:

Dados: pings públicos do RIPE Atlas, os mesmos do nosso GitHub. 92 fluxos. Primeira semana só para o normal de cada caminho. Segunda semana rotulada. Os modelos não veem IP, país nem RTT em milissegundos — senão aprenderiam geografia.

O alvo é a classe 3 medições depois — 12 minutos. Quase 80% é OK. A classe só muda em 13,5% das vezes. Por isso a persistência é dura: acerta sempre que nada muda.

Não sorteamos linhas. Treino, validação e teste são fatias de tempo. O teste foi olhado uma vez.

Não usamos acurácia: um modelo que só diz OK parece bom e não detecta falha. A métrica é F1 macro: as três classes pesam igual.

Tem 1.990 inícios de FALHA no teste: agora não é FALHA, daqui a 12 minutos será. Um preditor de verdade precisaria acertar isso. Lucas mostra o que aconteceu.

Não fale: 227.112 pares, códigos F01–F92, 12 combinações, Python 3.14, blocos de código.

## Bloco 5 — Lucas — resultados, recomendação e fecho — 1 min 40 s

Tela: role para “Resultados no teste”. Deixe a Tabela 3 ocupando o meio da tela. Aponte:

- coluna F1 macro (0,759 / 0,763 / 0,765 / 0,753)
- coluna Início de FALHA (tudo 0,002 ou 0)
- coluna Alarmes falsos (650 / 446 / 446 / 2.008)

Se sobrar 10 s, desça até as três bullets (“Os três empatam…”, “Nenhum modelo prevê…”, “O ganho está no fim…”). Não abra matrizes (Figura 7), geografia nem importância.

No último meio minuto, role para o box “Recomendação”. Feche em cima do box, sem descer em Limitações.

Fala:

No teste, os três modelos empatam e ganham pouco da persistência: 0,765 contra 0,753. A diferença entre árvore, floresta e XGBoost é 0,006 — pequena demais para coroar um campeão.

Nenhum modelo prevê o início de uma FALHA. Dos 1.990 inícios, o melhor anunciou 4. Olhando só o agora e as últimas 5 medições, não há sinal de que um caminho saudável vai quebrar em 12 minutos.

O ganho é outro: os modelos percebem quando a falha vai passar e cortam alarmes falsos de 2.008 para cerca de 446. Em troca, perdem mais falhas que continuam.

Por isso escolhemos a árvore: quase o mesmo F1, 0,56 ms por ping, e o operador lê as 16 folhas. Não é preditor de falha futura. É um detector com previsão de curto prazo.

Se o objetivo fosse menos fadiga de alerta, iríamos de floresta ou XGBoost. Se fosse antecipar FALHA, nenhum dos três resolve — janelas mais longas, como no exemplo da professora, e talvez um horizonte menor.

Obrigado. Ficamos à disposição para perguntas.

Não fale: Tabela 5, SHAP, “como reproduzir”.

## Cronômetro no dia

Alguém que não está falando marca o tempo e levanta a mão aos 1:20 (Lucas 1:30).

Ensaio único: abrir o HTML, ler este roteiro em voz alta uma vez, com o scroll de verdade. Se passar de 8:00, cortar exemplos, não números. Não ensaiem as perguntas. Na pergunta, não saiam caçando a seção. Respondam de pé. Só voltem no HTML se o professor pedir para ver um número.

---

# Parte 3 — Pedido ao NotebookLM

Ao gerar o **vídeo**: explique o artigo como aula curta para o grupo. Comece pela pergunta dos 12 minutos, contraste detector versus preditor, explique persistência e F1 macro em linguagem simples, apresente os três modelos sem fórmulas, mostre os quatro números do topo, feche com a recomendação da árvore. Não invente métricas. Não diga que o grupo “prevê falhas com sucesso”.

Ao gerar o **mapa mental**: use a Parte 0 como ramos principais. Um ramo deve ser “dois trabalhos” (detector GitHub versus artigo). Outro ramo deve ser “apresentação de 8 minutos” com os cinco integrantes.
