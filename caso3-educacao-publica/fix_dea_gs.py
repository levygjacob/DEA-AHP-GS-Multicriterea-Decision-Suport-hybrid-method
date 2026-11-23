import pandas as pd
import numpy as np

# 1. Load raw data
df = pd.read_excel('caso3_data/dados_input_educacao.xlsx')
assert df['Escola_Inep_Ano'].is_unique

# 2. Define input/output columns per the article's stated methodology
input_cols = ["IN_INTERNET_APRENDIZAGEM", "IN_LABORATORIO_INFORMATICA", "IN_QUADRA_ESPORTES",
              "IN_INTERNET_ALUNOS", "EQUIP_TV_POR_ALUNO", "IN_LABORATORIO_CIENCIAS", "MÉDIA HORAS-AULA EF"]
output_cols = ["IDEB", "TAXA DE ABANDONO EF"]  # IDEB desirable (max); Taxa de Abandono inverse (min)

# 3. Correct max-based normalization with monotonicity (matches article's x'=x/max(x), inverse for "min")
df_norm = df.copy()
for col in input_cols + ["IDEB"]:
    max_val = df[col].max()
    df_norm[col] = df[col] / max_val if max_val != 0 else 0.0
# Taxa de Abandono: lower is better -> invert after max-normalizing (bounded [0,1])
max_ta = df["TAXA DE ABANDONO EF"].max()
df_norm["TAXA DE ABANDONO EF"] = 1 - (df["TAXA DE ABANDONO EF"] / max_ta) if max_ta != 0 else 0.0

# 4. Load the ALREADY-correct Gaussian-AHP weights (per-criterion, constant across DMUs)
weights_df = pd.read_excel('caso3_data/gaussian_weights_summary.xlsx')
w = dict(zip(weights_df['Criterion'], weights_df['Normalized Gaussian Weight']))
print("Weights loaded:", w)

# 5. Apply weights (value x weight), broadcast same weight vector to every DMU
inputs_normalized = df_norm[input_cols]
outputs_normalized = df_norm[output_cols]
inputs_weighted = inputs_normalized.mul(pd.Series({c: w[c] for c in input_cols}))
outputs_weighted = outputs_normalized.mul(pd.Series({c: w[c] for c in output_cols}))

weighted_sum_inputs = inputs_weighted.sum(axis=1)
weighted_sum_outputs = outputs_weighted.sum(axis=1)

efficiency = weighted_sum_outputs / weighted_sum_inputs
relative_efficiency = efficiency / efficiency.max()

df_results = pd.DataFrame({
    'Criteria': df['Escola_Inep_Ano'],
    'Weighted Inputs': weighted_sum_inputs,
    'Weighted Outputs': weighted_sum_outputs,
    'Efficiency': efficiency,
    'Relative Efficiency': relative_efficiency
})
df_results = df_results.sort_values('Efficiency', ascending=False).reset_index(drop=True)
df_results['Ranking'] = df_results['Efficiency'].rank(ascending=False, method='min').astype(int)

print("\nN DMUs:", len(df_results))
print(df_results.describe().to_string())
print("\nAny inf/nan?", np.isinf(df_results[['Efficiency','Relative Efficiency']]).any().any(), df_results[['Efficiency','Relative Efficiency']].isna().any().any())
print("\nSchools at exact 1.0 relative efficiency:", (df_results['Relative Efficiency']>=0.999999).sum())

df_results.to_excel('caso3_data/dea_results_corrected.xlsx', index=False)
inputs_weighted.assign(Criteria=df['Escola_Inep_Ano']).to_excel('caso3_data/weighted_inputs_corrected.xlsx', index=False)
outputs_weighted.assign(Criteria=df['Escola_Inep_Ano']).to_excel('caso3_data/weighted_outputs_corrected.xlsx', index=False)

print("\n--- TOP 10 ---")
print(df_results.head(10).to_string())
print("\n--- BOTTOM 10 ---")
print(df_results.tail(10).to_string())
