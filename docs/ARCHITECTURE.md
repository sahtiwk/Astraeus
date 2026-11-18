# Architecture and tradeoffs

Local import -> bounded parser -> redaction -> severity/time/service grouping
-> incident preview -> optional MiniLM/Chroma history -> SQLite job -> worker
process -> loopback llama.cpp -> schema/evidence validation -> SQLite report/export.

The core remains usable without model weights. Inference never falls back to an
external API. Setup downloads are explicit. Workers survive UI reruns and write
completed results themselves. SQLite transactions protect job claims and prevent
late writes after cancellation. Dead workers require explicit retry. Progress uses
state polling; this is not continuous monitoring.

Project directories separate local work, not mutually untrusted users. The same OS
user can read all projects. Regex redaction is incomplete PII protection. Hostile
log instructions cannot execute application commands but can influence generated
text. Evidence enumeration constrains quotes, not reasoning. Never execute model
suggestions automatically. One model-server slot bounds inference concurrency.

Kafka, hosted storage, authentication and a frontend rewrite are unnecessary for
this single-user offline release. Add them only for measured hosted requirements.

Demo: import a bundled sample, inspect evidence, save local history, import a
different sample, search history, generate a hypothesis, refresh and export.
Cancel another diagnosis and restart the UI to demonstrate durable results.
