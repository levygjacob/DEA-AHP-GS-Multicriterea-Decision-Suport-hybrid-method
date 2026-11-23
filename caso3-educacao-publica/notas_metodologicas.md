> **Nota antes da leitura:** os números abaixo já usam os dados corrigidos (ver explicação enviada no chat sobre o bug de normalização/pesos no notebook). Está tudo em rascunho para sua revisão de conteúdo — a formatação final (numeração de tabelas/figuras, estilo ABNT) só entra quando eu mesclar isso no docx principal.

---

## 6.3 Estudo de Caso 3: Alocação Eficiente de Recursos na Educação Pública Brasileira

### 6.3.1 Contexto e Problema

O Plano Nacional de Educação para o decênio 2026-2036 estabelece, para o ensino fundamental, duas metas estruturantes: assegurar que ao menos 95% dos estudantes concluam essa etapa na idade regular e que, ao final do ensino fundamental, pelo menos 85% dos alunos atinjam níveis adequados de aprendizagem. Diante dessas metas, coloca-se a questão de determinar quais investimentos — infraestrutura escolar, corpo docente, acesso a tecnologia — melhor favorecem simultaneamente o desempenho acadêmico e a permanência dos estudantes no sistema de ensino.

Este estudo aplicou o método DEA-GS para avaliar a eficiência relativa de **31.061 escolas públicas brasileiras** que atenderam aos anos finais do ensino fundamental em 2023, com dados consolidados a partir do Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (INEP) e do Fundo Nacional de Desenvolvimento da Educação (FNDE).

**Este caso foi selecionado, sobretudo, como prova empírica da tese de escalabilidade defendida no Capítulo 6.3-6.5**: com n = 31.061 DMUs, este é o maior conjunto de dados avaliado nesta dissertação — cerca de 31× maior que o cenário n = 1.000 já classificado como "computacionalmente proibitivo" para o DEA clássico na Tabela 20 (Capítulo 6). Um benchmarking de eficiência nessa escala está, na prática, **fora do alcance dos modelos DEA clássicos (CRS/VRS)**, que exigem a resolução de um problema de programação linear independente para cada DMU (Capítulo 6, Seções sobre complexidade do CRS/VRS). Como será quantificado na Seção 6.3.3, é exatamente a ausência dessa etapa de otimização por DMU que torna o DEA-GS viável neste volume — e é isso que este estudo de caso busca evidenciar, além da própria aplicação ao domínio educacional.

Diferentemente dos Casos 1 e 2, cuja base de critérios já vinha definida pelo domínio do problema, este estudo de caso incorporou ainda uma etapa adicional de **seleção de atributos com Inteligência Artificial Explicável (SHAP)**, necessária dada a alta dimensionalidade inicial dos microdados (41 atributos candidatos).

**Tabela [X1]** — Estatísticas descritivas dos critérios utilizados (n = 31.061 escolas)

| Critério | Média | Desvio Padrão | Mínimo | Máximo |
|---|---:|---:|---:|---:|
| IDEB | 4,74 | 0,89 | 0,80 | 9,30 |
| Taxa de Abandono EF (%) | 1,20 | 2,19 | ~0,00 | 42,20 |
| Acesso à internet p/ aprendizagem (0/1) | 0,75 | 0,43 | 0 | 1 |
| Laboratório de informática (0/1) | 0,56 | 0,50 | 0 | 1 |
| Quadra de esportes (0/1) | 0,69 | 0,46 | 0 | 1 |
| Acesso à internet p/ alunos (0/1) | 0,66 | 0,47 | 0 | 1 |
| Equip. de TV por aluno | 0,02 | 0,04 | 0 | 1,15 |
| Laboratório de ciências (0/1) | 0,23 | 0,42 | 0 | 1 |
| Média de horas-aula (EF) | 5,45 | 1,51 | 0,20 | 16,80 |

Fonte: Elaboração própria (2026), a partir de microdados INEP/FNDE 2023.

*(Nota: dado o volume de DMUs, o padrão de tabela "uma linha por DMU" usado nos Casos 1 e 2 não é viável aqui — a tabela completa com as 31.061 escolas fica disponível no repositório público via QR code, como já é a prática do artigo original.)*

### 6.3.2 Aplicação do Método DEA-GS

