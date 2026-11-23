# Caso 4 — Benchmarking de Eficiência Operacional de APIs de LLM via DEA Gaussiano

## Fonte
Notebook do usuário: DEA_AHPGS_AI.ipynb (10 pastas de execução: claude/sonnet/deepseek/gemini/openai x nq/squad).
Apenas células efetivamente executadas no notebook foram usadas (exec_count presente em todas as células relevantes).

## DMUs
5 modelos de LLM: Claude Haiku 4.5, Claude Sonnet 4.5, DeepSeek Chat, Gemini 2.5 Flash, GPT-4o mini.
Dados agregados (soma) dos dois benchmarks (NQ + SQuAD) por modelo. Total: 20.715 execuções.

## Inputs / Outputs
- Inputs: Tokens de Entrada (total), Custo de Entrada (US$)
- Outputs: Razão Saída/Entrada, Tokens de Saída (total), Custo de Saída (US$)

## Pontos discutidos com o usuário (histórico de decisões)
1. Pesos: o notebook original usa `input_weights = inputs_normalized` / `output_weights =
   outputs_normalized` (auto-referência, equivalente a elevar os valores normalizados ao quadrado),
   em vez do Fator Gaussiano (σ/μ) global usado nos Casos 1-3. Inicialmente o usuário pediu para
   manter os resultados exatos do notebook; depois reverteu essa decisão e pediu explicitamente para
   usar o peso calculado no Fator Gaussiano — DECISÃO FINAL.
2. `cost_input` foi normalizado com monotonicidade 'min' (invertida) no passo interativo do notebook,
   mesma direção usada para `cost_output` — mas por ser um INPUT isso inverte a lógica esperada
   (penaliza o modelo mais barato). Muito provavelmente resposta trocada no prompt interativo
   ('min'/'max'). Como os pesos do Fator Gaussiano deram peso alto justamente a cost_input (0,758),
   essa inversão passou a dominar o ranking de forma contraintuitiva (o mais caro, Sonnet, liderando).
   Apresentei a comparação ao usuário, que optou por corrigir também esse ponto (monotonicidade 'max',
   sem inversão) — DECISÃO FINAL.

Sem Nota Metodológica no texto final: a metodologia agora é consistente com os Casos 1-3 (peso escalar
fixo por critério, via Fator Gaussiano σ/μ, sem correção de Pearson — mesmo padrão do Caso 3).

## Resultado final (pesos do Fator Gaussiano + cost_input com monotonicidade correta)
| DMU | Weighted Inputs | Weighted Outputs | Efficiency | Relative Efficiency | Ranking |
|---|---|---|---|---|---|
| Gemini 2.5 Flash | 0.0644 | 1.1630 | 18.0507 | 1.000 | 1 |
| Claude Haiku 4.5 | 0.1270 | 0.8094 | 6.3718 | 0.353 | 2 |
| DeepSeek Chat | 0.1169 | 0.7302 | 6.2483 | 0.346 | 3 |
| GPT-4o mini | 0.2141 | 0.3038 | 1.4189 | 0.079 | 4 |
| Claude Sonnet 4.5 | 0.7951 | 0.6492 | 0.8165 | 0.045 | 5 |

Pesos por critério (Fator Gaussiano normalizado, sem Pearson): Custo de Saída 1,000 | Custo de Entrada
0,758 | Tokens de Saída 0,388 | Razão Saída/Entrada 0,372 | Tokens de Entrada 0,047.

## Estrutura inserida na dissertação (6.4, logo após o Caso 3)
- 6.4.1 Contexto e Problema (+ Tabela 34, dados brutos por modelo)
- 6.4.2 Aplicação do Método DEA-GS (+ Tabela 35 pesos AHP-GS, Tabela 36 normalizados,
  Tabela 37 ponderados, Tabela 38 resultados finais, Gráfico 4)
- 6.4.3 Resultados Principais e Análise
- 6.4.4 Lições sobre o Método e Validação

