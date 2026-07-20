import math,statistics
def evaluate(r,z,capacity):
 n=len(r); assert n==len(z) and n>0
 wins=[x for x in r if x>0]; losses=[-x for x in r if x<0]; equity=peak=1.; dd=0.
 for x in r: equity*=1+x; peak=max(peak,equity); dd=max(dd,1-equity/peak)
 down=[min(0,x) for x in r]; pf=sum(wins)/sum(losses) if losses else 99.
 m={"sample_size":n,"realized_mean":statistics.mean(r),"realizable_mean":statistics.mean(z),"median_return":statistics.median(r),"hit_rate":len(wins)/n,"profit_factor":pf,"expectancy":statistics.mean(r),"max_drawdown":dd,"downside_deviation":math.sqrt(sum(x*x for x in down)/n),"tail_loss":sorted(r)[max(0,int(n*.1)-1)],"capacity_score":capacity,"consistency":len(wins)/n}
 if n<8:s="INSUFFICIENT_SAMPLE"
 elif capacity<.5 or m["realizable_mean"]<=0:s="NON_ACTIONABLE_CAPACITY"
 elif dd>.35 or m["tail_loss"]<-.30:s="FRAGILE_EDGE"
 elif pf>=1.5 and m["consistency"]>=.55:s="REPEATABLE_EDGE"
 else:s="UNPROVEN_EDGE"
 return {"status":s,"metrics":m,"copyable":s=="REPEATABLE_EDGE","strongest_alternative_hypothesis":"REGIME_SPECIFIC_SUCCESS_OR_SURVIVORSHIP_BIAS"}
