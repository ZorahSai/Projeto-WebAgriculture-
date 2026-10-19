# Roteiro de apresentação — artigo no HTML (máximo 8 minutos)

**Não há slides.** A tela inteira é o artigo:

- Online: https://iedahirari.github.io/artigo-preditor-redes/
- Local: `Downloads/artigo preditor de redes.html` (se as figuras não carregarem, use o link)

**5 pessoas × ~1 min 25 s.** Se alguém passar de 1 min 40 s, o grupo estoura 8 minutos.

Falem **devagar**, um número por vez. **Não leiam o artigo.** O HTML é o quadro; vocês apontam e explicam.

---

## Quem aponta o quê (ordem do próprio artigo)

| # | Quem | Onde o HTML deve estar | Tempo |
|---|---|---|---|
| 1 | Apollo Moura De Sousa | Título + 4 números do topo + **O problema** | 1 min 25 s |
| 2 | Icaro Luiz Dellalo Silva | **Modelo 1 · Árvore de Decisão** (Figura 1) | 1 min 25 s |
| 3 | Ieda de Oliveira | **Random Forest** + **XGBoost** (Figuras 2 e 3) | 1 min 25 s |
| 4 | João Pedro C. de Morais | **O experimento** (Tabela 2 + Figura 5) | 1 min 25 s |
| 5 | Lucas Matteus Baptista de Godoy | **Resultados** (Tabela 3) + **Recomendação** | 1 min 40 s |

A ordem das falas **é a ordem da página**. Só rola para baixo. Ninguém volta.

---

## Como abrir a tela (2 minutos antes)

1. Abra o artigo **no Chrome ou Edge**, tela cheia (`F11`).
2. Zoom **125%** (no notebook, 150% se a sala for grande). O menu “Neste artigo” some um pouco — não tem problema; vocês não vão usar o índice.
3. Fiquem **no topo**. Os quatro números (`+0,012`, `4 de 1.990`, `446`, `0,56 ms`) precisam caber na tela junto com o título.
4. **Não** abra as caixas cinzas “Aprofundamento” (Gini, fórmulas). **Não** role o código Python. **Não** abra as Referências.
5. Um celular marca o tempo. Aos **1:20** de cada bloco (no Lucas, **1:30**), levanta a mão.

**Quem controla o scroll:** quem está falando. No último segundo da fala, role até o título da seção do próximo e solte o mouse.

Figuras largas (Figura 1, matrizes): deslize a barra **dentro** da figura, ou clique nela para abrir grande. Não gaste tempo nisso no ensaio.

---

## Antes de começar (15 segundos — Apollo, ainda no topo)

Aponte o título. Não leia o subtítulo inteiro.

> “Somos o grupo WebAgriculture. Este artigo usa os pings do nosso projeto integrador para testar se dá para **prever** a qualidade de um caminho da internet **12 minutos antes**. Spoiler: quase não dá — e isso também é resultado.”

---

## 1. Apollo — o problema (1 min 25 s)

**Tela:** topo. Aponte com o cursor os **quatro números**, um de cada vez, depois role só até o título **“O problema: avisar antes que o caminho degrade”**. Pare no segundo parágrafo (OK / RISCO / FALHA). Não desça até a árvore.

**Fala:**

> Estes quatro números já são a tese. O melhor modelo ganha só **+0,012** de F1 da regra burra. Dos **1.990** inícios de falha, anunciamos **4**. O que os modelos fazem bem é cortar alarme falso: **446** contra **2.008**. E a árvore responde em **meio milissegundo**.
>
> Quem opera uma rede quer saber se o caminho está **OK, RISCO ou FALHA**. RTT alto sozinho não é falha: Iraque–Japão com 315 ms pode estar saudável; Auckland de 1 ms para 12 ms pode estar ruim. A classe compara o ping com o **normal daquele mesmo fluxo**.
>
> Saber a classe **de agora** é o detector do nosso GitHub. Aqui a pergunta muda: olhando **só o agora**, qual será a classe **daqui a 12 minutos**? A régua é a **persistência**: “vai continuar como está”.
>
> Icaro mostra o primeiro modelo, a árvore.

**Não fale:** MAD, z_robusto, Período A/B, 97 vs 92 fluxos.  
**Não role:** índice, autores, Referências.

---

## 2. Icaro — árvore de decisão (1 min 25 s)