## Numeração de seções (corrigida)
O Capítulo 6 ainda usava numeração "5.x" herdada de um esquema de capítulos anterior (nunca atualizado
no documento original bancado). Foi feita uma correção completa e única (sem substituições em cadeia)
de todos os índices de seção do documento, não apenas do Capítulo 6:
- 3.4. → 3.4 (ponto solto removido)
- 3.2 "Estratégia de Validação" → 4.2 (estava com o número do capítulo errado)
- 4.3.4 "Etapa 4..." → 5.3.4 (idem)
- 6. "APLICAÇÕES..." → 6 (ponto solto removido, para consistência com os demais títulos de capítulo)
- 5.1/5.1.1-5.1.4 (Caso 1) → 6.1/6.1.1-6.1.4
- 5.2/5.2.1-5.2.4 (Caso 2) → 6.2/6.2.1-6.2.4
- 6.3, 6.4 (Casos 3 e 4): já estavam corretos, sem alteração
- 5.2.3 "Análise Comparativa..." + 5.2.3.1-5.2.3.5 → 6.5 + 6.5.1-6.5.5 (esta seção reusava o número
  "5.2.3", já usado por "Resultados Principais e Análise" do Caso 2 — conflito de numeração duplicada
  no original, agora resolvido)
- 5.3.1 "Análise Quantitativa Comparativa..." + 5.3.1.1-5.3.1.3 → 6.6 + 6.6.1-6.6.3
- 5.4.3 "Síntese da Análise Comparativa" → 6.7
- 7.3 "Recomendações para estudos futuros" → 7.2 (não havia 7.2 no original, pulava direto de 7.1 para 7.3)

A lógica adotada: a seção comparativa DEA-GS vs. modelos clássicos (complexidade + resultados
quantitativos + síntese) passou a ocupar 6.5-6.7, na sequência natural após os 4 estudos de caso (6.1-6.4).

## Pendência de conteúdo — RESOLVIDA (seções 6.5-7.2)
A pendência original (texto de 6.5-7.2 ainda falando em "dois estudos de caso") foi resolvida: rodou-se
DEA CRS/VRS clássico real para o Caso 4 (LLMs, n=5), com o Custo de Saída reformulado como input adicional
(mesmo tratamento de inversão já usado para a latência no Caso AWS). Novas tabelas: Tabela 24 (correlações
Spearman/Kendall DEA-GS vs. CRS/VRS, caso LLMs) e Tabela 27 (discrepância de rankings, caso LLMs), mais
extensões pontuais às Tabelas 28 (linha "LLMs" na correlação escore-ranking), 29 (coluna "LLMs (CV)" na
dispersão) e 30 (células de Evidência da síntese, citando os Casos 3 e 4). O Caso 3 (n=31.061) permanece
explicitamente fora dessa comparação quantitativa específica — inviável para DEA clássico, o que é
justamente o ponto do caso — com uma "Nota metodológica" no texto (antes da Tabela 24) deixando isso
explícito, incluindo a violação da heurística n ≥ 2-3×(m+s) (Cooper; Seiford; Tone, 2007) e o resultado
consequente (4 dos 5 modelos empatados como plenamente eficientes no CRS/VRS). Seções 6.5, 6.6 (6.6.1-
6.6.3), 6.7 e o Capítulo 7 (Conclusão, incluindo Escopo/Limitações e Recomendações) foram reescritos para
falar em "quatro estudos de caso" e citar os quatro domínios consistentemente. Nova recomendação de
pesquisa futura adicionada à seção 7.2, sobre a sensibilidade do próprio DEA-GS à razão n/(m+s).

