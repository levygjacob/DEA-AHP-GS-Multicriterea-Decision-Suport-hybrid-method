"""
DEA GAUSSIAN LLM — v0 Instrumentação de Benchmark
Autores: Levy Jacob | Thiago Bluhm | Dr. Plácido | Dr. Furlan
Descrição: Camada de instrumentação para chamadas padronizadas às APIs de LLM
(OpenAI e Gemini), com coleta de métricas (tempo, tokens e custo) e persistência
em JSONL/CSV/SQLite. Arquitetura OOP (OOM) para facilitar a expansão para novos
provedores.

Requisitos (pip):
  openai>=1.35.0
  google-generativeai>=0.7.2
  tiktoken>=0.7.0
  datasets>=2.20.0

Variáveis de ambiente:
  OPENAI_API_KEY  -> chave OpenAI
  GOOGLE_API_KEY  -> chave Gemini

Observações:
- v0 implementa chamada não-stream por simplicidade; TTFT fica como None.
- Para Gemini, tenta usar usage_metadata; se indisponível, faz estimativa local.
- Preços são configuráveis via PRICING_REGISTRY abaixo (USD/1k tokens).
- Dataset QA esperado: CSV com colunas [id, question, reference_answer, context?].
"""
from __future__ import annotations

import csv
import dataclasses as dc
import hashlib
import json
import os
import sqlite3
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from dotenv import load_dotenv
load_dotenv()

# Loader de datasets (opcional para exportar QA)
try:
    from datasets import load_dataset
except Exception:  # pragma: no cover
    load_dataset = None

# Barra de progresso (opcional)
try:
    from tqdm.auto import tqdm  # pip install tqdm
except Exception:  # pragma: no cover
    tqdm = None

# ---- Dependências opcionais (tratadas com fallback) ----
try:
    import tiktoken  # Para contagem local de tokens (OpenAI)
except Exception:  # pragma: no cover
    tiktoken = None

# OpenAI SDK (v1)
try:
    from openai import OpenAI as _OpenAI
except Exception:  # pragma: no cover
    _OpenAI = None

# Gemini SDK
try:
    import google.generativeai as genai
except Exception:  # pragma: no cover
    genai = None

# =============================
# Pricing (USD/1k tokens)
# =============================
# Valores oficiais convertidos para "por 1k tokens" (fonte: páginas de pricing)
# Gemini: valores padrão para prompts <= 128k tokens.
# Ajuste conforme contrato interno, se necessário.
PRICING_REGISTRY: Dict[str, Dict[str, Dict[str, float]]] = {
    # provider -> model -> {"in_1k": float, "out_1k": float, "currency": "USD"}
    "openai": {
        # GPT-4o mini — $0.60 / 1M input ; $2.40 / 1M output  =>  0.00060 ; 0.00240 per 1k
        "gpt-4o-mini": {"in_1k": 0.00060, "out_1k": 0.00240, "currency": "USD"},
        # GPT-4.1 mini — $0.40 / 1M input ; $1.60 / 1M output  =>  0.00040 ; 0.00160 per 1k
        "gpt-4.1-mini": {"in_1k": 0.00040, "out_1k": 0.00160, "currency": "USD"},
    },
    "gemini": {
        # Gemini 1.5 Pro (<=128k) — $1.25 / 1M input ; $5.00 / 1M output  =>  0.00125 ; 0.00500 per 1k
        "gemini-1.5-pro": {"in_1k": 0.00125, "out_1k": 0.00500, "currency": "USD"},
        # Gemini 1.5 Flash (<=128k) — $0.075 / 1M input ; $0.30 / 1M output  =>  0.000075 ; 0.00030 per 1k
        "gemini-1.5-flash": {"in_1k": 0.000075, "out_1k": 0.00030, "currency": "USD"},
    },
    "deepseek": {
        # DeepSeek pricing (USD per 1k tokens), usando valores de CACHE MISS para input por conservadorismo.
        # A tabela oficial exibe preços por 1M tokens; convertidos aqui para 1k:
        # 1M INPUT (CACHE MISS) = $0.28  => 0.00028 por 1k
        # 1M OUTPUT              = $0.42  => 0.00042 por 1k
        "deepseek-chat":     {"in_1k": 0.00028, "out_1k": 0.00042, "currency": "USD"},
        "deepseek-reasoner": {"in_1k": 0.00028, "out_1k": 0.00042, "currency": "USD"},
    }
}

