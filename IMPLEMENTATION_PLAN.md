# Astraeus implementation plan

Updated 2026-11-17. Offline-first, single-user Windows release. The original
hosted enterprise roadmap is superseded for this release; no mandatory API.

## Implemented and exercised

- [x] Parser/detector repair, bounded ingestion, redaction and source-aware retrieval.
- [x] Optional loopback llama.cpp inference, evidence-constrained JSON and report cache.
- [x] Persistent subprocess jobs, explicit retries, cancellation and restart handling.
- [x] File/folder import, incident filters/timeline, project history, JSON/Markdown export.
- [x] Pinned/checksummed Qwen3 model download/import, Windows CPU runtime and RAM checks.
- [x] Python 3.11 clean environment, full uv lock, install/run scripts and safe source ZIP.
- [x] 108 controlled cases with run-level train/validation/test splits and provenance.
- [x] Rules, lexical/semantic retrieval and base/retrieval-assisted local model evaluator.
- [x] Dataset/model/compatibility cards, architecture rationale and raw result retention.
- [x] Applied source and verified weights/runtime to C:/astraeus, preserving prior data.
- [x] Regression tests and real worker/offline integration checks. See VALIDATION.md.

## Conditional decision

Fine-tuning is deferred on evidence: 54 template-repetitive training cases and no
reviewed target reports cannot justify adapter training. The baseline has reasoning
weaknesses; collect broader reviewed data and compare stronger local candidates
before a compute-backed LoRA pilot. No new trained model is claimed.

## Gates not claimed complete

- [ ] Independent/blinded diagnostic correctness and semantic evidence scoring;
      unseen-application/failure-family generalization, larger-model comparison.
- [ ] Actual 8 GiB, Linux/macOS and full disconnected OS-level testing; only the
      available Windows ~16 GiB machine has been exercised.
- [ ] Executed hosted CI, public tagged release, demo recording and Docker runtime.
      CI configuration and local release artifact exist; nothing was published.

These are validation/research/publication gates, not completed features. A working
local student release does not establish production readiness or universal support.

## Windows publishing continuation - 2026-11-18

Release candidate packaging adds double-click setup/launch, verified standalone
bootstrap without a system Python prerequisite, optional Core/Search/Diagnosis
setup profiles, local model discovery and actionable startup errors.
The source ZIP installs privately in its extracted location. Model/runtime
downloads remain explicit setup operations. Windows CI produces a release ZIP
and checksum. See WINDOWS_QUICKSTART.md for distribution and offline scope.
