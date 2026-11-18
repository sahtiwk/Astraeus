# Local diagnosis model and tuning decision

Qwen3-1.7B, GGUF Q4_K_M from ggml-org, runs through llama.cpp b12443 on CPU.
Exact revision, checksum, size and upstream license reference are recorded in
models-manifest.json. The weights are an upstream pretrained model, not trained
by Astraeus. Model weights are not bundled in the source ZIP.

The application asks for structured diagnostic hypotheses and exact source lines.
Schema validation and evidence enumeration reject malformed or invented quotes;
they do not prove a cause or recommended check is supported. Confidence is not
calibrated. Logs, including retrieved history, are untrusted model inputs.

## Evaluation protocol

Run `python -m evaluation.evaluate --split validation --semantic --endpoint
http://127.0.0.1:18080/v1 --model astraeus-qwen3-1.7b --output
 evaluation/results-validation-v2.json` (join the command onto one line).
Freeze the prompt and application code, then repeat with `--split test` and a
separate output file. Supply `--server-pid PID` for combined process memory.
Raw reports and rejected attempts remain in the JSON. See VALIDATION.md for results.
Latency is warm sequential generation, excluding model startup and embedding setup.
Early v1/v2 validation metrics count valid-response latency only; test metrics count
all attempted generations. Do not directly compare these latency populations.

For independent review, hide model/mode and score each report: causal correctness
(0 incorrect, 1 plausible but incomplete, 2 matches established cause), evidence
support (0 unsupported, 1 partial, 2 sufficient), abstention on unresolved cases,
and unsafe/irrelevant recommendations. Quote membership is a separate mechanical
check. No independent human review has been performed in this release.

## Fine-tuning gate

Decision: do not train an adapter yet. There are only 54 training examples, with
repeated templates and no independently reviewed target reports. Training on them
would encourage template memorization and cannot establish better diagnoses.
No training-from-scratch or custom trained-weight claim is warranted.

Collect permissioned incidents across different applications and reviewed targets;
hold out applications/families. Profile an explicitly available development GPU.
Only then run a bounded Transformers/PEFT LoRA pilot against the original base,
using validation for selection, never test. Require improved blinded correctness
without worse evidence fabrication, abstention or memory/latency. Merge/export/
quantize and evaluate the exact final GGUF. Record dataset and adapter lineage.
Until those gates are met, ship optional base inference and reliable core tools.

## Observed reasoning failure

Validation's three ambiguous timeout cases did not trigger the simple abstention
proxy in either mode. Inspection found causes such as "timeout due to lack of
upstream metrics or configuration" and an invented API Gateway component.
Missing diagnostic context does not establish that cause. Retrieval also sometimes
mixes services from prior incidents. Treat these as material model limitations,
not merely formatting errors. A larger model comparison and independent review
are needed before promising reliable diagnosis. No automatic alert/remediation
workflow should depend on this model's conclusions.