# =============================
# Data Classes
# =============================
@dc.dataclass
class LLMParams:
    temperature: float = 0.0
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    seed: Optional[int] = None
    stream: bool = False

@dc.dataclass
class LLMResult:
    run_id: str
    example_id: str
    timestamp: float
    provider: str
    model: str
    model_version: Optional[str]
    prompt_text: str
    system_text: Optional[str]
    context_text: Optional[str]
    temperature: float
    top_p: Optional[float]
    max_tokens: Optional[int]
    seed: Optional[int]
    stream: bool
    latency_ms: float
    ttft_ms: Optional[float]
    input_tokens: int
    output_tokens: int
    total_tokens: int
    tokens_source: str  # "api" | "local_estimate"
    cost_input: float
    cost_output: float
    cost_total: float
    currency: str
    status: str  # ok | error
    http_status: Optional[int]
    error_type: Optional[str]
    retry_count: int
    request_id: Optional[str]
    output_text: Optional[str]
    truncated: bool = False
    split: Optional[str] = None
    domain: Optional[str] = None
    difficulty: Optional[str] = None

# =============================
# Abstração de Cliente LLM
# =============================
class LLMClient:
    provider: str

    def __init__(self, model: str, pricing_registry: Dict[str, Dict[str, Dict[str, float]]] = PRICING_REGISTRY):
        self.model = model
        self.pricing_registry = pricing_registry

    # --- Interface principal ---
    def generate(self, *, prompt: str, system: Optional[str], context: Optional[str], params: LLMParams) -> Tuple[str, Dict[str, Any]]:
        """Retorna (texto, raw_metadata) e DEVE ser implementado pelo provedor."""
        raise NotImplementedError

    def count_tokens(self, text: str) -> int:
        """Contagem local de tokens (heurística). Provê fallback quando a API não retorna usage."""
        return max(1, len(text) // 4)  # heurística (4 chars ~ 1 token)

    def _pricing(self) -> Tuple[float, float, str]:
        prov = self.provider
        model = self.model
        if prov not in self.pricing_registry or model not in self.pricing_registry[prov]:
            # Default genérico (evita crash em novo modelo) — RECOMENDADO configurar explicitamente
            return 1.0, 1.0, "BRL"
        p = self.pricing_registry[prov][model]
        return p.get("in_1k", 1.0), p.get("out_1k", 1.0), p.get("currency", "BRL")

    def _calc_cost(self, in_tokens: int, out_tokens: int) -> Tuple[float, float, float, str]:
        in_k, out_k, cur = self._pricing()
        cost_in = (in_tokens / 1000.0) * in_k
        cost_out = (out_tokens / 1000.0) * out_k
        return cost_in, cost_out, cost_in + cost_out, cur

    def run(self, *, example_id: str, prompt: str, system: Optional[str], context: Optional[str], params: LLMParams, split: Optional[str] = None, domain: Optional[str] = None, difficulty: Optional[str] = None) -> LLMResult:
        run_id = str(uuid.uuid4())
        t0 = time.perf_counter()
        retry_count = 0
        http_status = None
        error_type = None
        status = "ok"
        request_id = None
        output_text = None
        tokens_source = "api"
        input_tokens = 0
        output_tokens = 0
        model_version = None
        ttft_ms = None  # v0 (sem streaming)

        try:
            output_text, raw = self.generate(prompt=prompt, system=system, context=context, params=params)
            # --- Extrai usage/tokens por provedor ---
            input_tokens, output_tokens, tokens_source, model_version, request_id, http_status = self._extract_usage(raw, prompt=prompt, system=system, context=context)
        except Exception as e:
            status = "error"
            error_type = f"{type(e).__name__}: {e}"
            output_text = None
        finally:
            t1 = time.perf_counter()

        latency_ms = (t1 - t0) * 1000.0
        total_tokens = (input_tokens or 0) + (output_tokens or 0)
        cost_in, cost_out, cost_total, currency = self._calc_cost(input_tokens or 0, output_tokens or 0)

        return LLMResult(
            run_id=run_id,
            example_id=example_id,
            timestamp=time.time(),
            provider=self.provider,
            model=self.model,
            model_version=model_version,
            prompt_text=prompt,
            system_text=system,
            context_text=context,
            temperature=params.temperature,
            top_p=params.top_p,
            max_tokens=params.max_tokens,
            seed=params.seed,
            stream=params.stream,
            latency_ms=latency_ms,
            ttft_ms=ttft_ms,
            input_tokens=input_tokens or 0,
            output_tokens=output_tokens or 0,
            total_tokens=total_tokens,
            tokens_source=tokens_source,
            cost_input=cost_in,
            cost_output=cost_out,
            cost_total=cost_total,
            currency=currency,
            status=status,
            http_status=http_status,
            error_type=error_type,
            retry_count=retry_count,
            request_id=request_id,
            output_text=output_text,
            split=split,
            domain=domain,
            difficulty=difficulty,
        )

    # --- Cada cliente deve implementar seu extrator de usage ---
    def _extract_usage(self, raw: Dict[str, Any], *, prompt: str, system: Optional[str], context: Optional[str]) -> Tuple[int, int, str, Optional[str], Optional[str], Optional[int]]:
        raise NotImplementedError


# =====================================
# DeepSeek Client (OpenAI-compatible)
# =====================================
class DeepSeekClient(LLMClient):
    provider = "deepseek"

    def __init__(self, model: str):
        super().__init__(model=model)
        if _OpenAI is None:
            raise RuntimeError("Pacote openai não encontrado. Instale com: pip install openai")
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("Defina DEEPSEEK_API_KEY no ambiente.")
        # API compatível com OpenAI; muda apenas o base_url
        self.client = _OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    def generate(self, *, prompt: str, system: Optional[str], context: Optional[str], params: LLMParams) -> Tuple[str, Dict[str, Any]]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        if context:
            messages.append({"role": "user", "content": f"Contexto:\n{context}"})
        messages.append({"role": "user", "content": prompt})

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=params.temperature,
            top_p=params.top_p,
            max_tokens=params.max_tokens,
            seed=params.seed,
        )
        # DeepSeek (reasoner) pode retornar 'reasoning_content' além de 'content'
        text = (resp.choices[0].message.content or "").strip()
        raw = {
            "id": getattr(resp, "id", None),
            "usage": resp.usage.model_dump() if hasattr(resp, "usage") else None,
            "model": getattr(resp, "model", None),
            "status_code": getattr(resp, "status_code", None),
            "has_reasoning_content": hasattr(resp.choices[0].message, "reasoning_content"),
        }
        return text, raw

    def _extract_usage(self, raw: Dict[str, Any], *, prompt: str, system: Optional[str], context: Optional[str]) -> Tuple[int, int, str, Optional[str], Optional[str], Optional[int]]:
        usage = raw.get("usage") or {}
        in_tok = int(usage.get("prompt_tokens" , 0) or 0)
        out_tok = int(usage.get("completion_tokens", 0) or 0)
        tokens_source = "api" if (in_tok or out_tok) else "local_estimate"
        model_version = raw.get("model")
        request_id = raw.get("id")
        http_status = raw.get("status_code")

        if tokens_source == "local_estimate":
            in_est = self.count_tokens("\\n\\n".join(filter(None, [system, context, prompt])))
            out_est = 0
            in_tok, out_tok = in_est, out_est
        return in_tok, out_tok, tokens_source, model_version, request_id, http_status


