# DEA-AHP-GS — Método Híbrido de Decisão Multicritério

> Dissertação de Mestrado: **"DEA-GS: Um Método Híbrido de Análise Envoltória de Dados Gaussiana para Suporte à Decisão Multicritério"**
> Programa de Pós-graduação em Informática Aplicada — Universidade de Fortaleza (UNIFOR), 2026.
>
> **Mestrando:** Levy Galas Jacob
> **Orientador:** Prof. Dr. Plácido Rogério Pinheiro

Desenvolvimento de um método híbrido de suporte à decisão: DEA (Data Envelopment Analysis / Análise Envoltória de Dados) e AHP Gaussiano com Correção de Pearson.

## Sobre o método

O **DEA-GS** combina a Análise Envoltória de Dados (DEA) com o Processo Analítico Hierárquico Gaussiano (AHP Gaussiano), propondo pesos objetivos por critério (via fator gaussiano σ/μ) em substituição à resolução de um problema de programação linear por DMU. Isso reduz a complexidade computacional de O(n⁴) (DEA clássico) para O(n×m²), permitindo aplicar benchmarking de eficiência multicritério em escalas antes inviáveis.

O método foi validado em 4 estudos de caso reais, cada um documentado em sua própria pasta:

| Caso | Pasta | Domínio | Escala (DMUs) |
|---|---|---|---|
| 1 | [`caso1-restaurantes/`](caso1-restaurantes) | Benchmarking operacional em rede de restaurantes | 4 |
| 2 | [`caso2-aws/`](caso2-aws) | Avaliação de arquiteturas de nuvem AWS | — |
| 3 | [`caso3-educacao-publica/`](caso3-educacao-publica) | Alocação de recursos na educação pública brasileira (INEP/FNDE) | 31.061 |
| 4 | [`caso4-llm-apis/`](caso4-llm-apis) | Benchmarking de eficiência operacional de APIs de LLM | 5 modelos |

Cada pasta contém o(s) notebook(s)/script de implementação, os dados de resultado (`dados/`) e os gráficos de fronteira de eficiência (`graficos/`, quando houver).

## Estrutura do repositório

```
.
├── caso1-restaurantes/
├── caso2-aws/
├── caso3-educacao-publica/
└── caso4-llm-apis/
```
