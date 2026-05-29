import os
import json
from typing import List, Optional
from google import genai
from google.genai import types
from src.schemas import AnomalyChunk, RCAResponse

def generate_rca(anomaly: AnomalyChunk, historical_context: Optional[List[AnomalyChunk]] = None) -> RCAResponse:
    """
    Generate a Root Cause Analysis (RCA) report using Google Gemini.
    """
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY is not set.")
        
    client = genai.Client(api_key=key)
    
    prompt = (
        "You are an expert DevOps engineer and Site Reliability Engineer (SRE). "
        "Your task is to analyze the following anomalous log chunk and provide a structured Root Cause Analysis (RCA).\n\n"
        f"ANOMALY DETAILS:\n"
        f"- Severity: {anomaly.severity}\n"
        f"- Keywords: {', '.join(anomaly.keywords)}\n"
        f"- Start Time: {anomaly.start_ts}\n"
        f"- End Time: {anomaly.end_ts}\n"
        f"- Log Lines:\n{anomaly.chunk_text}\n\n"
    )
    
    if historical_context:
        prompt += "HISTORICAL SIMILAR INCIDENTS:\n"
        for i, ctx in enumerate(historical_context):
            prompt += (
                f"Incident {i+1} (Severity: {ctx.severity}):\n"
                f"{ctx.chunk_text}\n\n"
            )
            
    prompt += (
        "Analyze the logs and any provided historical context to determine the root cause of the anomaly. "
        "Extract the exact log lines that prove the root cause as 'evidence_lines'."
    )
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RCAResponse,
            temperature=0.2
        )
    )
    
    try:
        parsed_json = json.loads(response.text)
        return RCAResponse(**parsed_json)
    except Exception as e:
        raise RuntimeError(f"Failed to parse LLM RCA output: {e}\nRaw response: {response.text}")