# =============================
# OpenAI Client
# =============================
class OpenAIClient(LLMClient):
    provider = "openai"

    def __init__(self, model: str):
        super().__init__(model=model)
        if _OpenAI is None:
            raise RuntimeError("Pacote openai não encontrado. Instale com: pip install openai")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Defina OPENAI_API_KEY no ambiente.")
        self.client = _OpenAI(api_key=api_key)

    def generate(self, *, prompt: str, system: Optional[str], context: Optional[str], params: LLMParams) -> Tuple[str, Dict[str, Any]]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        if context:
            messages.append({"role": "user", "content": f"Contexto:\n{context}"})
        messages.append({"role": "user", "content": prompt})

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=params.temperature,
            top_p=params.top_p,
            max_tokens=params.max_tokens,
            seed=params.seed,
        )
        text = (resp.choices[0].message.content or "").strip()
        # Serializa partes relevantes em raw
        raw = {
            "id": getattr(resp, "id", None),
            "usage": resp.usage.model_dump() if hasattr(resp, "usage") else None,
            "model": getattr(resp, "model", None),
            "status_code": getattr(resp, "status_code", None),  # pode não existir
        }
        return text, raw

    def _extract_usage(self, raw: Dict[str, Any], *, prompt: str, system: Optional[str], context: Optional[str]) -> Tuple[int, int, str, Optional[str], Optional[str], Optional[int]]:
        usage = raw.get("usage") or {}
        in_tok = int(usage.get("prompt_tokens" , 0) or 0)
        out_tok = int(usage.get("completion_tokens", 0) or 0)
        tokens_source = "api" if (in_tok or out_tok) else "local_estimate"
        model_version = raw.get("model")
        request_id = raw.get("id")
        http_status = raw.get("status_code")

        if tokens_source == "local_estimate":
            in_est = self._count_openai_tokens("\n\n".join(filter(None, [system, context, prompt])))
            out_est = self._count_openai_tokens("")  # sem como estimar output aqui
            in_tok = in_est
            out_tok = out_est
        return in_tok, out_tok, tokens_source, model_version, request_id, http_status

    def _count_openai_tokens(self, text: str) -> int:
        if tiktoken is None:
            return super().count_tokens(text)
        try:
            enc = tiktoken.get_encoding("cl100k_base")  # aproximação para modelos 4.x
            return len(enc.encode(text))
        except Exception:
            return super().count_tokens(text)