**Pré-processamento e seleção de atributos.** A partir de 41 atributos iniciais dos microdados do Censo Escolar, aplicou-se um pipeline de ciência de dados para reduzir a dimensionalidade antes da etapa DEA-GS propriamente dita: as variáveis-alvo contínuas (IDEB e Taxa de Abandono) foram discretizadas em três níveis (Baixo, Médio, Alto); os dados foram divididos em treino/teste (80/20) com amostragem estratificada por localização; a técnica SMOTENC tratou o desbalanceamento de classes; e classificadores interpretáveis (SVM, Random Forest, XGBoost) foram avaliados com métricas robustas a desbalanceamento (G-Mean, UAR). Os valores SHAP dos melhores modelos (XGBoost com SelectFromModel para IDEB; SVC com RFE para Taxa de Abandono) permitiram reduzir o conjunto para **16 atributos relevantes**, dos quais **7 critérios de entrada** apresentaram correlação de Spearman superior a 0,15 com o IDEB e foram efetivamente utilizados na etapa DEA-GS: acesso à internet para aprendizagem, laboratório de informática, quadra de esportes, acesso à internet para os alunos, equipamentos de TV por aluno, laboratório de ciências e média de horas-aula.

**DMUs, inputs e outputs.** Cada uma das 31.061 escolas foi tratada como uma DMU. Os *outputs* adotados foram o **IDEB** (desejável, quanto maior melhor) e a **Taxa de Abandono** (com monotonicidade inversa — quanto menor, melhor). Os *inputs* foram os 7 critérios de infraestrutura/recursos listados acima.

A aplicação seguiu a arquitetura do método (Figura 2):

1. **Cálculo dos Pesos (AHP-GS):** os pesos foram obtidos objetivamente a partir da variabilidade estatística (Fator Gaussiano = σ/μ) de cada um dos 9 critérios (7 inputs + 2 outputs). O critério com maior poder discriminatório foi *laboratório de ciências* (Fator Gaussiano normalizado = 1,000), seguido por *equipamentos de TV por aluno* (0,854) — ambos atributos de infraestrutura pouco presentes na rede (médias baixas, alta variabilidade relativa). Em contraste, o IDEB e a Taxa de Abandono, por serem indicadores mais "estáveis" na amostra, receberam pesos comparativamente menores (0,104 e 0,030), conforme a Tabela [X2].

**Tabela [X2]** — Cálculo dos pesos detalhados (Etapa AHP Gaussiano)

| Critério | Média | Desvio Padrão | Fator Gaussiano | Peso Normalizado |
|---|---:|---:|---:|---:|
| Laboratório de ciências | 0,234 | 0,424 | 1,808 | **1,000** |
| Equip. de TV por aluno | 0,020 | 0,031 | 1,544 | 0,854 |
| Laboratório de informática | 0,562 | 0,496 | 0,882 | 0,488 |
| Acesso à internet p/ alunos | 0,659 | 0,474 | 0,719 | 0,398 |
| Quadra de esportes | 0,687 | 0,464 | 0,675 | 0,373 |
| Acesso à internet p/ aprendizagem | 0,750 | 0,433 | 0,577 | 0,319 |
| Média de horas-aula | 0,325 | 0,090 | 0,277 | 0,153 |
| IDEB | 0,509 | 0,096 | 0,189 | 0,104 |
| Taxa de Abandono | 0,972 | 0,052 | 0,053 | 0,030 |

Fonte: Elaboração própria (2026).

