from pathlib import Path

import streamlit as st

from src.pipeline import ingest

SAMPLES = {
    "Application error": "app_error.log",
    "Database timeout": "db_timeout.log",
    "HTTP 500 errors": "nginx_500.log",
}


def main():
    st.set_page_config(page_title="Astraeus | Log investigation")
    st.title("Astraeus")
    st.caption("Investigate incidents in bundled sample logs.")
    sample = st.selectbox("Log sample", list(SAMPLES))
    if st.button("Analyze sample", type="primary"):
        path = Path(__file__).parent / "data" / "samples" / SAMPLES[sample]
        st.session_state["sample_analysis"] = (sample, ingest(path.read_bytes()))

    analysis = st.session_state.get("sample_analysis")
    if analysis is None or analysis[0] != sample:
        return

    result = analysis[1]
    incidents = result["anomalies"]
    st.write(f"{result['counts']['events']} events · {len(incidents)} incidents")
    if result["warnings"]:
        st.warning("\n".join(result["warnings"]))
    with st.expander("Parsed log preview"):
        st.dataframe(result["preview"])
    if not incidents:
        st.info("No incidents matched the detection rules.")
        return

    st.dataframe([
        {"Start": incident.start_ts, "End": incident.end_ts, "Severity": incident.severity}
        for incident in incidents
    ])
    selected = st.selectbox("Incident", range(len(incidents)), format_func=lambda i: str(i + 1))
    incident = incidents[selected]
    st.code(incident.chunk_text, language="text")
    st.download_button(
        "Export incident JSON", incident.model_dump_json(indent=2),
        file_name="astraeus-incident.json", mime="application/json",
    )


if __name__ == "__main__":
    main()