## Pendência remanescente (NÃO resolvida — fora do escopo desta rodada)
O Resumo (abstract, parágrafo com "A validação empírica foi conduzida por meio de dois estudos de caso...")
e o parágrafo de roteiro do Capítulo 1 ("Através da aplicação em dois estudos de caso publicados...", que
introduz o conteúdo do Capítulo 6) ainda mencionam apenas 2 estudos de caso. Esses dois parágrafos ficam
ANTES do Capítulo 6 e não foram cobertos por esta rodada (que tratou apenas das seções posteriores ao
capítulo de casos). Ficam como pendência para uma rodada dedicada a revisar o material introdutório/resumo.

## Bugs encontrados e corrigidos durante esta rodada (Caso 4, extensão 6.5-7.2)
1. **Índices de tabela desatualizados**: os Blocos C/D/E do script (`insert_case4.py`) localizavam as
   tabelas de correlação escore-ranking, dispersão e síntese via `d.tables[N]` com N fixo. Como a própria
   extensão insere 2 tabelas novas mais cedo no documento (Tabela 24 e Tabela 27), os índices das tabelas
   subsequentes mudam. O Bloco E acabou escrevendo o texto de "Evidência" da síntese em uma tabela errada
   (o quadro "Aspecto | DEA CRS/VRS | DEA Gaussiano" da seção 6.5), sobrescrevendo seu conteúdo original
   curto ("Programação Linear", "O(n⁴)", "n") com o texto longo destinado à síntese. Corrigido com uma
   função `find_table_by_header()` que localiza a tabela certa pelo texto exato do cabeçalho, em vez de por
   posição — usada agora nos Blocos C, D e E. O script sempre reconstrói do zero a partir de `working.docx`,
   então bastou corrigir e rodar de novo; nenhum reparo manual no docx foi necessário.
2. **Tamanho de fonte inconsistente em células de tabela (bug mais amplo, afetava Casos 3 E 4)**: as funções
   auxiliares que escrevem texto em células de tabela (`set_row_text`, `set_cell_text`, `add_data_row`,
   `append_column_cell`) usavam os templates de run `REG`/`BOLD`, que são 12pt (sz=24), copiados de um
   parágrafo do corpo do texto — mas as células de tabela nesta dissertação usam 9pt (sz=18). Isso deixava
   qualquer texto novo inserido em tabela visivelmente maior que o texto nativo ao redor (mais óbvio na
   coluna "LLMs (CV)" da Tabela 29, que também ficou em negrito). Como essas funções são usadas em TODAS as
   tabelas novas do Caso 3 e do Caso 4 (não só nesta extensão), o bug afetava também tabelas construídas em
   sessões anteriores. Corrigido adicionando templates `TCELL`/`TCELL_BOLD` (9pt, extraídos de uma célula de
   tabela real já existente no documento) e trocando as 4 funções para usá-los. Após a correção, o PDF final
   caiu de 89 para 86 páginas (linhas de tabela mais compactas, como deveriam ser desde o início).

## Travessões (—) removidos
Todo o texto dos Casos 3 e 4 (parágrafos, legendas de tabela, itens numerados/bullets) foi revisado para
remover o travessão em todas as ocorrências, substituindo por vírgula ou ponto conforme a frase. Isso
incluiu também os títulos e eixos dos Gráficos 3 e 4 (imagens matplotlib regeradas: `grafico_fronteira_
educacao_v4.png` e `grafico_fronteira_llm_v2.png`), que também continham travessões nos títulos/eixos.
Confirmado por varredura completa do PDF renderizado (parágrafos + células de tabela + cabeçalhos/rodapés):
zero ocorrências de "—" no documento final.

## Pendência conhecida, não relacionada a esta rodada: LISTA DE TABELAS desatualizada
A lista de tabelas no pré-textual (parágrafos ~200-229, "Tabela 1" a "Tabela 28" com número de página fixo
via líder de pontos) já estava desatualizada antes desta rodada, faltando as entradas de Tabela 29-37
inseridas nos Casos 3/4. Com a renumeração desta rodada (24-28 → 25-30, mais as novas Tabela 24 e Tabela
27), essa lista fica ainda mais desatualizada. Corrigi-la requer repaginação completa (a lista usa números
de página fixos digitados manualmente, não campos de referência automática do Word) — fica como pendência
separada, a ser tratada em uma rodada dedicada ao pré-textual.

