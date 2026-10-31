# Entrega final — conferência do PDF da professora

**Revisão em 31/10/2026 · WebAgriculture · Ciência da Computação · Universidade Brás Cubas.**

Base: PDF `projeto final.pdf`, enviado pela equipe, páginas 2–9. As páginas 10–14 estão em branco. A leitura foi feita por OCR e conferência visual das tabelas. Esta revisão não comprova inscrições ou envios externos.

## Checklist final

| Prazo | Exigência do PDF | Situação e evidência |
|---|---|---|
| **02/11** | Logo PNG 600 × 600, `logo_nomedoprojeto.png` | **Pronto:** [logo_webagriculture.png](logo_webagriculture.png), exportação técnica do desenho enviado, em 600 × 600. Original 500 × 500 preservado em `logo_webagriculture_original.png`. |
| **02/11** | Nome até 30 caracteres | **Pronto:** WebAgriculture, 14 caracteres. |
| **02/11** | Descritivo até 200 caracteres | **Pronto:** texto de 167 caracteres em [dados de inscrição](inscricao_mostra.md). |
| **02/11** | Tags e formulário da turma | **Tags prontas; envio externo pendente.** A URL do formulário não consta como link recuperável no PDF rasterizado. |
| **04/11** | GitHub completo: código, documentos e todos os `tarefas.md` | **Arquivos preparados:** pipeline T1–T5 preservado, relatórios/diários, [índice de tarefas](../tarefas.md) e registros em `docs/tarefas/T1…T5/tarefas.md`. Esses registros são cópias identificadas dos diários existentes; não inventam um histórico. |
| **04/11** | Pitch de 90 s no YouTube como não listado | **Vídeo pronto; YouTube pendente:** [MP4](pitch/webagriculture-90s.mp4), narração sintética em português, [legendas SRT](pitch/legendas.srt), [WebVTT](pitch/legendas.vtt) e [transcrição](pitch/transcricao.html). [Instruções de publicação](pitch/LEIA-ME.md). |
| **04/11** | README com links do artigo e vídeo | **Artigo e MP4 vinculados.** Substituir/complementar o link do MP4 com a URL não listada após envio ao YouTube. |
| **04/11** | Página para visitantes, com vídeo | **Pronta:** problema, objetivo, funcionamento, pipeline com entradas/saídas, dados e avaliação, resultados, limitações, pitch incorporado, curso/instituição, equipe, orientação, acesso e fontes. |
| **04/11** | QR Code que abre a página | **Conferido:** `qrcode.png` decodifica para `https://zorahsai.github.io/Projeto-WebAgriculture-/`. QR incorporado na página e no encerramento do vídeo. Testar a impressão antes da mostra. |
| **04/11** | ZIP com nome do grupo, enviado ao Blackboard | **Pacote pronto; Blackboard pendente:** [WebAgriculture.zip](../entrega/WebAgriculture.zip), com os três arquivos exigidos e carregador/instruções/dependências. |
| **05/11** | Avaliação formal individual e perguntas | **Preparação humana pendente:** roteiro de ensaio abaixo. A nota e seleção da mostra são individuais. |

A presença dos arquivos no GitHub e do MP4 na página **não substitui** inscrição, publicação não listada no YouTube nem envio do ZIP no Blackboard. Não há acesso a essas três plataformas nesta sessão. Não foram enviados formulários nem registradas confirmações fictícias.

O README antigo cita apresentação em 10–12/11. A documentação agora separa isso dos prazos do PDF: inscrição 02/11, entregas 04/11 e avaliação individual 05/11. Confirmar se 10–12/11 corresponde a outro evento.

## Contrato do modelo corrigido

O modelo binário e o baseline foram preservados, sem novo treino, mudança de hiperparâmetros ou reavaliação do bloco de teste. O pacote agora inclui:

