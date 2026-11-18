"""Reproducible diagnostic proxies; not a substitute for blinded expert review."""
import argparse
import json
import re
import statistics
import time
import threading
from pathlib import Path
import psutil
from src.pipeline import ingest
from src.llm_analysis import generate_rca, PROMPT_VERSION


def tokens(text):return set(re.findall(r'[a-z]+',text.lower()))

def percentile(values,p):
    if not values:return None
    values=sorted(values)
    return values[round((len(values)-1)*p)]


def evaluate(cases,split,output,endpoint=None,model='local',semantic=False,limit=None,server_pid=None):
    from src.schemas import AnomalyChunk
    corpus=[c for c in cases if c['split']=='train' and c['should_detect']]
    targets=[c for c in cases if c['split']==split]
    if limit:targets=targets[:limit]
    history=[ingest(c['logs'].encode())['anomalies'][0] for c in corpus]
    vectors=None
    if semantic:
        import numpy as np
        from src.embeddings import get_embeddings
        vectors=np.array(get_embeddings([h.chunk_text for h in history]))
    rows=[];latencies=[];peak=[0];stop=threading.Event()
    def monitor():
        while not stop.wait(0.1):
            processes=[psutil.Process()]
            if server_pid:
                try:
                    server=psutil.Process(server_pid);processes+=[server]+server.children(recursive=True)
                except psutil.Error:pass
            memory=0
            for process in processes:
                try:memory+=process.memory_info().rss
                except psutil.Error:pass
            peak[0]=max(peak[0],memory)
    thread=threading.Thread(target=monitor,daemon=True);thread.start()
    try:
        for case in targets:
            state=ingest(case['logs'].encode());chunks=state['anomalies']
            row={'id':case['id'],'family':case['family'],'detected':bool(chunks),'should_detect':case['should_detect'],'outputs':{}}
            if chunks:
                chunk=chunks[0]
                lexical=sorted(range(len(history)),key=lambda i:len(tokens(chunk.chunk_text)&tokens(history[i].chunk_text))/max(1,len(tokens(chunk.chunk_text)|tokens(history[i].chunk_text))),reverse=True)[:3]
                row['lexical_hit_at_3']=any(corpus[i]['family']==case['family'] for i in lexical)
                ranked=lexical
                if vectors is not None:
                    from src.embeddings import get_embedding
                    q=np.array(get_embedding(chunk.chunk_text));ranked=list(np.argsort(-(vectors@q))[:3])
                    row['semantic_hit_at_3']=any(corpus[i]['family']==case['family'] for i in ranked)
                if endpoint:
                    for mode,context in [('base',[]),('retrieval',[history[i] for i in ranked])]:
                        t=time.perf_counter()
                        try:
                            report=generate_rca(chunk,context,endpoint=endpoint,model=model)
                            elapsed=time.perf_counter()-t;latencies.append(elapsed)
                            cause=report.probable_root_cause.lower()
                            row['outputs'][mode]={'status':'valid','latency_s':elapsed,'term_match_proxy':any(term in cause for term in case['expected_terms']),
                                'abstention_proxy':any(term in cause for term in ['insufficient','cannot determine','not enough','unclear','unknown']),
                                'report':report.model_dump()}
                        except Exception as exc:
                            elapsed=time.perf_counter()-t;latencies.append(elapsed)
                            row['outputs'][mode]={'status':'rejected','latency_s':elapsed,'error':str(exc)}
            rows.append(row)
            print(f"Evaluated {len(rows)}/{len(targets)}: {case['id']}",flush=True)
            Path(output).parent.mkdir(parents=True,exist_ok=True)
            Path(output).write_text(json.dumps({'partial':True,'rows':rows},indent=2),encoding='utf-8')
    finally:stop.set();thread.join()
    tp=sum(r['detected'] and r['should_detect'] for r in rows)
    fp=sum(r['detected'] and not r['should_detect'] for r in rows)
    fn=sum(not r['detected'] and r['should_detect'] for r in rows)
    metrics={'cases':len(rows),'detection_precision':tp/(tp+fp) if tp+fp else None,'detection_recall':tp/(tp+fn) if tp+fn else None,
             'false_alerts':fp,'latency_p50_s':percentile(latencies,.5),'latency_p95_s':percentile(latencies,.95),'peak_process_tree_rss_gib':peak[0]/2**30}
    for name in ['lexical_hit_at_3','semantic_hit_at_3']:
        vals=[r[name] for r in rows if name in r];metrics[name]=sum(vals)/len(vals) if vals else None
    for mode in ['base','retrieval']:
        vals=[r['outputs'][mode] for r in rows if mode in r['outputs']]
        valid=[v for v in vals if v['status']=='valid']
        metrics[mode]={'attempts':len(vals),'valid_reports':len(valid),'term_match_proxy':sum(v['term_match_proxy'] for v in valid)/len(vals) if vals else None}
    result={'partial':False,'split':split,'model':model,'semantic':semantic,'prompt_version':PROMPT_VERSION,'metrics':metrics,'rows':rows,
        'limitations':['Controlled same-template cases; not production generalization.','Term matching and abstention are automated proxies, not independently scored diagnosis correctness.','Matching evidence lines does not establish semantic support.','Peak RSS sums processes and may double count shared pages.']}
    Path(output).write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--split',choices=['validation','test'],default='validation')
    parser.add_argument('--endpoint');parser.add_argument('--model',default='local');parser.add_argument('--semantic',action='store_true')
    parser.add_argument('--limit',type=int);parser.add_argument('--server-pid',type=int);parser.add_argument('--output',default='evaluation/results.json')
    args=parser.parse_args();cases=[json.loads(x) for x in (Path(__file__).parent/'cases.jsonl').read_text().splitlines()]
    print(json.dumps(evaluate(cases,args.split,args.output,args.endpoint,args.model,args.semantic,args.limit,args.server_pid)['metrics'],indent=2))
