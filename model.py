"""Pure calculation engine. All monetary outputs are USD per DMT."""
import json
import math
from pathlib import Path

GROUPS = json.loads(Path(__file__).with_name('fields.json').read_text(encoding='utf-8'))
FIELDS = [d for _, fields in GROUPS for d in fields]
DEFAULTS = {d[0]: float(d[3]) for d in FIELDS} | {'mode': 'dynamic', 'metals': 'yes', 'finance': 'yes'}

def validate(v):
    for d in FIELDS:
        x = v.get(d[0])
        if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
            raise ValueError(f'{d[1]}: 유효한 숫자가 필요해.')
        if len(d) > 4 and x < d[4] or len(d) > 5 and x > d[5]:
            raise ValueError(f'{d[1]}: 허용범위를 확인해.')
    for k, choices in {'mode': ['dynamic','fixed'], 'metals':['yes','no'], 'finance':['yes','no']}.items():
        if v.get(k) not in choices:
            raise ValueError(f'{k}: 선택값 오류')

def calculate(v):
    validate(v)
    q=max(0,min(v['cuGrade']/100*v['cuPay']/100,(v['cuGrade']-v['cuMinDed'])/100))
    qa=max(0,v['auGrade']-v['auDed'])*v['auPay']/100
    qs=max(0,v['agGrade']-v['agDed'])*v['agPay']/100
    fc=(v['cuGrade']/100*v['cuRec']/100-q)*v['cuPrice']
    fa=(v['auGrade']*v['auRec']/100-qa)*v['auPrice']/31.1034768
    fs=(v['agGrade']*v['agRec']/100-qs)*v['agPrice']/31.1034768
    acid=v['acidRatio']*v['acidPrice']/v['fx']
    prem=v['cuGrade']/100*v['cuRec']/100*v['premium']/v['fx']
    N=fc+fa+fs+acid+prem
    values=[q*v['cuPrice'],qa*v['auPrice']/31.1034768,qs*v['agPrice']/31.1034768]
    fin=[x*v['rate']/100*v['days']/365 if i==0 or v['metals']=='yes' else 0 for i,x in enumerate(values)]
    F=sum(fin) if v['finance']=='yes' else 0
    K=1+q*2204.62262185/1000 if v['mode']=='dynamic' else v['factor']
    b=v['share']/100
    W=b*v['benchmark']+(1-b)*v['spot']
    T=K*W
    pre=N+T-v['cost']-v['extra']
    M=pre-F
    required=(v['cost']+v['extra']+F+v['target']-N)/K
    breakeven=(v['cost']+v['extra']+F-N)/K
    implied=None if b==1 else (required-b*v['benchmark'])/(1-b)
    return {k: val for k,val in locals().items() if k != 'v'}

def bridge(v,r):
    return [('Free Cu',r['fc']),('Free Au',r['fa']),('Free Ag',r['fs']),('황산 수익',r['acid']),('Cathode 프리미엄',r['prem']),('Non-TCRC 수익 소계',r['N']),('가중 TC 수익',r['W']),('RC 상당 수익',r['T']-r['W']),('운영비',-v['cost']),('추가비용',-v['extra']),('금융비 차감 전 마진',r['pre']),*[(n,-r['fin'][i] if v['finance']=='yes' else 0) for i,n in enumerate(['Cu 금융비','Au 금융비','Ag 금융비'])],('금융비 차감 후 마진',r['M'])]
