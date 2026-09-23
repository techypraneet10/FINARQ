# Phase 9: LLM Answer Generation & Orchestration Architecture

## 1. Executive Summary

Phase 9 implements the **LLM Answer Generation & Orchestration Engine**, the synthesis and presentation layer downstream of Phase 3 Deterministic Reasoning.

In accordance with ADRs 0022–0026:
> **THE LLM IS NOT THE SOURCE OF TRUTH.**  
> Source documents and Phase 3 verified facts, calculations, claims, and citations are the authoritative ground truth. The LLM functions purely as an instruction-following natural language synthesis engine.

---

## 2. End-to-End Orchestration Architecture

```
User Inquiry (AnswerRequest)
       │
       ▼
1. Phase 3 ReasoningService (Multi-Period Facts, Decimal Calculations, Conflicts, Claims, Citations)
       │
       ▼
2. Deterministic Answerability Gate (Intercepts INSUFFICIENT_EVIDENCE / CONFLICTING_EVIDENCE / CALCULATION_FAILED)
       │
       ├──[Intercepted] ──────────────────────────────────────────┐
       │                                                         │
       ▼[Proceed to LLM]                                          │
3. Budgeted ContextBuilder (<QUESTION>, <FACTS>, <CALCS>, <CLAIMS>, <CITATION_MAP>, <SOURCE_EVIDENCE>)
       │
       ▼
4. Versioned PromptBuilder (Multi-Style, System Injection Defense, Untrusted Data Boundary)
       │
       ▼
5. Cryptographic Answer Cache Check (tenant_id|query|facts_hash|calcs_hash|prompt_ver|model)
       │
       ├──[Cache Hit] ───────────────────────────────────────────┤
       │                                                         │
       ▼[Cache Miss]                                             │
6. Gated LLM Generation & Bounded Validation Loop (Attempts <= 1 Retry)
       │
       ├── Structured Output (LLMAnswerOutput Schema)
       │
       ├── 8-Stage Deterministic AnswerValidator:
       │   ├─ Stage 1: Schema & Completeness (Non-empty summary & body)
       │   ├─ Stage 2: Citation Marker Audit (Regex verification against verified citation set, rejects [C99])
       │   ├─ Stage 3: Claim Reference Audit (Verifies referenced claim IDs)
       │   ├─ Stage 4: Numerical Fidelity Audit (Matches numbers/deltas to verified facts within 0.5% tolerance)
       │   ├─ Stage 5: Grounding Consistency (Discloses partial grounding limitations)
       │   ├─ Stage 6: Answerability Consistency (Discloses missing metrics/periods)
       │   ├─ Stage 7: Unsupported Content Detection (Flags speculative phrases like 'I predict')
       │   └─ Stage 8: Style & Length Compliance
       │
       ├──[Validation Failure & Attempts <= 1] ──> Correction Prompt Re-query
       │
       ├──[Second Failure / Provider Outage] ────> Safe Deterministic Fallback Synthesis
       │
       ▼
7. Response Renderer (Renders Markdown with citations and arithmetic formulas; saves to cache)
       │
       ▼
Authoritative AnswerResponse / Server-Sent Events (SSE) Stream
```

---

## 3. Core Components

### 3.1 Provider-Agnostic LLM Layer (`src/financial_rag/infrastructure/llm/`)
- `LLMProviderProtocol`: Abstract protocol for `generate`, `structured_generate`, `generate_stream`, and `health_check`.
- `FakeLLMProvider`: Deterministic simulator for testing with configurable modes (`valid`, `hallucinate_number`, `hallucinate_citation`, `unsupported_claim`, `malformed_json`, `timeout`, `error`, `streaming`).
- `OpenAILLMProvider`: Async OpenAI client integration with JSON schema structured output and streaming.
- `create_llm_provider`: Factory selector driven by `LLMSettings`.

### 3.2 8-Stage Deterministic Post-Generation Validator (`validator.py`)
- **Stage 1 (Schema)**: Ensures summary and detailed answer bodies are non-empty.
- **Stage 2 (Citation Audit)**: Validates that all `[C\d+]` markers exist in the verified citation set; flags unknown markers like `[C99]`.
- **Stage 3 (Claim Audit)**: Asserts all referenced claim IDs exist in the `AnswerPackage`.
- **Stage 4 (Numerical Fidelity)**: Extracts all numbers, scaled values ($B, $M), and percentage changes ($+2.02\%$) and matches them against facts and calculations.
- **Stage 5 (Grounding Consistency)**: Asserts that partially grounded packages disclose limitations.
- **Stage 6 (Answerability Consistency)**: Verifies that partially answerable inquiries disclose what is missing.
- **Stage 7 (Speculation Defense)**: Flags forbidden speculative phrasing ("I predict", "guaranteed to").
- **Stage 8 (Style Bounds)**: Enforces character limits for concise presentation styles.

### 3.3 Safe Deterministic Fallback (`renderer.py`)
If the LLM provider experiences an outage or fails validation after retry, the system constructs a 100% grounded response directly from `AnswerPackage.claims`, `calculations`, and `citations`.
- Metadata flags `used_fallback=True`.
- Diagnostic explanation is attached to `warnings`.

---

## 4. API Endpoints

### 4.1 Unary Answer Generation (`POST /api/v1/answers`)
- Scoped to caller tenant via JWT bearer token.
- Returns complete `AnswerQueryResponse` with structured facts, claims, calculations, citations, and execution latency.

### 4.2 Progressive SSE Streaming (`POST /api/v1/answers/stream`)
- Emits Server-Sent Events with typed envelopes:
  1. `stage_start` (stage="reasoning")
  2. `reasoning_complete` (facts, calculations, citations counts)
  3. `calculations` (formula breakdowns)
  4. `citations` (source excerpts & page numbers)
  5. `stage_start` (stage="generation")
  6. `token_delta` (incremental token text chunks)
  7. `answer_complete` (final answer metadata)

---

## 5. Structured Prompts & Prompt Injection Defense (`prompts/v1.py`)
- **System Instruction Boundary**: Rigid hierarchy `SYSTEM RULES > APPLICATION TASK > RETRIEVED EVIDENCE`.
- **Untrusted Document Boundary**: All retrieved text inside `<SOURCE_EVIDENCE>` tags is processed strictly as data, never instructions.
- **Style Instructions**: Tailored templates for `STANDARD`, `CONCISE`, `DETAILED`, and `ANALYTICAL` response modes.
- **Correction Templates**: Formatted critique appended on validation failures during bounded retry ($\le 1$).

---

## 6. Golden QA Benchmark Dataset (`tests/fixtures/golden_financial_qa.json`)
Covers all 11 canonical financial query types:
1. **Factual Lookup**: Single-period metric query with exact scale and currency.
2. **Arithmetic Calculation**: Multi-operand subtraction/addition.
3. **Percentage Change**: YoY growth rate calculation ($+2.02\%$).
4. **Margin Calculation**: Gross/Operating margin ratio calculation ($46.21\%$).
5. **YoY Comparison**: Multi-year net income comparison with delta.
6. **Multi-Period Comparison**: 3-year revenue trend analysis.
7. **Table-Based Answer**: Provision for income taxes extracted from consolidated statements.
8. **Narrative Answer**: Liquidity risk factors from MD&A.
9. **Cross-Document Reasoning**: FY2023 10-K compared with FY2024 10-K.
10. **Insufficient Evidence**: Interception and safe disclosure for unmentioned metrics (e.g. FY2030).
11. **Conflicting Evidence**: Conflicting filing numbers surfaced with discrepancy breakdown.

