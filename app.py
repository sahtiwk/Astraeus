"""Astraeus: offline-first log investigation."""
import os
from pathlib import Path

import streamlit as st
from src.pipeline import ingest, ingest_folder
from src.vector_store import VectorStore
from src.llm_analysis import validate_endpoint
from src.jobs import JobManager
from src.model_manager import hardware
from src.projects import project_directory, clear_history
from src.reports import ReportStore, report_key

DATA_DIR = Path(os.getenv('ASTRAEUS_DATA_DIR', str(Path(__file__).parent / 'data')))


@st.cache_resource
def stores(path):
    return VectorStore(str(Path(path)/'chromadb')), ReportStore(Path(path)/'reports.sqlite3')


@st.cache_resource
def job_manager(path):
    return JobManager(Path(path)/'reports.sqlite3')


def display_report(report):
    st.success('Diagnostic hypothesis — verify against the evidence')
    st.write(report.summary)
    st.write('Probable cause:', report.probable_root_cause)
    st.write('Severity:', report.severity, '| Component:', report.affected_component)
    st.caption('Model confidence is not a calibrated probability and is not displayed.')
    for line in report.evidence_lines:
        st.code(line, language='text')
    for action in report.recommended_actions:
        st.write('- ' + action)
    markdown = '\n\n'.join(['# Astraeus diagnostic hypothesis', report.summary, '**Probable cause:** '+report.probable_root_cause, '**Evidence:**', *['> '+line.replace('\n','\n> ') for line in report.evidence_lines], '**Next checks:**', *['- '+action for action in report.recommended_actions]])
    st.download_button('Export report (Markdown)', markdown, file_name='astraeus-report.md', mime='text/markdown')
    st.download_button('Export report (JSON)', report.model_dump_json(indent=2),
                       file_name='astraeus-report.json', mime='application/json')