# =============================
# Gemini Client
# =============================
class GeminiClient(LLMClient):
    provider = "gemini"

    def __init__(self, model: str):
        super().__init__(model=model)
        if genai is None:
            raise RuntimeError("Pacote google-generativeai não encontrado. pip install google-generativeai")
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("Defina GOOGLE_API_KEY no ambiente.")
        genai.configure(api_key=api_key)
        self.model_obj = genai.GenerativeModel(model_name=self.model)

    def generate(self, *, prompt: str, system: Optional[str], context: Optional[str], params: LLMParams) -> Tuple[str, Dict[str, Any]]:
        # Para v0, concatenamos system/context ao prompt
        sys_block = f"<system>\n{system}\n</system>\n" if system else ""
        ctx_block = f"<context>\n{context}\n</context>\n" if context else ""
        full_prompt = f"{sys_block}{ctx_block}{prompt}".strip()

        resp = self.model_obj.generate_content(
            full_prompt,
            generation_config={
                "temperature": params.temperature,
                "top_p": params.top_p,
                "max_output_tokens": params.max_tokens,
                # seed não é suportado universalmente em todas versões
            },
            safety_settings=None,
        )
        text = (resp.text or "").strip()

        raw = {
            "usage_metadata": getattr(resp, "usage_metadata", None),
            "model_version": getattr(resp, "model_version", None),
            "request_id": getattr(resp, "request_id", None),
            "status_code": None,  # não exposto diretamente
        }
        # Converte objeto usage_metadata se existir
        if raw["usage_metadata"] is not None:
            try:
                um = raw["usage_metadata"]
                raw["usage_metadata"] = {
                    "prompt_token_count": getattr(um, "prompt_token_count", None),
                    "candidates_token_count": getattr(um, "candidates_token_count", None),
                    "total_token_count": getattr(um, "total_token_count", None),
                }
            except Exception:
                pass
        return text, raw

    def _extract_usage(self, raw: Dict[str, Any], *, prompt: str, system: Optional[str], context: Optional[str]) -> Tuple[int, int, str, Optional[str], Optional[str], Optional[int]]:
        usage = raw.get("usage_metadata") or {}
        in_tok = usage.get("prompt_token_count")
        out_tok = usage.get("candidates_token_count")
        tokens_source = "api" if (in_tok is not None or out_tok is not None) else "local_estimate"
        model_version = raw.get("model_version")
        request_id = raw.get("request_id")
        http_status = raw.get("status_code")

        if tokens_source == "local_estimate":
            # Heurística simples; aprimorar com tokenizador compatível quando disponível.
            in_tok = self.count_tokens("\n\n".join(filter(None, [system, context, prompt])))
            out_tok = 0
        return int(in_tok or 0), int(out_tok or 0), tokens_source, model_version, request_id, http_status


