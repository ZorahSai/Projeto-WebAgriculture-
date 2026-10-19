# Material de estudo — artigo “Preditor de degradação de rede”

**Para quem:** os 5 integrantes do WebAgriculture  
**Artigo:** https://iedahirari.github.io/artigo-preditor-redes/  
**Arquivo local:** `Downloads/artigo preditor de redes.html`  
**Repo do artigo:** https://github.com/iedahirari/artigo-preditor-redes  
**Tempo de apresentação:** até 8 minutos, **abrindo o HTML** (sem slides).  
Roteiro com o que apontar na tela: `roteiro_apresentacao_artigo.md` (esta pasta).

Leia isto **antes** do roteiro. Não precisa decorar o HTML inteiro. Na apresentação, cada pessoa fala em cima da seção do artigo que já está na tela; só rola para baixo.

---

## 1. Em uma frase

O artigo pergunta: **olhando o ping de agora, dá para saber se daqui a 12 minutos o caminho estará OK, RISCO ou FALHA?**

Comparam três programas que “aprendem com exemplos” (árvore, floresta e XGBoost) com a regra mais burra possível: **“daqui a 12 minutos vai estar como está agora”** (isso se chama **persistência**).

Conclusão do artigo: **quase não dá.** Os modelos empatam entre si e ganham muito pouco da persistência. **Ninguém avisa o início de uma FALHA.** O que eles fazem melhor é perceber quando uma falha **já está acabando**, e assim disparam menos alarme falso.

Por isso o grupo recomenda a **árvore de decisão** não como “bola de cristal”, e sim como **detector com um olhinho no curto prazo**: rápida, dá para ler as regras, e quase tão boa quanto os modelos grandes.

---

## 2. Não misture os dois trabalhos

| | Projeto no GitHub (Tarefas 1–4) | Artigo |
|---|---|---|
| Pergunta | Qual é a classe **desta** medição? | Qual será a classe **daqui a 12 minutos**? |
| Nome honesto | **Detector** | Tentativa de **preditor** |
| Modelos | Uma árvore (Tarefas 3 e 4) | Árvore + Random Forest + XGBoost |
| Régua | Validação; teste ainda fechado na Tarefa 4 | Persistência + teste único |
| Dados | Os mesmos pings RIPE Atlas do grupo | Os mesmos, com alvo = classe 3 medições à frente |

Se alguém perguntar “vocês já preveem o futuro?”: **não com confiança.** O artigo mostra isso com números.

---

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

---

## 4. Os três modelos (ideia, sem fórmula)

### Árvore de decisão
Faz perguntas do tipo “`z_robusto` ≤ 3,4?” até chegar numa folha (OK, RISCO ou FALHA).  
**Prós:** dá para ler; muito rápida (0,56 ms por ping).  
**Contras:** se ficar profunda demais, decora.  
**No artigo:** profundidade 4, 16 folhas. F1 no teste **0,759**.

### Random Forest (floresta)
Muitas árvores, cada uma treina num sorteio dos dados e só vê alguns atributos por pergunta. No fim, **votação**.  
**Prós:** mais estável (reduz variância).  
**Contras:** lenta para um ping de cada vez (15,7 ms); não dá para mostrar o caminho de um alerta.  
**No artigo:** F1 **0,763**.

### XGBoost (boosting)
Árvores **em fila**: cada uma tenta corrigir o erro da anterior.  
**Prós:** em tabelas, costuma ser o mais forte.  
**Contras:** mais ajuste; treino mais lento (7 s).  
**No artigo:** F1 **0,765** — o maior, por um fio.

Frase para guardar: **floresta = várias árvores em paralelo (voto). Boosting = árvores em sequência (correção).**

---

## 5. Números para não errar na fala

Teste: **66.702** medições.

| Modelo | F1 macro | Inícios de FALHA anunciados | Alarmes falsos de FALHA |
|---|---|---|---|
| Árvore | 0,759 | 4 de 1.990 | 650 |
| Random Forest | 0,763 | 3 de 1.990 | **446** |
| XGBoost | **0,765** | **4 de 1.990** | **446** |
| Persistência | 0,753 | **0** de 1.990 | 2.008 |

- Melhor modelo vs persistência: **+0,012** de F1 (0,765 − 0,753). Pouquinho.  
- Três modelos entre si: diferença **0,006** — ruído de uma execução.  
- Caminhos **longos** são fáceis (~0,85 de F1). **Curtos** são difíceis (~0,54); neles a persistência até ganha.  
- Ninguém trata caminho longo como problema → os atributos relativos funcionaram.

---

## 6. A recomendação (o “e daí?”)

**Escolhemos a árvore**, como detector de curto prazo, **não** como preditor de falha futura.

Por quê?

1. Quase o mesmo F1 do XGBoost.  
2. Única que o operador lê (“RTT a mais de 3,4 desvios e jitter baixo → a falha deve continuar”).  
3. Mais rápida.

Se o objetivo fosse **menos alarme falso**, floresta ou XGBoost (446 vs 650).  
Se o objetivo fosse **avisar FALHA 12 min antes**, **nenhum** resolve com estes 8 atributos.

O RFC do projeto já dizia: sem ganho claro sobre a persistência, declara-se **detector**.

---

## 7. Limitações (se o professor perguntar)

- O rótulo é **política**, não ticket de roteador.  
- Uma semente, um corte no tempo — os 0,006 entre modelos não são “vitória”.  
- Só 5 medições de memória; falha que começa sem aviso não aparece.  
- Mudança de rota (ex. 7 ms → 13 ms estável) a regra marca FALHA o tempo todo.  
- Anchors do RIPE não são a rede do campus.

---

## 8. Como estudar em 30 minutos

1. Ler as seções 1–6 deste guia (10 min).  
2. Abrir o artigo e só olhar: Figura 1 (árvore), Figura 6 (overfitting), Tabela 3 (resultados), o box de Recomendação (10 min).  
3. Ler **só o seu bloco** do roteiro em voz alta, com cronômetro (5–8 min).  
4. Combinar a passagem de um integrante para o outro (quem fala a última frase).

Artigo publicado: 18/10/2026. Autores (ordem alfabética): Apollo, Icaro, Ieda, João Pedro, Lucas.
