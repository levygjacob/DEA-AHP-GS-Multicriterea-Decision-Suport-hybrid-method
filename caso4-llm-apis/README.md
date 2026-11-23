# Caso 4 — Benchmarking de Eficiência Operacional de APIs de LLM

**DMUs:** 5 modelos de LLM (Claude Haiku 4.5, Claude Sonnet 4.5, DeepSeek Chat, Gemini 2.5 Flash, GPT-4o mini), avaliados via DEA-GS sobre métricas agregadas de dois benchmarks de QA (Natural Questions + SQuAD v2), totalizando 20.715 execuções.

## Inputs / Outputs

- **Inputs:** Tokens de Entrada (total), Custo de Entrada (US$)
- **Outputs:** Razão Saída/Entrada, Tokens de Saída (total), Custo de Saída (US$)

## Conteúdo desta pasta

- `DEA_AHPGS_AI.ipynb` — notebook com a implementação do método DEA-GS aplicado às execuções de benchmark das APIs de LLM.
- `dea_gaussian_llm_benchmarking.py` — módulo de instrumentação: padroniza as chamadas às APIs de LLM (OpenAI, Gemini, DeepSeek) e coleta métricas comparáveis de latência, tokens e custo (ver detalhes de uso abaixo).
- `notas_metodologicas.md` — histórico de decisões metodológicas tomadas durante a análise deste caso (pesos, normalização).
- `graficos/` — gráficos da fronteira de eficiência.

---

## Sobre o módulo de instrumentação (`dea_gaussian_llm_benchmarking.py`)

> Instrumentação e benchmark multicritério de APIs de LLM para RAG/Agents, combinando AHP Gaussiano (ponderação) e DEA (eficiência) — com coleta padronizada de métricas de latência, tokens, custo e qualidade (extensível).

### O que este módulo faz

- Chamada padronizada às APIs de LLM (OpenAI, Gemini, DeepSeek) em modo não-stream, com latência total, tokens in/out (via `usage` da API ou estimativa local), custo calculado por USD/1k tokens, texto de saída e metadados HTTP/ID.
- **Benchmark QA:** roda perguntas/contexts de um CSV padronizado e grava resultados.
- **Persistência:** `runs.jsonl`, `runs.csv`, `runs.sqlite`.
- **Exportador de datasets** (SQuAD v2, Natural Questions) para CSV no formato esperado.

### Arquitetura do código (OOP)

```
LLMClient (classe base)
 ├─ OpenAIClient     (provider="openai")
 ├─ GeminiClient     (provider="gemini")
 └─ DeepSeekClient   (provider="deepseek")

BenchmarkRunner  -> orquestra o loop sobre o CSV de QA e chama client.run(...)
MetricsRecorder  -> escreve JSONL, CSV e SQLite com o mesmo schema
PRICING_REGISTRY -> tabela de preços USD/1k tokens por provider/modelo
```

### Instalação

```bash
pip install openai>=1.35.0 google-generativeai>=0.7.2 tiktoken>=0.7.0 datasets>=2.20.0 tqdm python-dotenv
```

```bash
export OPENAI_API_KEY="..."
export GOOGLE_API_KEY="..."
export DEEPSEEK_API_KEY="..."
```

### Como rodar

```bash
# Exportar dataset de QA (opcional)
python dea_gaussian_llm_benchmarking.py export_qa squad_v2 "validation[:2000]" data/qa/qa_squad_v2_val.csv --streaming

# Rodar benchmark
python dea_gaussian_llm_benchmarking.py openai gpt-4.1-mini data/qa/qa_squad_v2_val.csv outputs/
python dea_gaussian_llm_benchmarking.py gemini gemini-1.5-flash data/qa/qa_nq_val.csv outputs/
python dea_gaussian_llm_benchmarking.py deepseek deepseek-chat data/qa/qa_squad_v2_val.csv outputs/
```

### Pricing (USD/1k tokens, configurável em `PRICING_REGISTRY`)

- **OpenAI:** `gpt-4o-mini` (in 0.00060, out 0.00240), `gpt-4.1-mini` (in 0.00040, out 0.00160)
- **Gemini:** `gemini-1.5-pro` (in 0.00125, out 0.00500), `gemini-1.5-flash` (in 0.000075, out 0.00030)
- **DeepSeek:** `deepseek-chat` / `deepseek-reasoner` (in 0.00028, out 0.00042)

Ajuste estes números conforme contrato/recência.
