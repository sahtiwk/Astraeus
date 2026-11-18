# Compatibility and installation scope

| Environment | Status |
| --- | --- |
| Windows 11 x64, 15.6 GiB RAM, CPU inference, Python 3.11.18 | Clean locked dependencies and real Qwen3 inference exercised |
| Windows 8 GiB / low-power CPU | Not measured; no responsiveness guarantee |
| Linux / macOS | CI matrix configured, not executed here; manual llama.cpp setup required |
| Python 3.12 / 3.13 | Lock allows these versions; not tested here |
| Python 3.14 | Unsupported by this release's dependency range |
| Docker / fully air-gapped installation | Not certified |

The GGUF is about 1.28 GB. Runtime, embeddings and Python dependencies require
additional disk/RAM. Launch refuses model startup below 3 GiB available RAM;
this is a conservative startup check, not a universal performance guarantee.
No GPU is required for the measured configuration.

The source ZIP is not a standalone executable: install dependencies while online,
explicitly download/import models and runtime, then operate locally. For an
air-gapped device prepare matching wheels, Python, runtime and models elsewhere.
Never copy a Windows virtual environment to a different platform.
