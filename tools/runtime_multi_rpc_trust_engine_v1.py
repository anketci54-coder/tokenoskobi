from statistics import median

RPC_TIMEOUT_MS=1500

def consensus(values):
    return median(values)

def trust_score(latency_ms,height_ok,time_ok):
    score=100
    if latency_ms>500:
        score-=20
    if not height_ok:
        score-=40
    if not time_ok:
        score-=40
    return max(score,0)
