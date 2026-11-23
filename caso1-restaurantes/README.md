# Caso 1 — Benchmarking Operacional no Varejo Alimentar

**Síntese:** *"Implementação da DEA com AHP Gaussiano e Correção de Pearson para Avaliação de Eficiência em uma rede de restaurantes"* (57º SBPO).

## Modelo DEA

- **Inputs:** Custo Total + Volume de Vendas
- **DMUs:** Rede de 4 restaurantes (Agosto/23 a Abril/24)
- **Output:** Lucro Bruto

## O problema

O setor alimentar opera com margens estreitas e sofre forte pressão socioeconômica. Redes de restaurantes enfrentam dificuldade para identificar com clareza quais de suas unidades (DMUs) realmente operam na fronteira de eficiência, devido ao alto volume de dados ruidosos (anomalias em notas fiscais, picos em feriados) e à variabilidade de escala (VRS) entre lojas de tamanhos diferentes.

## Descobertas

O modelo evidenciou empiricamente a performance de cada unidade: o Restaurante A formou a fronteira de eficiência (Score 1º), equilibrando custos controlados e alta conversão de lucro. Unidades menos eficientes, como o Restaurante B, puderam ser isoladas e encaminhadas para intervenções de gestão (ciclos PDCA), com foco no controle de desperdício e na elevação do ticket médio.

## Conteúdo desta pasta

- `DEA_AHPGS_RESTAURANT_levy.ipynb` — implementação do método híbrido DEA-GS (o utilizado na dissertação).
- `método_DEA_PURO_case_restaurantes.ipynb` — notebook de comparação com o DEA clássico (CRS/VRS).
- `dados/Restaurant dataset.csv` — dataset bruto de entrada.
- `dados/Comparação restaurante DEAGS-CRS-VRS.xlsx` — comparação de resultados entre DEA-GS e DEA clássico.

## Referência

JACOB, L. G.; PINHEIRO, P. R.; DUARTE, J. B. F. Implementing DEA with Gaussian AHP and Pearson Correction for Efficiency Benchmarking in a Food Retail Chain. In: VISVIZI, A.; TROISI, O.; SERRADELL-LÓPEZ, E. (ed.). Research and Innovation Forum 2025. Cham: Springer, 2026. v. 1. (Springer Proceedings in Complexity).
