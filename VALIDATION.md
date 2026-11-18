# Validation - 2026-11-17

## Application and installation

- 41 regression/UI tests passed in staging, a clean extracted source release,
  and the final C:/astraeus installation (Python 3.11.18).
- The full uv lock installed 115 compatible packages; dependency check passed.
  The pre-existing global Python environment was left unchanged.
- Real subprocess diagnosis completed, survived a manager restart, and persisted
  its report. Cancellation prevented a saved result. A transport-redaction bug
  found by this integration check was fixed and regression-tested.
- A real integration probe blocked non-loopback Python socket connections while
  local embeddings, Chroma search, llama.cpp diagnosis and report reload passed.
  This does not cover every native dependency or certify OS-level isolation.
- The target launcher started both the verified model and Streamlit on temporary
  loopback ports; both health checks and a real diagnostic request passed. Tests exercise UI interactions; no hosted service was deployed.
- The allowlisted source ZIP has per-file SHA-256 and an archive digest. Repeated
  builds with identical inputs are byte-identical. A clean extracted install used
  cached dependencies with uv offline mode and passed its tests.
- Existing secrets/data were preserved. Changed-source backups are under the
  agent workspace's astraeus-before-completion directory.

## Real local model evaluation

Hardware: Windows 11 x64, 15.6 GiB total RAM, 16 logical CPUs. Runtime: llama.cpp
b12443, Qwen3-1.7B Q4_K_M, context 4096, four CPU threads, one inference slot,
reasoning off. Exact weights and runtime hashes are in models-manifest.json.

Controlled dataset: 108 cases, nine families, 54/27/27 train/validation/test runs.
No production or unseen-family accuracy claim. Healthy examples are only three
per evaluation split. Retrieval templates overlap, so perfect retrieval is easy.

Validation v1: 17/24 base and 1/24 retrieval-assisted reports passed validation.
The model paraphrased evidence. Prompt/schema v2 enumerates permitted evidence
lines: 24/24 base and 24/24 retrieval-assisted reports passed. Validation term
match proxies were 66.7%/75.0%; these are NOT diagnostic correctness scores.
Warm valid-response p50/p95: 7.19/13.01 seconds. Peak summed process RSS: ~3.99 GiB.
Two integration probes overlapped portions of validation; use the reserved test
run for uncontended final latency. RSS may double-count shared pages and excludes
any unrelated UI process.

All three unresolved validation examples failed the simple abstention proxy in
both modes. Inspection found unsupported causes/components. See MODEL_CARD.md.
No blinded human causal/support review has been completed. A schema-valid model
report remains a hypothesis and cannot drive automatic remediation.

## Reserved test split (frozen v2 prompt)

27 cases: 24 fault/ambiguous cases, three healthy examples. Base and retrieval
modes each produced 24/24 schema-valid reports with supplied evidence quotes.
Detection and retrieval proxies were 100% on this narrow same-template split;
this is not generalization evidence. Cause term-match proxy: base 17/24 (70.8%),
retrieval 16/24 (66.7%). Retrieval did not demonstrate a diagnosis benefit.
Warm generation p50 7.44 s, p95 9.68 s; peak summed process RSS ~4.34 GiB.
Raw outputs: evaluation/results-test-v2.json. No final-test-driven prompt changes.

## Remaining verification

8 GiB devices, Linux/macOS, Docker, full offline installation media, OS-level
network isolation and GitHub-hosted CI have not been exercised. CI configuration
exists; no public commit/tag/release was created. Fine-tuning was not performed:
the available dataset does not justify it. See IMPLEMENTATION_PLAN.md.

## Windows release candidate 0.3.0rc1 - 2026-11-18

Fresh-folder setup downloaded its checksum-verified official uv archive, a private
CPython 3.11.18 runtime, and 112 locked runtime dependencies. pip check passed.
A cached offline repeat installation passed. All 43 regression/UI tests passed.
The native launcher started successfully using the fresh installation. Real
MiniLM/Chroma indexing and retrieval passed with Python sockets blocked.
Model/runtime import verified the pinned artifacts. The combined UI/model
launcher, real RCA generation and saved-report reload passed in the fresh
environment while external Python socket connections were blocked. Initial setup requires network access. No OS-level offline certification,
8 GiB device certification, or signed executable installer is claimed.
