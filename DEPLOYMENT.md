# Deploy the public demo

The public entry point is demo.py. Visitors can analyze three bundled samples,
inspect their incidents and export incident JSON. The image only packages demo
dependencies and source. It requires no model, database, secret or volume.

On Render, create a Blueprint from the repository branch that contains render.yaml.
The Blueprint selects Dockerfile.demo, a free web service and a health check.
After deployment, open the HTTPS URL Render assigns and analyze each sample.

To verify on any Docker host:

    docker build -f Dockerfile.demo -t astraeus-demo .
    docker run --rm -p 127.0.0.1:10000:10000 astraeus-demo

Open http://127.0.0.1:10000. The Linux CI workflow builds the same image, probes
the health endpoint and exercises all three samples. For another container host,
use Dockerfile.demo, set PORT as needed, and route HTTPS to that port.

The full local application lives in the original Astraeus checkout.

Verified on 2026-11-17: Linux amd64 image built, health endpoint returned OK on an overridden PORT, and all three sample analysis flows passed inside the non-root container.

GitHub deployment source is https://github.com/sahtiwk/Astraeus on branch
codex/public-demo. Select that branch when creating the Render Blueprint.
Commit 911d9fb passed GitHub's Linux container build, health check and all three
sample workflows on 2026-11-18:
https://github.com/sahtiwk/Astraeus/actions/runs/44233464338

If setting up a Web Service directly, select the same branch, Docker runtime,
Dockerfile.demo as the Dockerfile path, the Free instance, and
/_stcore/health as the health check. The service reads Render's PORT variable.
Verify the assigned HTTPS URL and each sample after deployment.

Live deployment verified 2026-11-18 at https://astraeus-demo.onrender.com.
Render service srv-dbui9s08v5cc7396o9a0 uses the Free plan in Oregon,
branch codex/public-demo, Dockerfile.demo and /_stcore/health.
The public application-error sample produced an incident, source evidence and
an export control during browser verification. Free instances sleep when idle.
