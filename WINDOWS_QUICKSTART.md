# Astraeus for Windows - release candidate

1. Extract the entire ZIP into a writable folder, for example Documents/Astraeus.
2. Double-click Install Astraeus.cmd. Choose core analysis, search, or diagnosis.
   Setup downloads a private Python 3.11 runtime and packages. Search downloads
   MiniLM. Diagnosis also downloads a 1.28 GB Qwen3 GGUF and llama.cpp runtime.
3. Double-click Start Astraeus.cmd. Your browser opens the local app.
4. Import a log or folder, inspect incidents and save/export results. Keep the
   launcher window open. Press Ctrl+C there to stop the UI and model server.

The default launcher enables diagnosis when its verified model/runtime are
installed and at least 3 GiB RAM is available. Otherwise it starts core analysis.
Use run.ps1 -CoreOnly to explicitly start core analysis.

## Install location and data

Administrator privileges and a system Python installation are unnecessary.
Use a folder you can write to. Keep the extracted folder in its installed
location because the private Python environment references that location.
If you move it, rerun setup online to rebuild the environment before launching.
Existing projects are in data/projects. Back up that directory before replacing
the application. Model files are in models and the inference runtime in runtime.
Do not install a new release over an open application.

The command wrappers use an execution-policy override for their own PowerShell
process. Organization-managed policy or SmartScreen may require an administrator's
review. The scripts and release candidate are unsigned.

## Offline operation

Initial setup needs internet. Subsequent parsing, detection, prepared embedding
search and installed-model diagnosis run on this machine with loopback services.
No external inference API key is required. Core analysis works without weights.
install.ps1 -Offline repairs dependencies from a previously populated cache when
the matching Python runtime is still installed. An extracted source ZIP alone
does not provide an air-gapped installation.

## Troubleshooting

- Setup interrupted: rerun Install Astraeus.cmd. The diagnosis download resumes.
- Port already used: stop the previous launcher before starting another copy.
- Missing model: rerun setup and select Search or Diagnosis.
- Browser did not open: visit http://127.0.0.1:8501.
- Low memory: close other applications or run run.ps1 -CoreOnly.
- Model startup failed: inspect data/model-server.log.
- Clear a project's saved history using the app's project storage controls.

The tested target is Windows x64 on the available approximately 16 GiB machine.
Lower-memory devices have not been certified. Diagnoses are hypotheses that
require checking against the displayed evidence.
