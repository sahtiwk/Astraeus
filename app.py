"""
Astraeus - Log Analysis & Anomaly Detection Agent
"""

import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from src.parser import parse_log_text
from src.anomaly import detect_anomalies
from src.vector_store import VectorStore

load_dotenv()

def decode_file(uploaded_file) -> str:
    bytes_data = uploaded_file.getvalue()
    
    # Try different encodings
    for encoding in ['utf-8', 'utf-16', 'latin-1']:
        try:
            return bytes_data.decode(encoding)
        except UnicodeDecodeError:
            continue
    
    st.error("Could not decode the file using standard encodings.")
    return ""

def main():
    st.set_page_config(page_title="Astraeus", page_icon="🔍", layout="wide")
    st.title("Astraeus - Log Analysis & Anomaly Detection")
    st.markdown("Upload your log files to parse, detect anomalies, and retrieve similar incidents.")
    
    st.sidebar.header("Configuration")
    env_gemini_key = os.getenv("GEMINI_API_KEY")
    if not env_gemini_key:
        user_gemini_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password")
        if user_gemini_key:
            os.environ["GEMINI_API_KEY"] = user_gemini_key
            st.sidebar.success("API Key applied!")
        else:
            st.sidebar.warning("Please provide a Gemini API Key to enable embeddings and similarity search.")
    else:
        st.sidebar.success("Gemini API Key detected from environment.")
    
    vector_store = None
    try:
        vector_store = VectorStore()
    except Exception as e:
        st.sidebar.error(f"Could not load local Vector Database: {e}")
    
    st.header("Log Ingestion & Parsing")
    uploaded_file = st.file_uploader("Choose a log file", type=["log", "txt"])
    
    if uploaded_file is not None:
        if uploaded_file.size == 0:
            st.warning("The uploaded file is empty.")
            return
            
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > 50:
            st.error(f"File size ({file_size_mb:.2f} MB) exceeds the 50MB limit.")
            return
            
        with st.spinner("Decoding file..."):
            raw_log_text = decode_file(uploaded_file)
            
        if not raw_log_text:
            return
            
        st.success("File successfully ingested!")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("File Information")
            st.text(f"Filename: {uploaded_file.name}")
            st.text(f"File Size: {file_size_mb:.2f} MB")
        
        with col2:
            st.subheader("Raw Log Preview")
            lines = raw_log_text.splitlines()
            preview_text = "\n".join(lines[:5])
            st.code(preview_text, language="text")
            
        st.divider()
        st.subheader("Parsed Log Events")
        
        with st.spinner("Parsing logs..."):
            parsed_events = parse_log_text(raw_log_text)
            
        if parsed_events:
            st.info(f"Successfully parsed {len(parsed_events)} events.")
            df = pd.DataFrame([event.model_dump() for event in parsed_events])
            st.dataframe(df.head(50), use_container_width=True)
            
            st.divider()
            st.subheader("Anomaly Detection & Retrieval")
            with st.spinner("Detecting anomalies..."):
                anomalies = detect_anomalies(parsed_events)
                
            if anomalies:
                st.warning(f"Detected {len(anomalies)} anomalous regions in the logs.")
                
                has_key = bool(os.getenv("GEMINI_API_KEY"))
                
                if vector_store and has_key:
                    with st.spinner("Indexing new anomalies into local Vector Database..."):
                        try:
                            vector_store.index_anomaly_chunks(anomalies)
                        except Exception as e:
                            st.error(f"Failed to index anomalies: {e}")
                
                for i, chunk in enumerate(anomalies):
                    with st.expander(f"Anomaly {i+1} | Severity: {chunk.severity} | Keywords: {', '.join(chunk.keywords)}"):
                        st.text(f"Start: {chunk.start_ts} | End: {chunk.end_ts}")
                        st.code(chunk.chunk_text, language="text")
                        
                        if not has_key:
                            st.info("Provide a Gemini API Key in the sidebar to view similar historical incidents.")
                        elif vector_store:
                            st.markdown("##### Similar Incidents (Semantic Search Context)")
                            with st.spinner("Searching for similar incidents..."):
                                try:
                                    similar = vector_store.query_similar_anomalies(chunk.chunk_text, limit=3)
                                    similar = [s for s in similar if s.chunk_id != chunk.chunk_id]
                                    if similar:
                                        for idx, sim in enumerate(similar):
                                            st.markdown(f"**Incident {idx+1}** | Severity: `{sim.severity}` | Keywords: `{', '.join(sim.keywords)}`")
                                            st.code(sim.chunk_text, language="text")
                                    else:
                                        st.write("No similar historical incidents found in the local vector database yet.")
                                except Exception as e:
                                    st.error(f"Failed to retrieve similar incidents: {e}")
                                    
                            st.divider()
                            st.markdown("##### AI Root Cause Analysis")
                            if st.button(f"Analyze Root Cause for Anomaly {i+1}", key=f"rca_btn_{i}"):
                                with st.spinner("Generating structured RCA using Gemini..."):
                                    try:
                                        from src.llm_analysis import generate_rca
                                        rca = generate_rca(chunk, similar if 'similar' in locals() else None)
                                        
                                        st.success("Analysis Complete!")
                                        st.markdown(f"**Summary**: {rca.summary}")
                                        
                                        col1_rca, col2_rca = st.columns(2)
                                        with col1_rca:
                                            st.metric("Confidence", f"{int(rca.confidence * 100)}%")
                                            st.info(f"**Severity**: {rca.severity}")
                                        with col2_rca:
                                            st.info(f"**Component**: {rca.affected_component}")
                                            st.warning(f"**Root Cause**: {rca.probable_root_cause}")
                                            
                                        st.markdown("**Evidence Lines:**")
                                        for line in rca.evidence_lines:
                                            st.code(line, language="text")
                                            
                                        st.markdown("**Recommended Actions:**")
                                        for action in rca.recommended_actions:
                                            st.markdown(f"- {action}")
                                    except Exception as e:
                                        st.error(f"Failed to generate RCA: {e}")
            else:
                st.success("No significant anomalies detected in the logs.")
        else:
            st.warning("No valid log events could be parsed from the file.")

if __name__ == "__main__":
    main()
