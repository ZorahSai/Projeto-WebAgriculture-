"""Árvore de decisão implementada manualmente (CART simplificado, critério de Gini).

Estrutura:
- `Folha`: guarda a classe prevista e quantas amostras de cada classe chegaram nela.
- `No`: guarda a condição de corte (`atributo <= limiar`) e os filhos `esquerda` (condição
  verdadeira) e `direita` (condição falsa).

Construção (recursiva): em cada nó, testa todos os cortes possíveis de cada atributo e escolhe
o que deixa os dois filhos mais "puros" (menor impureza de Gini ponderada). Para quando o nó
já é puro, quando atinge a profundidade máxima, quando tem poucas amostras ou quando nenhum
corte melhora a impureza. Depois de construir os filhos, aplica uma poda simples: um corte
cujos dois lados terminam em folhas da mesma classe é trocado por uma única folha.

Classificação (percurso recursivo): começa na raiz, testa a condição e desce para a esquerda
ou para a direita até chegar a uma folha.

Valores vazios (None): latência e jitter ficam vazios quando todos os pacotes se perdem.
A árvore trata o vazio como "infinito" (sem resposta = latência infinitamente alta), então
um valor vazio nunca satisfaz `atributo <= limiar` e sempre desce para a direita.
"""
import math
import random
from dataclasses import dataclass, field

ATRIBUTOS = ["latencia_ms", "perda_pacotes_pct", "jitter_ms"]


@dataclass
class Folha:
    classe: str
    contagem: dict


@dataclass
class No:
    atributo: str
    limiar: float
    esquerda: "No | Folha"
    direita: "No | Folha"
    contagem: dict = field(default_factory=dict)


def contar(rotulos):
    contagem = {}
    for rotulo in rotulos:
        contagem[rotulo] = contagem.get(rotulo, 0) + 1
    return contagem


def gini(contagem, total):
    if total == 0:
        return 0.0
    return 1.0 - sum((quantidade / total) ** 2 for quantidade in contagem.values())


def classe_majoritaria(contagem):
    # Em caso de empate, escolhe a classe de nome menor, para o resultado ser determinístico.
    return min(contagem, key=lambda classe: (-contagem[classe], classe))


def valor_ordenavel(valor):
    return math.inf if valor is None else valor


def vai_para_esquerda(valor, limiar):
    return valor is not None and valor <= limiar


def melhor_corte(registros, rotulos, atributos):
    """Devolve (atributo, limiar, impureza_ponderada) do melhor corte, ou None se não houver corte."""
    total = len(rotulos)
    melhor = None

    for atributo in atributos:
        pares = sorted((valor_ordenavel(registro[atributo]), rotulo)
                       for registro, rotulo in zip(registros, rotulos))
        esquerda, direita = {}, contar(rotulos)

        # Varre os valores em ordem, movendo uma amostra por vez da direita para a esquerda.
        for i in range(total - 1):
            valor, rotulo = pares[i]
            esquerda[rotulo] = esquerda.get(rotulo, 0) + 1
            direita[rotulo] -= 1

            proximo = pares[i + 1][0]
            if valor == proximo:
                continue  # só dá para cortar entre valores diferentes

            n_esq = i + 1
            n_dir = total - n_esq
            impureza = (n_esq * gini(esquerda, n_esq) + n_dir * gini(direita, n_dir)) / total
            if melhor is None or impureza < melhor[2]:
                limiar = valor if math.isinf(proximo) else (valor + proximo) / 2
                melhor = (atributo, round(limiar, 4), impureza)

    return melhor