# =============================
# Persistência (JSONL/CSV/SQLite)
# =============================
class MetricsRecorder:
    def __init__(self, *, jsonl_path: Optional[Path] = None, csv_path: Optional[Path] = None, sqlite_path: Optional[Path] = None):
        self.jsonl_path = Path(jsonl_path) if jsonl_path else None
        self.csv_path = Path(csv_path) if csv_path else None
        self.sqlite_path = Path(sqlite_path) if sqlite_path else None

        if self.csv_path and not self.csv_path.exists():
            with self.csv_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([f.name for f in dc.fields(LLMResult)])

        if self.sqlite_path:
            self._init_sqlite()

    def _init_sqlite(self):
        conn = sqlite3.connect(self.sqlite_path)
        c = conn.cursor()
        # Cria tabela runs
        cols = ",".join([f"{f.name} {self._sqlite_type(f.type)}" for f in dc.fields(LLMResult)])
        c.execute(
            f"CREATE TABLE IF NOT EXISTS runs ({cols});"
        )
        # Índices úteis
        c.execute("CREATE INDEX IF NOT EXISTS idx_runs_provider_model ON runs(provider, model);")
        c.execute("CREATE INDEX IF NOT EXISTS idx_runs_example ON runs(example_id);")
        conn.commit()
        conn.close()

    def _sqlite_type(self, t: Any) -> str:
        # Simplificação: usa TEXT/REAL/INTEGER
        if t in (int, Optional[int]):
            return "INTEGER"
        if t in (float, Optional[float]):
            return "REAL"
        return "TEXT"

    def record(self, result: LLMResult):
        # JSONL
        if self.jsonl_path:
            with self.jsonl_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(dc.asdict(result), ensure_ascii=False) + "\n")

        # CSV
        if self.csv_path:
            with self.csv_path.open("a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([getattr(result, fld.name) for fld in dc.fields(LLMResult)])

        # SQLite
        if self.sqlite_path:
            conn = sqlite3.connect(self.sqlite_path)
            c = conn.cursor()
            row = dc.asdict(result)
            placeholders = ",".join(["?"] * len(row))
            c.execute(
                f"INSERT INTO runs VALUES ({placeholders});",
                [row[f.name] for f in dc.fields(LLMResult)],
            )
            conn.commit()
            conn.close()


# =============================
# Loader/Exporter de Datasets QA (SQuAD v2 e Natural Questions)
# =============================

def _ensure_datasets():
    if load_dataset is None:
        raise RuntimeError("Pacote 'datasets' não encontrado. Instale com: pip install datasets")


def _row_squad_v2(ex):
    # HF squad_v2: {'id','title','context','question','answers':{'text':list,'answer_start':list}}
    answers = ex.get("answers") or {}
    texts = (answers.get("text") or [])
    ref = (texts[0] if len(texts) > 0 else "").strip()
    return {
        "id": ex.get("id") or str(uuid.uuid4()),
        "question": (ex.get("question") or "").strip(),
        "context": (ex.get("context") or "").strip(),
        "reference_answer": ref,
    }


def _row_natural_questions(ex):
    # HF natural_questions (simplificado): alguns configs têm 'answers':{'text': list}
    # outros têm 'annotations' com 'short_answers': {'text': list}
    ref = ""
    if isinstance(ex.get("answers"), dict):
        texts = ex["answers"].get("text") or []
        if len(texts) > 0:
            ref = (texts[0] or "").strip()
    elif isinstance(ex.get("annotations"), list) and ex["annotations"]:
        ann0 = ex["annotations"][0]
        sa = (ann0.get("short_answers") or {}).get("text") or []
        if len(sa) > 0:
            ref = (sa[0] or "").strip()
    return {
        "id": str(ex.get("id") or uuid.uuid4()),
        "question": (ex.get("question") or "").strip(),
        "context": (ex.get("document_text") or ex.get("context") or "").strip(),
        "reference_answer": ref,
    }


def export_qa_csv(dataset_name: str, split: str, out_csv: Path, limit: Optional[int] = None, streaming: bool = False):
    """Exporta para CSV com colunas: id,question,context,reference_answer.
    dataset_name ∈ {'squad_v2','natural_questions'}.
    split pode usar slicing do HF (ex.: 'validation[:2000]').
    Se streaming=True, evita baixar o dataset completo quando usar slicing.
    """
    _ensure_datasets()

    if dataset_name == "squad_v2":
        ds = load_dataset("squad_v2", split=split, streaming=streaming)
        mapper = _row_squad_v2
    elif dataset_name in {"natural_questions", "natural_questions_open", "nq", "nq_open"}:
        # Preferir 'nq_open' quando pedido explicitamente (mais leve)
        if dataset_name == "nq_open":
            ds = load_dataset("nq_open", split=split, streaming=streaming)
        else:
            try:
                ds = load_dataset("natural_questions", split=split, streaming=streaming)
            except Exception:
                ds = load_dataset("nq_open", split=split, streaming=streaming)
        mapper = _row_natural_questions
    else:
        raise ValueError(f"Dataset não suportado: {dataset_name}")

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "question", "context", "reference_answer"])
        writer.writeheader()
        count = 0
        total = None
        # tenta estimar total (quando não-streaming e sem limit)
        if tqdm is not None and not streaming and limit is None:
            try:
                total = len(ds)  # nem todo dataset suporta
            except Exception:
                total = None
        iterator = ds
        if tqdm is not None:
            desc = f"Exportando {dataset_name}:{split}"
            iterator = tqdm(iterator, total=(limit or total), unit="ex", desc=desc)
        for ex in iterator:
            row = mapper(ex)
            writer.writerow(row)
            count += 1
            if limit and count >= limit:
                break
        if tqdm is None:
            print(f"Exportados {count} exemplos para {out_csv}")

