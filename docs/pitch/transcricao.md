# Pitch — WebAgriculture

Duração: 90 segundos. Narração sintética em português. Legendas em SRT e WebVTT.

## 00:00:00–00:00:10 · WebAgriculture

Uma rede pode parecer lenta. Mas está em risco? Conheça o WebAgriculture, projeto de Ciência da Computação da Universidade Brás Cubas.

## 00:00:10–00:00:22 · 01 / O PROBLEMA

Um caminho longo pode ter latência alta e estar saudável. Já um pequeno aumento num caminho curto pode indicar degradação. Um limite global em milissegundos não conta toda a história.

## 00:00:22–00:00:34 · 02 / DADOS REAIS

Usamos quatorze dias de medições públicas de ping do RIPE Atlas, em noventa e sete fluxos. A primeira semana estima o normal de cada caminho, com mediana e desvio absoluto mediano.

## 00:00:34–00:00:46 · 03 / COMO FUNCIONA

Na segunda semana, calculamos atributos relativos, perda, jitter e histórico de cinco medições. Uma árvore de decisão aprende a classificar cada fluxo como OK, RISCO ou FALHA, seguindo a política de rótulos.

## 00:00:46–00:00:58 · 04 / AVALIAÇÃO

Separamos os dados em ordem de tempo. Os parâmetros são escolhidos apenas na validação. O teste é aberto uma única vez, reduzindo o risco de ajustar o modelo aos resultados finais.

## 00:00:58–00:01:10 · 05 / RESULTADOS

No teste, com sessenta e oito mil quatrocentas e setenta e duas medições, o F um macro foi de zero vírgula nove nove nove nove. Foram quatro erros de classificação.

## 00:01:10–00:01:20 · 06 / LIMITES

O resultado mede a reprodução de regras heurísticas. Não comprova defeito físico nem prevê falhas futuras. Mudanças de rota podem exigir recalibração do normal do caminho.

## 00:01:20–00:01:30 · EXPLORE O PROJETO

Na página, experimente os cenários, ajuste os atributos e explore a classificação. Consulte também o código, a metodologia e as limitações. WebAgriculture: contexto para entender a degradação da rede.