def main():
    st.set_page_config(page_title='Astraeus', page_icon='🔍', layout='wide')
    st.title('Astraeus — offline log investigation')
    st.caption('No cloud inference or API key required. Parsing and detection work without a model.')
    project=st.sidebar.text_input('Local project', 'default')
    try:project_path=project_directory(DATA_DIR,project)
    except ValueError as exc:
        st.error(str(exc));return
    if st.session_state.get('project_path') != str(project_path):
        st.session_state.pop('analysis',None)
        st.session_state.pop('results',None)
        st.session_state['project_path']=str(project_path)
    st.sidebar.header('Optional local RCA')
    endpoint=st.sidebar.text_input('Local model endpoint', os.getenv('ASTRAEUS_LOCAL_ENDPOINT','http://127.0.0.1:8080/v1'))
    model=st.sidebar.text_input('Model identifier / version', 'astraeus-qwen3-1.7b')
    resources=hardware()
    st.sidebar.caption(f"Available RAM: {resources['available_gib']:.1f} GB / {resources['ram_gib']:.1f} GB. CPU inference supported.")
    if resources['available_gib'] < 3:
        st.sidebar.warning('Memory is tight for the lightweight model. Close other applications or use core-only mode.')
    st.sidebar.caption('Start a llama.cpp server separately. Use a versioned model identifier to avoid stale cached reports after changing weights.')
    st.sidebar.caption('Log previews, vector documents and reports use best-effort redaction. Review exports before sharing.')
    try:
        vectors,reports=stores(str(project_path))
        jobs=job_manager(str(project_path))
        jobs.poll()
    except Exception:
        vectors=reports=jobs=None
        st.warning('Local storage unavailable. Parsing and detection remain available; check the data-directory permissions.')
    if vectors and jobs:
        with st.sidebar.expander('Project storage'):
            confirmed=st.checkbox('Clear saved incidents, jobs and reports for this project')
            if st.button('Clear project history',disabled=not confirmed):
                try:
                    clear_history(vectors,jobs)
                    st.session_state.pop('analysis',None)
                    st.session_state.pop('results',None)
                    st.success('Project history cleared from the application.')
                except ValueError as exc:st.error(str(exc))
    uploaded=st.file_uploader('Import logs',type=['log','txt','jsonl'])
    if uploaded is not None and st.button('Analyze file', type='primary'):
        try:
            with st.spinner('Parsing and grouping incidents...'):
                state=ingest(uploaded.getvalue())
                state['indexed']=False
                state['history']={}
                st.session_state['analysis']=state
        except (ValueError, UnicodeError) as exc:
            st.error(str(exc))
            st.session_state.pop('analysis',None)
    with st.expander('Import a local folder'):
        folder=st.text_input('Folder path (up to 50 files / 50 MB total)')
        if st.button('Analyze folder'):
            try:
                state=ingest_folder(folder)
                state.update(indexed=False,history={})
                st.session_state['analysis']=state
            except (ValueError,OSError,UnicodeError) as exc:
                st.error(str(exc))
                st.session_state.pop('analysis',None)
    state=st.session_state.get('analysis')
    if state is None:
        st.info('Import a log file, then select Analyze file. Local model setup is optional.')
        return
    st.write(f"{state['counts']['events']} events; {len(state['anomalies'])} incidents")
    if state['counts']['warnings']:
        st.warning(f"{state['counts']['warnings']} records have parsing warnings. Review before trusting detection results.")
        st.write('\n'.join(state['warnings']))
    with st.expander('Parsed preview (first 50 events)'):
        st.dataframe(state['preview'],width='stretch')
    if not state['anomalies']:
        st.info('No incidents matched the current rules. This does not prove the logs are healthy.')
        return
    if vectors and not state['indexed'] and st.button('Save incidents to local history'):
        with st.spinner('Indexing locally...'):
            result=vectors.index_anomaly_chunks(state['anomalies'])
        if result.failed:
            st.warning(f'{len(result.failed)} incidents could not be indexed. Ensure the embedding model is installed locally, then retry. Successful writes are preserved.')
        else:
            state['indexed']=True
            st.success(f'{result.indexed} new incidents saved; existing incidents were preserved.')
    levels=st.multiselect('Severity filter',['HIGH','MEDIUM','LOW'],default=['HIGH','MEDIUM','LOW'])
    query=st.text_input('Filter incidents by text or service').lower()
    choices=[i for i,c in enumerate(state['anomalies']) if c.severity in levels and query in c.chunk_text.lower()]
    if not choices:
        st.info('No incidents match these filters.');return
    with st.expander('Incident timeline (first 200 matches)'):
        st.dataframe([dict(start=state['anomalies'][i].start_ts,end=state['anomalies'][i].end_ts,severity=state['anomalies'][i].severity) for i in sorted(choices,key=lambda i:state['anomalies'][i].start_ts)[:200]],width='stretch')
    selected=st.selectbox('Incident',choices,
        format_func=lambda i:f"{i+1} | {state['anomalies'][i].severity} | {state['anomalies'][i].start_ts}")
    chunk=state['anomalies'][selected]
    st.code(chunk.chunk_text,language='text')
    st.caption('Source record IDs: '+', '.join(chunk.record_ids))
    if vectors and st.button('Find historical incidents'):
        try:
            state['history'][chunk.chunk_id]=vectors.query_similar_anomalies(
                chunk.chunk_text,limit=3,exclude_ids=[c.chunk_id for c in state['anomalies']],
                exclude_source_id=state['source_id'],exclude_source_ids=state.get('source_ids'))
        except Exception:
            st.error('Local search unavailable. Verify the cached embedding model; no network download was attempted.')
            state['history'][chunk.chunk_id]=[]
    history=state['history'].get(chunk.chunk_id,[])
    for related in history:
        with st.expander('Related incident '+related.start_ts):
            st.code(related.chunk_text,language='text')
    if chunk.chunk_id in state['history'] and not history:
        st.caption('No related incidents found outside this upload.')
    key=report_key(chunk,history,endpoint,model)
    report=st.session_state.get('results',{}).get(key)
    if report is None and reports:
        report=reports.get(key)
    if report:
        display_report(report)
    elif jobs:
        current=jobs.store.latest(key)
        active=current and current['status'] in ('queued','starting','running')
        if current:
            st.caption('Diagnosis job: '+current['status'])
            if current.get('error'):st.warning(current['error'])
        if active:
            st.button('Refresh diagnosis status')
            if st.button('Cancel diagnosis'):
                jobs.cancel(current['id'])
                st.rerun()
        elif st.button('Generate local diagnosis'):
            try:
                validate_endpoint(endpoint)
                jobs.store.submit(key,dict(anomaly=chunk.model_dump(),history=[h.model_dump() for h in history],endpoint=endpoint,model=model))
                jobs.poll()
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))


if __name__=='__main__':
    main()