# =============================
# Runner de Benchmark (QA)
# =============================
class BenchmarkRunner:
    def __init__(self, client: LLMClient, recorder: MetricsRecorder, *, default_params: Optional[LLMParams] = None):
        self.client = client
        self.recorder = recorder
        self.default_params = default_params or LLMParams()

    def iter_qa_csv(self, csv_path: Path) -> Iterable[Dict[str, Any]]:
        with Path(csv_path).open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield row

    def run_over_csv(self, csv_path: Path, *, system: Optional[str] = None, attach_context: bool = True, split: Optional[str] = None, domain: Optional[str] = None, difficulty: Optional[str] = None, params: Optional[LLMParams] = None):
        params = params or self.default_params
        # estima total de linhas do CSV (excluindo cabeçalho)
        total = None
        try:
            with Path(csv_path).open("r", encoding="utf-8") as f:
                total = sum(1 for _ in f) - 1
                if total < 0:
                    total = None
        except Exception:
            total = None

        iterator = self.iter_qa_csv(csv_path)
        if tqdm is not None:
            iterator = tqdm(iterator, total=total, unit="ex", desc=f"Benchmark {self.client.provider}:{self.client.model}")

        for row in iterator:
            example_id = str(row.get("id") or row.get("example_id") or uuid.uuid4())
            question = str(row.get("question", "")).strip()
            context = str(row.get("context", "")).strip() if attach_context else None

            prompt = question
            res = self.client.run(
                example_id=example_id,
                prompt=prompt,
                system=system,
                context=context,
                params=params,
                split=split,
                domain=domain,
                difficulty=difficulty,
            )
            self.recorder.record(res)


