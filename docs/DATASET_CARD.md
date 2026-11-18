# Controlled incident dataset

108 generated cases in nine families, dated 2026-11-17. Regenerate with
`python -m evaluation.generate_cases`. Each case records provenance and the
mechanism used to establish its label. SQLite contention, uniqueness violations,
missing files/configuration, malformed JSON, connection refusal and bounded pool
exhaustion execute controlled failures. Healthy cases and unresolved timeouts
provide negative/abstention examples. No customer logs or LLM-generated labels.

Per family: six training runs, three validation runs, three test runs (54/27/27).
Runs are separate but templates and failure families overlap. This dataset tests
regressions and controlled behavior; it cannot establish production accuracy or
unseen-system generalization. Template overlap explains the easy retrieval scores.
Do not advertise its detection precision as production performance.

Term matching is an automated proxy. An expert must separately assess causal
correctness, whether evidence supports the proposed cause, unsafe suggestions and
appropriate abstention. Keep validation for development; freeze code before test.
For further tuning collect independently reviewed examples from new applications,
with permissions/licenses, and split by application/failure family before training.