**Tela:** clique no título **“Modelo 1 · Árvore de Decisão”** (ou role até ele). Deixe visíveis os **três bullets** e, se couber, a **Figura 1**. Se a figura estiver cortada, deslize um pouco para a direita só para mostrar raiz → folhas. **Não** abra “Aprofundamento: Gini”. **Não** leia “nó, folha, poda”.

**Fala:**

> Uma árvore é uma sequência de perguntas. Cada caminho termina numa folha: OK, RISCO ou FALHA.
>
> Mesmo com **3 níveis**, ela já diz coisas que um operador entende. *(aponte os bullets)* Desvio grande e estável → a FALHA **continua**. Desvio grande com jitter alto e sem repetição → era um **pico**, tende a voltar a OK. O resto do tempo, a rede está no próprio normal — **77%** das medições.
>
> *(aponte a Figura 1, mesmo que pequena)* Verde, amarelo, vermelho nas folhas: a previsão para daqui a 12 minutos, não a classe de agora.
>
> Se a árvore cresce demais, ela **decora** o treino: F1 0,998 no passado e 0,618 em dado novo. Por isso a árvore que usamos no artigo tem profundidade **4** e **16 folhas**. É a mais rápida e a única que dá para auditar pergunta por pergunta.
>
> Ieda mostra os outros dois, que juntam muitas árvores.

**Não fale:** Gini, `ccp_alpha`, scikit-learn.  
**Não clique:** zoom da figura em outra aba (perde tempo).

---

## 3. Ieda — floresta e boosting (1 min 25 s)

**Tela:** role para **“Modelo 2 · Random Forest”**. Aponte a **Figura 2** (número de árvores × F1). Depois role para **“Modelo 3 · XGBoost”** e pare na **Figura 3** (dois diagramas: bagging à esquerda, boosting à direita). **Não** fique na Figura 4 (taxas de aprendizado). **Não** leia a Tabela 1 linha a linha — se der, 5 segundos no título **“Os três lado a lado”** no fim da fala.

**Fala:**

> **Random Forest:** dezenas de árvores **diferentes** e **votação**. Cada uma vê um sorteio dos dados. Uma árvore sozinha oscila; a média oscila menos. *(Figura 2)* Com mais árvores, a faixa de F1 fica estreita. No teste, F1 0,763. Preço: **15,7 ms** por ping e **não dá** para mostrar o caminho de um alerta.
>
> **XGBoost:** as árvores entram **em fila**. Cada uma tenta corrigir o erro da anterior. A previsão é a **soma**. *(Figura 3: lado direito)* F1 0,765, o maior. Treino mais lento: 7 segundos.
>
> Frase única: floresta = **paralelo e voto**. Boosting = **fila e correção**.
>
> Os três usam os mesmos dados e o mesmo esforço de ajuste. João Pedro mostra como o experimento foi montado.

**Não fale:** bootstrap, ρσ², early stopping, 452 árvores, SHAP, Figura 4.

---

## 4. João Pedro — o experimento (1 min 25 s)

**Tela:** role para **“O experimento”**. Mostre em sequência, sem parar no código:

1. Primeiro parágrafo (RIPE Atlas, 92 fluxos)  
2. **Tabela 2** (os 8 atributos) — aponte só a frase abaixo: RTT em ms, país e IP ficam de fora  
3. **Figura 5** (quase tudo OK)  
4. O parágrafo do **13,5%** e dos **1.990 inícios de FALHA**

Pule **“O código, em três trechos”** inteiro. Pule a **Figura 6** (overfitting) — o Icaro já falou nisso.

**Fala:**

> Dados: pings públicos do **RIPE Atlas**, os mesmos do nosso GitHub. 92 fluxos. Primeira semana só para o **normal** de cada caminho. Segunda semana rotulada. Os modelos **não** veem IP, país nem RTT em milissegundos — senão aprenderiam geografia. *(Tabela 2)*
>
> O alvo é a classe **3 medições depois** — 12 minutos. *(Figura 5)* Quase 80% é OK. A classe só muda em **13,5%** das vezes. Por isso a persistência é dura: acerta sempre que nada muda.
>
> Não sorteamos linhas. Treino, validação e teste são **fatias de tempo**. O teste foi olhado **uma vez**.
>
> Não usamos acurácia: um modelo que só diz OK parece bom e não detecta falha. A métrica é **F1 macro**: as três classes pesam igual.
>
> Tem **1.990 inícios de FALHA** no teste: agora não é FALHA, daqui a 12 minutos será. Um preditor de verdade precisaria acertar isso. Lucas mostra o que aconteceu.

