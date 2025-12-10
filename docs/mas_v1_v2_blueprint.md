# MAS blueprint: AI-Scientist v1 → v2 for Ollama-backed LLM evals

This blueprint tailors the AI-Scientist pipeline to your MAS stack with **VM workers**, **Ollama-only inference**, and **internal/non-public evaluation sets** where **raw model outputs must never be stored**. It captures the v1 (linear) and v2 (agentic tree-search) modes, governance controls, and operator-facing knobs—including a configurable worker count (default: 3 VMs, one per local GPU).

## 1) Topology (Proxmox)

**Control plane (trusted):**
- `ui-gateway` (LXC): OpenWebUI + Flowise (approvals, operator console).
- `orchestrator` (VM/LXC): pipeline + tree-search manager + policy checks.
- `queue` (VM/LXC): RabbitMQ.
- `registry` (VM/LXC): Postgres + MinIO + MLflow (metadata, artifacts, metrics).
- `vector` (VM/LXC): Qdrant (paper corpus embeddings, run similarity).
- `mirror` (VM/LXC): apt-cacher-ng + PyPI proxy/group (Nexus or devpi).
- `papers` (VM/LXC): PDF ingestion + GROBID-style extractor for structured citations.

**Model plane:**
- `ollama` (LXC/VM, GPU): provides all inference endpoints to workers.

**Sandbox plane (untrusted):**
- `worker-01..N` (VMs): executes jobs only; firewalled; **default N = 3**, exposed as a GUI setting in OpenWebUI/Flowise so operators can increase/decrease workers per available GPU.

## 2) Network policy

- Workers: egress **default deny**. Allow only `queue`, `registry` (MinIO/MLflow/Postgres), `mirror`, and `ollama`. Optional read-only access to `papers/vector` for retrieval. No public internet.
- Control/model planes: isolated from sandbox via VLANs/security groups; MGMT network reserved for Proxmox only.

## 3) Data governance for internal eval sets

- Package each eval set as an immutable bundle: `evalsets/<name>/<version>/dataset.parquet` + `manifest.yaml`.
- Manifest fields (minimum):
  - `data_classification` (e.g., confidential)
  - `pii` status
  - `purpose`: **evaluation only** (no training)
  - `allowed_outputs`: `store_raw_model_outputs: false`, `store_redacted_outputs: true`
  - `retention_days`
  - `allowed_roles` (e.g., `eval_worker`), `requires_approval`
- Worker-side redaction: strip or hash example IDs and responses before upload; only scores and redacted snippets are stored. Orchestrator sees only aggregate metrics/metadata by default.

## 4) Evaluation runner (Ollama-only)

- Standardized job input: `run_spec.yaml` + optional git patch.
- Execution engine: `lm-evaluation-harness` (or equivalent) with an **Ollama adapter**. Example endpoint URI: `ollama://<model>@http://ollama.internal:11434`.
- Job outputs (uploaded to MinIO/MLflow):
  - `metrics.json`
  - `per_sample.jsonl` **(redacted or absent for internal sets per manifest)**
  - `plots/*.png`
  - `env.lock` (exact deps, SHAs)
  - `stdout.log`, `stderr.log`

### Sample `run_spec.yaml` schema (excerpt)

```yaml
run_id: 2025-12-10-llm-eval-001
mode: v2  # v1 = linear; v2 = tree-search
model:
  provider: ollama
  name: llama2-70b
  endpoint: http://ollama.internal:11434
benchmarks:
  - id: arc_challenge
    source: public
  - id: internal_support_tickets
    source: internal
    dataset_version: 2025-12-01
    store_raw_outputs: false  # enforced by worker
search:
  expanders: [prompt_tweak, temperature, rag_toggle, chunk_size]
  scorer:
    weights: {quality: 1.0, robustness: 0.6, cost: -0.3, latency: -0.1, variance: -0.2}
resources:
  max_parallel_workers: 3  # surfaced in GUI; defaults to one VM per GPU
  time_budget_minutes: 240
policy:
  require_human_approval_for_patches: true
  allow_internal_data_access: true
```

## 5) v1 → v2 behavior

- **v1 (linear):** baseline run → propose single change (prompt/decoding/RAG) → run → compare → report.
- **v2 (tree-search):** nodes represent `{model, prompt, decoding, retrieval config, benchmark mix, seeds}`. Edges are safe mutations (prompt tweak, temperature/top_p change, chunk size, RAG toggle, ablation). Scoring combines quality, robustness, cost, latency, and variance with regression penalties on must-not-fail internal sets.

## 6) Operator experience (OpenWebUI/Flowise)

- **New Eval Tree**: select models, benchmark mix (public + internal), budget, **worker count** (default 3; slider/selector to match GPU availability).
- **Approve Patch**: diff viewer + policy scan results.
- **Run Replication**: fixed seeds, N repeats.
- **Generate Report**: plots + markdown + audit footer (run IDs, dataset versions, “AI-assisted” disclosure).

## 7) Worker VM hardening checklist

- Immutable base image (cloud-init template); ephemeral job workspace wiped per run.
- No secrets on disk; role account with minimal privileges.
- CPU/RAM/disk quotas + wall-clock timeouts per job.
- Dependency allowlist; no public internet; logging shipped centrally with signed manifests.

## 8) Rollout milestones

1) **M0:** Standardize `run_spec.yaml` + worker image + mirrors wired.
2) **M1:** v1 linear loop live with HITL approvals for patches and internal set access.
3) **M2:** v2 tree-search enabled (expansion operators + scoring + budget controls).
4) **M3:** Quality layer—replication runs, regression gates on internal sets, figure/report critic.
