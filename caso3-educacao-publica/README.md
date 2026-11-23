# Caso 3 — Alocação Eficiente de Recursos na Educação Pública Brasileira

## Contexto e problema

O Plano Nacional de Educação para o decênio 2026-2036 estabelece, para o ensino fundamental, duas metas estruturantes: assegurar que ao menos 95% dos estudantes concluam essa etapa na idade regular e que, ao final do ensino fundamental, pelo menos 85% dos alunos atinjam níveis adequados de aprendizagem. Este estudo aplicou o método DEA-GS para avaliar a eficiência relativa de **31.061 escolas públicas brasileiras** que atenderam aos anos finais do ensino fundamental em 2023, com dados consolidados a partir do INEP e do FNDE.

Este caso foi selecionado, sobretudo, como prova empírica da tese de escalabilidade defendida na dissertação: com n = 31.061 DMUs, é o maior conjunto de dados avaliado — um benchmarking de eficiência nessa escala está, na prática, fora do alcance dos modelos DEA clássicos (CRS/VRS), que exigem a resolução de um problema de programação linear independente para cada DMU.

Diferente dos Casos 1 e 2, este estudo incorporou ainda uma etapa de seleção de atributos com IA Explicável (SHAP), dada a alta dimensionalidade inicial dos microdados (41 atributos candidatos).

## Modelo DEA

- **Inputs:** acesso à internet para aprendizagem, laboratório de informática, quadra de esportes, acesso à internet para alunos, equipamento de TV por aluno, laboratório de ciências, média de horas-aula (EF).
- **Outputs:** IDEB (quanto maior, melhor) e Taxa de Abandono no EF (quanto menor, melhor — invertida na normalização).

## Conteúdo desta pasta

- `fix_dea_gs.py` — script de normalização e cálculo de eficiência (DEA-GS) aplicado aos microdados do caso.
- `notas_metodologicas.md` — rascunho de texto/decisões metodológicas do capítulo da dissertação referente a este caso.
- `dados/` — planilhas de resultado: pesos do AHP Gaussiano por critério (`gaussian_weights_summary.xlsx`), inputs/outputs ponderados (`weighted_inputs_corrected.xlsx`, `weighted_outputs_corrected.xlsx`) e o ranking final de eficiência (`dea_results_corrected.xlsx`).
- `graficos/grafico_fronteira_educacao_v4.png` — gráfico da fronteira de eficiência.

> Observação: `fix_dea_gs.py` espera os dados brutos de entrada em `caso3_data/dados_input_educacao.xlsx` (microdados INEP/FNDE), não incluído neste repositório pelo tamanho/sensibilidade do arquivo original.