**Não fale:** 227.112 pares, F01–F92, 12 combinações, Python 3.14, blocos de código.

---

## 5. Lucas — resultados, recomendação e fecho (1 min 40 s)

**Tela:** role para **“Resultados no teste”**. Deixe a **Tabela 3** ocupando o meio da tela. Aponte:

- coluna **F1 macro** (0,759 / 0,763 / 0,765 / 0,753)
- coluna **Início de FALHA** (tudo 0,002 ou 0)
- coluna **Alarmes falsos** (650 / 446 / 446 / 2.008)

Se sobrar 10 s, desça até as **três bullets** (“Os três empatam…”, “Nenhum modelo prevê…”, “O ganho está no fim…”). **Não** abra matrizes (Figura 7), geografia nem importância.

No último meio minuto, role para o box verde **“Recomendação”**. Feche **em cima do box**, sem descer em Limitações.

**Fala:**

> No teste, os três modelos **empatam** e ganham **pouco** da persistência: 0,765 contra 0,753. A diferença entre árvore, floresta e XGBoost é 0,006 — pequena demais para coroar um campeão.
>
> **Nenhum modelo prevê o início de uma FALHA.** Dos 1.990 inícios, o melhor anunciou **4**. Olhando só o agora e as últimas 5 medições, não há sinal de que um caminho saudável vai quebrar em 12 minutos.
>
> O ganho é outro: os modelos percebem quando a falha **vai passar** e cortam alarmes falsos de 2.008 para cerca de **446**. Em troca, perdem mais falhas que **continuam**.
>
> *(box Recomendação)* Por isso **escolhemos a árvore**: quase o mesmo F1, 0,56 ms por ping, e o operador lê as 16 folhas. Não é preditor de falha futura. É um **detector com previsão de curto prazo**.
>
> Se o objetivo fosse menos fadiga de alerta, iríamos de floresta ou XGBoost. Se fosse antecipar FALHA, nenhum dos três resolve — janelas mais longas, como no exemplo da professora, e talvez um horizonte menor.
>
> Obrigado. Ficamos à disposição para perguntas.

**Não fale:** Tabela 5, SHAP, “como reproduzir”.

---

## Mapa da página (para o ensaio)

Role nesta ordem e **pare** nestes âncoras. Cada pessoa ensaia só o próprio trecho.

```
topo (#)                  → Apollo
#introducao               → Apollo (fim)
#arvore                   → Icaro   (Figura 1)
#random-forest            → Ieda    (Figura 2)
#xgboost                  → Ieda    (Figura 3)
#experimento              → João    (Tabela 2, Figura 5)
#resultados               → Lucas   (Tabela 3)
#recomendacao             → Lucas   (box)
```

Se alguém se perder, o índice do artigo tem exatamente esses nomes. Clique no índice **só** se o scroll falhar.

---

## Se o professor perguntar (qualquer um)

**“Então o artigo fracassou?”**  
Não. Mostrar que 12 minutos com estes atributos **não antecipam FALHA** é o resultado. O RFC já previa: sem ganho sobre a persistência, o sistema é detector.

**“Por que não usaram RTT em ms?”**  
Porque o modelo aprenderia “caminho longo = problema”. *(João pode voltar à Tabela 2 se pedirem.)*

**“Por que não Random Forest, se tem menos alarme falso?”**  
Critério do grupo: **auditar o alerta** e latência. Se a prioridade fosse fadiga de alerta, a floresta ganharia — o box da Recomendação diz isso.

**“Isso vale para a rede da faculdade?”**  
Não sabemos. Anchors são datacenters. Limitação explícita no HTML; **não role até lá** a menos que perguntem.

**“A Tarefa 4 não tinha F1 1,0?”**  
Aquela F1 é o **detector da classe atual**. O artigo prevê a classe **futura**. São perguntas diferentes; o F1 cai para ~0,76.

Na pergunta, **não saiam caçando** a seção. Respondam de pé. Só voltem no HTML se o professor pedir para ver um número.

---

## Cronômetro no dia

Alguém que não está falando marca o tempo e levanta a mão aos **1:20** (Lucas **1:30**).

Ensaio único: abrir o HTML, ler este roteiro em voz alta **uma vez**, com o scroll de verdade. Se passar de 8:00, cortar exemplos, **não** números. Não ensaiem as perguntas.