# =============================
# Exemplo de uso (CLI simples)
# =============================
HELP = f"""
Uso:
  # Benchmark
  python {Path(__file__).name} provider model qa.csv out_dir

  # Exportar QA (gera CSV com id,question,context,reference_answer)
  python {Path(__file__).name} export_qa <squad_v2|natural_questions> <split> <out_csv> [--limit N] [--streaming]
  # Dica: você pode usar slicing do HF na string do split, ex.: "validation[:2000]"

Exemplos:
  # Rodar benchmark
  python {Path(__file__).name} openai gpt-4.1-mini data/qa_squad_v2_val.csv outputs/
  python {Path(__file__).name} gemini gemini-1.5-flash data/qa_nq_val.csv outputs/
  python {Path(__file__).name} deepseek deepseek-chat data/qa_squad_v2_val.csv outputs/

  # Exportar datasets QA padronizados
  # PowerShell: coloque o split com aspas para suportar os dois-pontos
  python {Path(__file__).name} export_qa squad_v2 "validation[:2000]" data/qa/qa_squad_v2_val.csv --streaming
  python {Path(__file__).name} export_qa natural_questions "validation[:2000]" data/qa/qa_nq_val.csv --streaming

  # Ou usando --limit (faz download mais amplo; prefira slicing+--streaming para reduzir download)
  python {Path(__file__).name} export_qa squad_v2 validation data/qa/qa_squad_v2_val.csv --limit 2000

Saídas (benchmark):
  - outputs/runs.jsonl
  - outputs/runs.csv
  - outputs/runs.sqlite

Observação:
  Configure PRICING_REGISTRY para refletir custos reais (USD/1k tokens).
"""
def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print(HELP)
        return 2

    # Subcomando de exportação de datasets
    if argv[1] == "export_qa":
        if len(argv) < 5:
            print(HELP)
            return 2
        dataset_name = argv[2].strip().lower()
        split = argv[3].strip()
        out_csv = Path(argv[4])
        limit = None
        streaming = False
        # Flags: --limit N | --limit=N | --streaming
        i = 5
        while i < len(argv):
            arg = argv[i]
            if arg.startswith("--limit"):
                if "=" in arg:
                    try:
                        limit = int(arg.split("=", 1)[1])
                    except Exception:
                        pass
                elif i + 1 < len(argv):
                    try:
                        limit = int(argv[i + 1])
                        i += 1
                    except Exception:
                        pass
            elif arg == "--streaming":
                streaming = True
            i += 1
        export_qa_csv(dataset_name, split, out_csv, limit=limit, streaming=streaming)
        print(f"OK -> {out_csv}")
        return 0

    if len(argv) < 5:
        print(HELP)
        return 2

    provider = argv[1].strip().lower()
    model = argv[2].strip()
    qa_csv = Path(argv[3])
    out_dir = Path(argv[4])
    out_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = out_dir / "runs.jsonl"
    csv_path = out_dir / "runs.csv"
    sqlite_path = out_dir / "runs.sqlite"

    recorder = MetricsRecorder(jsonl_path=jsonl_path, csv_path=csv_path, sqlite_path=sqlite_path)

    if provider == "openai":
        client = OpenAIClient(model=model)
    elif provider == "gemini":
        client = GeminiClient(model=model)
    elif provider == "deepseek":
        client = DeepSeekClient(model=model)
    else:
        raise SystemExit(f"Provider não suportado: {provider}")


    runner = BenchmarkRunner(client=client, recorder=recorder, default_params=LLMParams(temperature=0.0, top_p=None, max_tokens=256))

    system_msg = (
        "Você é um modelo de QA conciso. Responda de forma direta e factual."
    )

    runner.run_over_csv(
        csv_path=qa_csv,
        system=system_msg,
        attach_context=True,
        split="test",
        domain="generic-qa",
        difficulty=None,
    )

    print(f"OK -> {jsonl_path}, {csv_path}, {sqlite_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