- `nome_modelo`, `versao_modelo` e versão do contrato.
- Ordem das oito features, tipos, fórmulas, saída e ordem de classes, horizonte atual, histórico e referência ao baseline.
- Fallback de MAD zero: `max(IQR/1.349, 1.0 ms)`; z zero se também o desvio é zero.
- Casos de jitter típico zero: `0/0 → 1`, positivo/zero → infinito, ausência → NaN.
- Descrição correta de `n5_risco`: soma do critério moderado **antes do rótulo final**, não contagem de classes finais RISCO.
- Corte correto de `n5_aumento80`: **`aumento_pct > 80`**, conforme o código.
- Política explícita da interface de entrega: rejeitar entradas faltantes, NaN ou infinito, sem imputar silenciosamente ou fabricar classe. O exemplo demonstra inferência de vetores finitos; não é um monitor operacional.
- Carregador que verifica chaves, ordem de features, classes e o exemplo real; script `empacotar_entrega.py` que fecha o ZIP sem treinar.

O script `exportar_entrega.py` continua treinando ao exportar do dataset. Para apenas fechar o ZIP existente, usar `python src/empacotar_entrega.py`. A formação de features operacionais e a validação da ficha devem respeitar as regras documentadas.

## Verificações executadas

- Ambiente virtual separado com **Python 3.14.7**, **numpy 2.5.4**, **pandas 3.0.6**, **scikit-learn 1.9.1**, **joblib 1.6.0**.
- Carga do `.joblib` e previsão do exemplo real: **OK**, sem avisos de incompatibilidade nesse ambiente.
- Quatro testes de integração do contrato, executados com avisos tratados como erros: exemplo com chaves reordenadas, rejeição de entradas inválidas, consistência do baseline e igualdade dos arquivos dentro do ZIP. **Todos passaram.**
- Interface: cenários OK/RISCO/FALHA, sincronização da ilustração, controles por teclado, etapas, roteiro guiado e saída por Escape.
- Layout sem rolagem horizontal da página em 320, 375, 768, 1100 e 1440 px. Gráficos/tabelas largos mantêm rolagem própria.
- Axe-core (WCAG A/AA e WCAG 2.1 AA): **nenhuma violação detectada** nos estados examinados nos temas claro e escuro. Isso não certifica conformidade integral nem substitui ensaio com leitor de tela.
- Movimento reduzido e leitura dos textos/resultados sem JavaScript.
- QR Code decodificado; vídeo com imagem H.264, áudio AAC e legendas/transcrição externas.

Foi relatado um travamento de scripts após gerar um JSON. A carga do modelo e os testes da entrega não reproduziram esse problema. Para diagnosticar o comando original, ainda são necessários o comando executado e as últimas linhas do erro; não foi declarado como resolvido sem essa evidência.

## UX e identidade

Paleta do logo: verde escuro `#14532D`, verde `#166534`, menta `#86EFAC`, amarelo `#FACC15`, com fundos/textos ajustados por contraste. Rótulos de classe e explicações textuais acompanham as cores.

A abertura convida a explorar; o laboratório existente foi antecipado e distingue demonstração, política de rótulos e modelo Python. A onda é explicitamente ilustrativa. O pipeline tem etapas clicáveis e fluxo completo com entradas/saídas. O roteiro guiado apoia a apresentação. O vídeo é acessível por controles nativos, legendas e transcrição.

Os resultados F1 macro 0,9999 descrevem reprodução de rótulos do **estado atual**. Não comprovam defeito físico nem antecipação de falhas. O artigo complementar a 12 minutos continua separado.

## Ensaio individual

Cada integrante precisa conseguir explicar:

1. Problema, origem dos dados e chamadas GET à API RIPE Atlas.
2. Por que RTT alto não implica falha; mediana, MAD e baseline por fluxo.
3. Como a árvore aprende; Gini, profundidade, poda e atributos relativos.
4. Corte temporal, validação e teste reservado.
5. Matriz de confusão, F1 macro, erros e limitações.
6. Diferença entre classificação atual, rótulo heurístico, falha física e previsão futura.

Antes dos envios: assistir aos 90 s e revisar pronúncia/legendas; ensaiar em celular e computador; testar QR impresso; guardar comprovantes da inscrição e do Blackboard.

## Estado da publicação nesta sessão

As alterações estão preparadas e testadas localmente. A tentativa de criar objetos e uma branch em `ZorahSai/Projeto-WebAgriculture-` foi recusada pelo GitHub com **403: Resource not accessible by integration**. A instalação disponível pertence somente à conta `iedahirari`. Nenhuma mudança desta revisão foi publicada no repositório WebAgriculture por esta sessão. É necessário habilitar a integração na conta/repositório de `ZorahSai` para concluir a publicação.