def construir(registros, rotulos, profundidade=0, max_profundidade=4, min_amostras=5, atributos=ATRIBUTOS):
    contagem = contar(rotulos)
    impureza_atual = gini(contagem, len(rotulos))

    if impureza_atual == 0 or profundidade >= max_profundidade or len(rotulos) < min_amostras:
        return Folha(classe_majoritaria(contagem), contagem)

    corte = melhor_corte(registros, rotulos, atributos)
    if corte is None or corte[2] >= impureza_atual:
        return Folha(classe_majoritaria(contagem), contagem)

    atributo, limiar, _ = corte
    reg_esq, rot_esq, reg_dir, rot_dir = [], [], [], []
    for registro, rotulo in zip(registros, rotulos):
        if vai_para_esquerda(registro[atributo], limiar):
            reg_esq.append(registro)
            rot_esq.append(rotulo)
        else:
            reg_dir.append(registro)
            rot_dir.append(rotulo)

    esquerda = construir(reg_esq, rot_esq, profundidade + 1, max_profundidade, min_amostras, atributos)
    direita = construir(reg_dir, rot_dir, profundidade + 1, max_profundidade, min_amostras, atributos)

    # Poda: se os dois filhos são folhas que preveem a mesma classe, o corte não muda nenhuma
    # previsão, então o nó vira uma folha só.
    if isinstance(esquerda, Folha) and isinstance(direita, Folha) and esquerda.classe == direita.classe:
        return Folha(esquerda.classe, contagem)

    return No(atributo, limiar, esquerda, direita, contagem)


def classificar(no, registro):
    """Percurso recursivo da raiz até uma folha."""
    if isinstance(no, Folha):
        return no.classe
    if vai_para_esquerda(registro[no.atributo], no.limiar):
        return classificar(no.esquerda, registro)
    return classificar(no.direita, registro)


def descrever(no, prefixo=""):
    """Representação textual da árvore, uma condição ou folha por linha."""
    if isinstance(no, Folha):
        return [f"{prefixo}→ {no.classe}  {formatar_contagem(no.contagem)}"]

    linhas = [f"{prefixo}{no.atributo} <= {no.limiar:g}?  {formatar_contagem(no.contagem)}"]
    linhas += descrever_filho(no.esquerda, prefixo, "sim", ultimo=False)
    linhas += descrever_filho(no.direita, prefixo, "não", ultimo=True)
    return linhas


def descrever_filho(filho, prefixo, resposta, ultimo):
    ramo = "└── " if ultimo else "├── "
    continuacao = "    " if ultimo else "│   "
    linhas = descrever(filho, prefixo + continuacao)
    primeira = linhas[0][len(prefixo + continuacao):]
    return [f"{prefixo}{ramo}{resposta}: {primeira}"] + linhas[1:]


def formatar_contagem(contagem):
    total = sum(contagem.values())
    partes = ", ".join(f"{classe} {contagem[classe]}" for classe in sorted(contagem))
    return f"[{total} amostras: {partes}]"


def profundidade(no):
    if isinstance(no, Folha):
        return 0
    return 1 + max(profundidade(no.esquerda), profundidade(no.direita))


def contar_folhas(no):
    if isinstance(no, Folha):
        return 1
    return contar_folhas(no.esquerda) + contar_folhas(no.direita)


def para_dict(no):
    """Converte a árvore em dicionário (para salvar em JSON e carregar no dashboard)."""
    if isinstance(no, Folha):
        return {"classe": no.classe, "contagem": no.contagem}
    return {
        "atributo": no.atributo, "limiar": no.limiar, "contagem": no.contagem,
        "esquerda": para_dict(no.esquerda), "direita": para_dict(no.direita),
    }


def de_dict(dados):
    if "classe" in dados:
        return Folha(dados["classe"], dados["contagem"])
    return No(dados["atributo"], dados["limiar"], de_dict(dados["esquerda"]), de_dict(dados["direita"]),
              dados["contagem"])


def dividir_treino_teste(registros, proporcao_treino=0.7, semente=42, coluna_rotulo="status_real"):
    """Divisão estratificada: cada classe é dividida na mesma proporção entre treino e teste."""
    rng = random.Random(semente)
    por_classe = {}
    for registro in registros:
        por_classe.setdefault(registro[coluna_rotulo], []).append(registro)

    treino, teste = [], []
    for classe in sorted(por_classe):
        grupo = por_classe[classe][:]
        rng.shuffle(grupo)
        corte = round(len(grupo) * proporcao_treino)
        treino += grupo[:corte]
        teste += grupo[corte:]

    rng.shuffle(treino)
    rng.shuffle(teste)
    return treino, teste


def acuracia(reais, previstos):
    return sum(1 for real, previsto in zip(reais, previstos) if real == previsto) / len(reais)


def matriz_confusao(reais, previstos, classes):
    matriz = {real: {previsto: 0 for previsto in classes} for real in classes}
    for real, previsto in zip(reais, previstos):
        matriz[real][previsto] += 1
    return matriz