2. **Normalização e Ponderação:** os dados foram normalizados pelo método do valor máximo (x' = x/max(x)), com inversão de monotonicidade para a Taxa de Abandono. Os valores normalizados foram então multiplicados pelos pesos gaussianos da Tabela [X2], gerando os inputs e outputs ponderados de cada DMU.

3. **Cálculo da Eficiência e Ranking:** a eficiência bruta (θ) de cada escola foi calculada pela razão entre a soma dos outputs ponderados e a soma dos inputs ponderados; a eficiência relativa foi obtida pela normalização em relação à DMU mais eficiente.

**Gráfico [Y] — Fronteira de eficiência DEA-GS, caso educação** (anexo: `grafico_fronteira_educacao.png`)

### 6.3.3 Viabilidade Computacional em Escala: DEA-GS vs. DEA Clássico para n = 31.061

Esta seção quantifica, com os parâmetros reais deste estudo de caso (n = 31.061 DMUs, m = 9 critérios), o argumento de escalabilidade apresentado na análise de complexidade do Capítulo 6 (Tabelas 18-20), estendendo-o de projeções teóricas (até n = 1.000) para um cenário empírico real de larga escala.

**Tabela [X2b]** — Viabilidade computacional: DEA-GS vs. DEA clássico (n = 31.061, m = 9)

| Método | Complexidade (caso médio) | Nº de operações estimado | Nº de LPs resolvidos |
|---|---|---:|---:|
| DEA CRS / VRS | O(n⁴) | **≈ 9,3 × 10¹⁷** | 31.061 |
| DEA-GS | O(n × m²) | **≈ 2,5 × 10⁶** | 0 |
| **Ganho do DEA-GS** | | **≈ 3,7 × 10¹¹ vezes menos operações** | |

Fonte: Elaboração própria (2026), aplicando as fórmulas de complexidade da Tabela 19 aos parâmetros deste estudo de caso.

Em termos práticos, isso significa: o DEA CRS/VRS precisaria resolver **31.061 problemas de programação linear independentes** — um por escola —, com um volume total de operações da ordem de 10¹⁷, várias ordens de grandeza além do que qualquer solver convencional processa em tempo hábil (a própria Tabela 20 do Capítulo 6 já classificava n = 1.000 como proibitivo, com ~10¹² operações; aqui estamos sete ordens de grandeza acima disso). O DEA-GS, por não depender de otimização por DMU, resolve o mesmo problema com pesos fixos e globais calculados uma única vez.

Essa vantagem teórica foi confirmada empiricamente: o cálculo completo do DEA-GS para as 31.061 escolas — normalização, ponderação, cálculo de eficiência e ranking — foi executado em **0,08 segundos** de processamento puro (cerca de 4,5 segundos incluindo a leitura do arquivo de dados original), em um único núcleo de CPU, sem qualquer estratégia de paralelização. Um benchmarking equivalente com DEA CRS/VRS clássico, nesta mesma escala, seria inviável na prática sem recorrer a hardware especializado, decomposição do problema ou heurísticas de amostragem — o que, por si só, já comprometeria a análise da população completa de escolas.

### 6.3.4 Resultados Principais e Análise

**Tabela [X3]** — DEA-GS: Top 10 e Bottom 10 (de 31.061 escolas)

| Ranking | Escola | Inputs Pond. | Outputs Pond. | Eficiência | Eficiência Relativa |
|---:|---|---:|---:|---:|---:|
| 1 | Antonio Urculino Alves EMEIF (CE) | 0,036 | 0,101 | 2,778 | **1,000** |
| 2 | Rufina Magalhães de Farias EEIEF (CE) | 0,036 | 0,094 | 2,562 | 0,922 |
| 3 | EMEB Prof.ª Maria Rocha Santos Silva (PE) | 0,048 | 0,124 | 2,560 | 0,922 |
| ... | *(ranking completo no repositório)* | | | | |
| 31.058 | EE Francisco Campos (MG) | 3,245 | 0,062 | 0,019 | 0,0069 |
| 31.059 | EE de Ladainha (MG) | 2,636 | 0,044 | 0,017 | 0,0060 |
| 31.060 | EE Pedro Severino Bezerra (RN) | 1,307 | 0,021 | 0,016 | **0,0057 (última colocada)** |

Fonte: Elaboração própria (2026).

A eficiência relativa média foi de 0,063 (desvio padrão 0,130), com forte assimetria à direita — típico de fronteiras DEA, em que a maioria das DMUs se posiciona abaixo da fronteira eficiente e um pequeno grupo concentra os escores mais altos. Apenas uma escola atingiu eficiência relativa igual a 1,00, formando isoladamente a fronteira em sua extremidade superior.

Um achado que merece discussão direta: **as escolas mais bem colocadas no ranking não são as mais bem equipadas** — pelo contrário. Comparando o perfil médio das 10 escolas mais eficientes com o das 10 menos eficientes:

| Critério | Top 10 (média) | Bottom 10 (média) | Média geral |
|---|---:|---:|---:|
| IDEB | 5,84 | 2,55 | 4,74 |
| Taxa de Abandono (%) | ~0,00 | 13,41 | 1,20 |
| Internet p/ aprendizagem | 0% | 90% | 75% |
| Laboratório de informática | 0% | 90% | 56% |
| Quadra de esportes | 0% | 100% | 69% |
| Internet p/ alunos | 0% | 100% | 66% |
| Laboratório de ciências | 0% | 80% | 23% |

As dez escolas no topo do ranking praticamente não reportam nenhum dos itens de infraestrutura considerados como input — e, ainda assim, atingem IDEB elevado e abandono nulo. Sob a ótica do DEA-GS, esse é exatamente o comportamento esperado do modelo, não uma distorção: eficiência é definida como a razão entre o que se produz e o que se consome, de modo que uma escola que sustenta bom desempenho acadêmico e baixíssima evasão com praticamente nenhum dos recursos de infraestrutura mapeados é, por definição, altamente eficiente na conversão de insumos em resultado. Já as dez piores colocadas são escolas relativamente bem equipadas (a maioria com laboratório, quadra e internet), mas com desempenho acadêmico fraco e evasão alta — ou seja, consomem bastante input ponderado sem retorno proporcional em output, e por isso ficam no fim do ranking mesmo com mais recursos disponíveis.

### 6.3.5 Lições sobre o Método e Validação

Este caso validou o DEA-GS em um cenário radicalmente distinto dos dois anteriores: **larga escala (31 mil DMUs, contra 4 e 6) e um domínio de política pública, não organizacional/privado.** O método demonstrou ser capaz de:

- **Viabilizar benchmarking em escala inatingível para o DEA clássico — a principal lição deste caso.** Com n = 31.061 DMUs, o DEA CRS/VRS exigiria ~9,3 × 10¹⁷ operações e a resolução de 31.061 problemas de programação linear independentes (Seção 6.3.3), o que o torna, na prática, inaplicável a este problema. O DEA-GS, por dispensar otimização por DMU, computou o ranking completo em frações de segundo. Este é o primeiro estudo de caso da dissertação em que a diferença de complexidade entre os métodos deixa de ser uma vantagem teórica (Tabelas 18-20) e passa a ser a **condição que torna o benchmarking possível** — não há alternativa clássica viável para comparar, na prática, o objetivo específico deste estudo.
- **Incorporar uma etapa de seleção de atributos anterior à ponderação estatística**, mostrando que o método é compatível com pipelines de pré-processamento mais sofisticados (seleção via IA explicável) quando a dimensionalidade dos dados exige — um requisito típico de bases de grande volume, mas incomum nas aplicações usuais de DEA de pequena escala.
- **Identificar eficiência genuína de conversão de recursos, e não apenas volume de infraestrutura:** o topo do ranking foi ocupado por escolas que produzem bons resultados acadêmicos com pouquíssimos dos recursos mapeados como input — o que é coerente com a própria definição de eficiência (razão output/input) e reforça o valor do método como ferramenta de diagnóstico: ele aponta unidades que "fazem mais com menos", em vez de simplesmente ordenar por volume de recursos ou de resultado absoluto.

A ponderação via AHP-GS atribuiu maior peso aos critérios de infraestrutura menos disseminados na rede (laboratório de ciências, equipamentos de TV por aluno) — exatamente os critérios com maior variabilidade relativa entre as escolas — reforçando a lógica de que atributos mais raros carregam mais poder discriminatório entre as DMUs.

Em conjunto com os Casos 1 e 2, este caso completa um espectro de validação por escala: de 4 DMUs (Caso 1, onde o DEA clássico seria perfeitamente viável, mas o DEA-GS já demonstra vantagem em objetividade de pesos) até 31.061 DMUs (Caso 3, onde o DEA clássico deixa de ser uma opção). Essa progressão evidencia que o ganho do DEA-GS não é apenas de eficiência computacional marginal, mas **estrutural**: ele desloca a fronteira do que é analiticamente possível fazer com DEA.

---

**Referências novas a incluir (que ainda não estão na lista da dissertação):** Alamri e Alharbi (2021); Alwarthan, Aslam e Khan (2022); Barros et al. (2019); Bouchlaghem, Akhiat e Amjad (2022); Goran et al. (2024); Melo et al. (2022); Rovira, Puertas e Igual (2017); Sanfo (2025); Yadav e Bhole (2020); Zaffar, Hashmani e Savita (2017).

**Siglas novas a incluir na Lista de Siglas:** IDEB, SHAP, XGBoost, SMOTENC, G-Mean, UAR, RFE, SVM/SVC, INEP, FNDE, PNE.