## Rodada seguinte: colisão de numeração de tabelas corrigida + Caso Educação citado em 6.6
O usuário reportou confusão com a "Tabela 32" (achou que misturava notação de complexidade com estatística
descritiva). Investigação (python-docx + pdftotext + imagem renderizada, inclusive na cópia que estava no
dispositivo do usuário) confirmou que o conteúdo da Tabela 32 ("Perfil comparativo, Top 10 vs. Bottom 10",
Caso Educação) sempre esteve limpo, sem qualquer notação O(n)/O(n²) misturada — não foi possível reproduzir
o problema relatado em nenhuma das três formas de inspeção.

Nessa investigação, porém, apareceu um bug real e não relacionado: os números de tabela 29 e 30 estavam
DUPLICADOS no documento — usados tanto pelas tabelas próprias do Caso 3/4 ("Tabela 29: Estatísticas
descritivas..." e "Tabela 30: Cálculo dos pesos...", seção 6.3/6.4) quanto pelas tabelas da seção 6.6/6.7
("Dispersão dos escores" e "Síntese da Análise Comparativa", que uma rodada anterior havia numerado 29 e 30
sem saber que esses números já estavam em uso mais cedo no documento). Corrigido deslocando apenas essas
duas tabelas colidentes para 38 e 39 (logo após a Tabela 37, última do Caso 4); as tabelas 22-28 não
colidiam com nada e permaneceram como estavam. Confirmado sem números duplicados no documento final (1 a
39, todos únicos).

## Causa raiz real da "Tabela 32 misturada": objetos de equação incorporados, invisíveis ao .text
O usuário mandou um print do Word mostrando "O(n)5,84", "O(n²)2,55" etc. dentro da Tabela 32. Minhas
checagens anteriores (python-docx `.text`, pdftotext, imagem renderizada pelo LibreOffice, e até o arquivo
salvo no computador do usuário) não detectaram nada de errado, porque o problema não estava em texto comum:
cada uma das 14 células de dados (7 linhas × 2 colunas) tinha um objeto de equação (`<m:oMathPara>`/
`<m:oMath>`, Office Math Markup Language) plantado bem antes do run de texto numérico. `python-docx` só lê
`<w:t>` (runs de texto normais) — equações OOXML matemáticas ficam invisíveis para `.text`, e o conversor
`soffice`/LibreOffice usado nas verificações também não as renderizou de forma visível (por isso os prints
e o PDF pareciam limpos, mas o Word do usuário exibia). A causa mais provável: em uma sessão anterior, essa
tabela ("Perfil comparativo, Top 10 vs. Bottom 10") foi construída clonando uma tabela de complexidade como
modelo (que legitimamente usa notação O(n)/O(n²) via equação), e a limpeza de texto daquela época só
removia `<w:r>` (runs comuns), sem tocar em `<m:oMathPara>` — a equação do modelo ficou para trás, escondida
atrás do número que a substituiu. Corrigido com uma função de limpeza (`strip_omath`) que remove
especificamente esses objetos de equação da Tabela 32; as 20 ocorrências legítimas de equação nas tabelas de
complexidade (seção 6.5) foram preservadas. Lição para o futuro: ao verificar tabelas geradas por clonagem
de outro template, checar também por `m:oMath`/`m:oMathPara`, não só texto.

Também foi atendido o pedido de citar o Caso 3 (Educação) na seção 6.6 (Análise Quantitativa Comparativa),
que antes só mencionava Restaurantes/AWS/LLMs (os três casos com um modelo DEA clássico calculável).
Como a correlação escore-ranking (Tabela 28, seção 6.6.2) não depende de um modelo clássico de referência,
foi possível estendê-la de fato ao Caso Educação: nova linha "Educação" na tabela (ρ = -1,00, calculado
diretamente das 31.061 linhas de `dea_results_corrected.xlsx`), mais um parágrafo interpretativo novo logo
após a tabela. O CV do DEA-GS para o Caso Educação (2,07, calculado do desvio padrão 0,130 / média 0,063 já
citados na Seção 6.3.3) também foi mencionado em prosa na seção 6.6.3 (Dispersão), com a ressalva explícita
de que esse caso não entra na Tabela 38 por não ter um CV calculado para os modelos clássicos. A introdução
da seção 6.5 (que apresenta as três dimensões da comparação: complexidade, quantitativa e qualitativa)
também ganhou uma cláusula explicando por que a consistência escore-ranking é a única análise quantitativa
desta seção estendida ao Caso Educação.

## Renumeração completa de tabelas, figuras e gráficos (ordem física = ordem de numeração)
Pedido do usuário: "ajuste toda a nomeclatura de tabelas, imagens, gráficos, etc. [...] entenda, não é
para tirar as coisas de lugar. só ajustar as nomesclaturas e referencias no texto, e ajeitar os indices."
Diagnóstico: a numeração das 39 tabelas não seguia a ordem de leitura física do documento. As tabelas dos
Casos 3 (Educação) e 4 (LLMs) tinham sido inseridas em sessões anteriores com os números 29-37, mesmo
aparecendo ANTES das tabelas de análise de complexidade (12-21) e de comparação quantitativa (22-28,
depois deslocadas para 38-39 numa correção anterior desta sessão). Nada de conteúdo foi movido — apenas
a numeração das legendas, as referências no texto, e os índices do início do documento.

Ordem física real (antes → depois da renumeração):
- Tabelas 1-11: já corretas, sem alteração.
- Tabelas do Caso 3/Caso 4 (antigas 29-37) → novas 12-20 (nesta ordem física, pois vêm antes da análise
  de complexidade).
- Tabelas de complexidade (antigas 12-21) → novas 21-30.
- Tabelas de comparação quantitativa/rankings (antigas 22-28) → novas 31-37.
- Tabelas 38-39 (dispersão dos escores / síntese): mantidas, sem alteração.

Passos executados no script (`insert_case4.py`):
1. 26 legendas de tabela renumeradas (busca por texto integral da legenda, não por índice de parágrafo,
   para evitar colisões — mesmo padrão já usado no script para os fix-ups anteriores).
2. 22 referências no corpo do texto corrigidas ("conforme a Tabela X", "na tabela Y:", etc.) para apontar
   para os novos números.
3. Nomenclatura "Imagem 1" → "Figura 1" corrigida nos dois lugares em que aparecia (a única figura fora
   de padrão do documento — todas as demais já usavam "Figura").
4. Referência cruzada órfã "Figura 4.1" (resquício de um esquema de numeração de seção antigo, na
   introdução do Capítulo 5/6) corrigida para "Figura 2", a única figura que a frase realmente descreve
   (arquitetura do método).
5. LISTA DE TABELAS reconstruída do zero: 39 entradas (antes só listava 1-28, desatualizada desde antes
   desta sessão), na nova ordem/numeração, com títulos extraídos diretamente das legendas atuais do corpo
   do texto (fonte mais confiável que a lista antiga, que já divergia de alguns títulos reais).
6. LISTA DE GRÁFICOS: as 2 entradas existentes (Gráfico 1, 2) tiveram a página atualizada; adicionadas as
   2 entradas que faltavam (Gráfico 3 — Educação, Gráfico 4 — APIs de LLM).
7. LISTA DE FIGURAS: apenas os números de página das 2 entradas existentes foram atualizados (nenhuma
   entrada nova, já estava completa).

Números de página: como os números em todas essas listas são texto digitado literalmente (não campos
PAGEREF do Word — confirmado via inspeção do XML bruto), eles nunca se autoatualizam. Em vez de estimar,
os números de página reais foram extraídos diretamente de um PDF renderizado do próprio documento
(pdftotext por página, com o deslocamento impressão-vs-índice calibrado e verificado em várias páginas).
Como adicionar 11 entradas à Lista de Tabelas e 2 à Lista de Gráficos empurra o resto do documento por
+1 página, o processo foi feito em duas passadas: uma primeira estimativa, seguida de uma nova renderização
e reextração para confirmar/corrigir o deslocamento — a versão final foi validada com 0 divergências entre
o que está escrito nas listas e a posição real de cada tabela/figura/gráfico no PDF renderizado.

Bug pré-existente identificado (fora do escopo desta tarefa, não corrigido): a legenda da Tabela 29 (antiga
Tabela 20) está com um trecho corrompido — "Exemplo Numérico Comparativo (para  variáveis)" — faltando o
"m=3" que deveria completar a frase (confirmado que esse defeito já existia em working.docx, antes desta
sessão). Como é um bug de conteúdo, não de numeração, não foi tocado no corpo do texto; a Lista de Tabelas
usa o título antigo, correto e mais descritivo ("Exemplo Numérico Comparativo (m=3)"), só para não propagar
o defeito para o índice.

Validação final: 0 travessões (—) no documento inteiro; 39 tabelas, todas com números únicos e em ordem
física sequencial 1-39; 40 tabelas no total (39 numeradas + 1 sem legenda numerada); 129 objetos de
equação (`oMath`) no corpo, todos nas 5 tabelas de complexidade legítimas (20 no total) — Tabela 15
(antiga 32) confirmada com 0 objetos de equação; verificação visual via PDF em múltiplas páginas (lista de
tabelas, lista de gráficos, lista de figuras, introdução, tabela 14/15, referência à Figura 2).

## Nova seção 3.6 "Normalização de Dados em MCDM" + trecho na metodologia sobre o limiar de 0,8 da Correção de Pearson
Pedido do usuário: adicionar 3-4 parágrafos ao referencial teórico sobre normalização, com foco nas 4
regras principais descritas no artigo "Impact of Normalization on Gaussian AHP Rankings in MCDM"
(Cavalcante e Silva, Jacob, Bentes, Freitas e Pinheiro, 2025 — anexado pelo usuário; Levy é coautor deste
artigo), citando-o mas trazendo também outras referências; e um trecho na metodologia explicando por que
a Correção de Pearson só é aplicada quando a correlação global ultrapassa 0,8.

Conteúdo lido do artigo (Tabela 1, "Standardization Process", 4 procedimentos):
1. Valor/valor máximo (aᵢⱼ/max(aᵢⱼ)) — preserva proporcionalidade.
2. Min-max ((aᵢⱼ−min)/(max−min)) — NÃO preserva proporcionalidade.
3. Soma (aᵢⱼ/Σaᵢⱼ) — preserva proporcionalidade.
4. Vetorial/euclidiana (aᵢⱼ/(Σaᵢⱼ²)^0,5) — preserva proporcionalidade.

Nova seção 3.6 "Normalização de Dados em MCDM" inserida entre 3.5 (Gaussian AHP) e a antiga 3.6 (Correção
de Pearson, renumerada para 3.7). Quatro parágrafos: (1) por que normalização é indispensável em MCDM e,
no caso do AHP-GS especificamente, por que ela afeta diretamente o Fator Gaussiano (σ/μ); (2) os 4
procedimentos do artigo citado, com as fórmulas; (3) evidência de que a escolha do método de normalização
não é neutra — o próprio artigo encontrou variações relevantes de ranking ao trocar de norma em dois
datasets reais do Ceará (IDHM e urbanização), achado consistente com a literatura mais ampla de MCDM;
(4) o argumento central que fecha a seção: o método valor/valor máximo usado nesta dissertação (Seção
5.3.3) foi escolhido porque, sendo uma divisão por uma constante por coluna, ele preserva exatamente a
razão σ/μ (matematicamente: escalar x por 1/c escala μ e σ pelo mesmo fator c, preservando o quociente),
enquanto o min-max, por ser uma transformação afim (não escalar), distorceria essa razão — o que
comprometeria o próprio mecanismo de ponderação do AHP-GS. Esse último ponto é uma dedução matemática
direta, não estava explícito no artigo, mas decorre logicamente da coluna "Keep the proportionality?" da
Tabela 1 do artigo.

Outras referências trazidas (verificadas via busca na web, com DOI/link para o usuário confirmar):
- MILANI, A. S.; SHANIAN, A.; MADOLIAT, R.; NEMES, J. A. (2005). "The effect of normalization norms in
  multiple attribute decision making models: a case study in gear material selection." Structural and
  Multidisciplinary Optimization, v. 29, n. 4, p. 312–318. DOI: 10.1007/s00158-004-0473-1.
- JAHAN, A.; EDWARDS, K. L. (2015). "A state-of-the-art survey on the influence of normalization
  techniques in ranking: Improving the materials selection process in engineering design." Materials &
  Design, v. 65, p. 335–342. (DOI não confirmado com certeza suficiente — não incluído na referência para
  evitar citar um DOI errado; a citação de volume/página foi confirmada via um artigo que cita este mesmo
  trabalho.)
- VAFAEI, N.; RIBEIRO, R. A.; CAMARINHA-MATOS, L. M. (2018). "Data normalisation techniques in decision
  making: case study with TOPSIS method." International Journal of Information and Decision Sciences,
  v. 10, n. 1, p. 19–38. DOI: 10.1504/IJIDS.2018.090667.

Trecho de metodologia (inserido logo após os 5 passos da variante AHP-GS-P, Seção 5.3.2): explica que o
limiar de 0,8 é uma versão deliberadamente mais conservadora do corte "0,7" mais comumente citado na
literatura de colinearidade/multicolinearidade (Dormann et al., 2013 — Ecography, DOI confirmado), e
argumenta por que abaixo de 0,8 a correção não compensaria o risco de atenuar diferenças de peso
legítimas. Referência adicionada:
- DORMANN, C. F. et al. (2013). "Collinearity: a review of methods to deal with it and a simulation study
  evaluating their performance." Ecography, v. 36, n. 1, p. 27–46. DOI: 10.1111/j.1600-0587.2012.07348.x.

Nota sobre veracidade: os 4 links/DOIs acima foram obtidos via busca na web e conferidos em pelo menos uma
fonte (geralmente a página do periódico, Springer, ou um artigo que cita o mesmo trabalho com a
referência completa). O usuário pediu explicitamente os links para poder verificar por conta própria —
recomendo essa conferência antes da entrega final, sobretudo para o DOI da Jahan e Edwards (2015), que
não incluí por não ter confirmação de fonte direta (ScienceDirect bloqueou o acesso automatizado).

5 novas entradas na lista de Referências (ordem alfabética): CAVALCANTE E SILVA (após BELTON), DORMANN
(após DHARMADHIKARI), JAHAN (após JACOB), MILANI (após MEZA), VAFAEI (após TAHA). O artigo-fonte
(Cavalcante e Silva et al., 2025) foi citado como manuscrito não publicado, com link do repositório GitHub
do próprio artigo (https://github.com/arthurzueiro123/AHP_gaussian) como forma de verificação, já que não
foi encontrado indexado em nenhuma base (é um trabalho do próprio grupo de pesquisa do Levy, ainda em
fase de seminário/pré-print).

Validação: 0 travessões após a adição; heading numbering confirmado 3.5→3.6(novo)→3.7(Correção de
Pearson, renumerada); verificação visual via PDF nas páginas da nova seção 3.6, do trecho de metodologia,
e das 5 novas referências (todas numeradas corretamente pela lista automática do Word, sem colisão).
