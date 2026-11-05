def render():
    import json
    from pathlib import Path
    import pandas as pd
    import streamlit as st
    from model import GROUPS, FIELDS, DEFAULTS, calculate, validate, bridge
    
    
    
    def reset():
        for k,v in DEFAULTS.items():
            st.session_state[k]=v
        st.session_state.pop('import_status',None)
    
    def import_json():
        try:
            f=st.session_state['scenario_file']
            if f is None:
                return
            obj=json.loads(f.getvalue().decode('utf-8-sig'))
            if obj.get('schema') != 1:
                raise ValueError('지원하지 않는 파일 형식')
            v=dict(obj['inputs'])
            v.setdefault('cuMinDed',0.0)  # old scenarios preserve original zero-deduction economics
            validate(v)
            for k in DEFAULTS:
                st.session_state[k]=v[k]
            st.session_state['import_status']='시나리오를 불러왔어.'
        except (ValueError, KeyError, TypeError, AttributeError, UnicodeError) as e:
            st.session_state['import_status']='불러오기 실패: '+str(e)
    
    for k,v in DEFAULTS.items():
        st.session_state.setdefault(k,v)
    st.subheader('통합 분석 — 공통 입력으로 연결')
    st.caption('공통 Assay → 제련 수익 → 금융비용 → 순현금마진 → 목표 Spot TC 역산')
    st.warning('가격은 원본 예시값이며 최신 시세가 아니야. 제련소 관점의 정태적 현금 경제성 모델이야.')
    with st.expander('통합 분석 입력 조건',expanded=True):
        st.header('분석 조건')
        st.button('통합 기본값 복원',on_click=reset)
        st.file_uploader('시나리오 JSON 불러오기',type=['json'],key='scenario_file',on_change=import_json)
        if 'import_status' in st.session_state:
            st.info(st.session_state['import_status'])
        for i,(title,fields) in enumerate(GROUPS):
            with st.expander(title,expanded=i==0):
                for d in fields:
                    kw={'key':d[0],'step':0.1,'format':'%.4f'}
                    if len(d)>4: kw['min_value']=float(d[4])
                    if len(d)>5: kw['max_value']=float(d[5])
                    st.number_input(f'{d[1]} ({d[2]})',**kw)
                if i==3:
                    st.selectbox('TCRC 환산 방식',['dynamic','fixed'],key='mode',format_func=lambda x:{'dynamic':'Cu 지급량 연동 (RC=TC/10)','fixed':'고정계수'}[x])
                if i==4:
                    st.selectbox('금융비용 차감',['yes','no'],key='finance',format_func=lambda x:'차감 (운영비에 미포함)' if x=='yes' else '미차감 (이미 포함 등)')
                    st.selectbox('금융대상 금속',['yes','no'],key='metals',format_func=lambda x:'Cu + Au + Ag' if x=='yes' else 'Cu만')
    v={k:st.session_state[k] for k in DEFAULTS}
    try:
        r=calculate(v)
    except ValueError as e:
        st.error(str(e))
        st.stop()
    fmt=lambda n:'산출 불가' if n is None else f'{n:,.2f}'
    for group in [[('금융비 차감 후 마진',r['M']),('목표 달성 필요 Spot TC',r['implied']),('금융비용',r['F'])],[('Non-TCRC 수익',r['N']),('현재 가중 TC',r['W']),('목표 대비 마진 차이',r['M']-v['target'])]]:
        for col,(label,n) in zip(st.columns(3),group):
            col.metric(label,fmt(n),help='USD / DMT')
    profit,tc,sensitivity,method=st.tabs(['손익 분석','목표 TC 역산','민감도 · 시나리오','계산 근거 · 한계'])
    rows=bridge(v,r)
    with profit:
        st.subheader('수익 → 비용 → 순현금마진')
        frame=pd.DataFrame(rows,columns=['항목','USD/DMT'])
        frame['전체 물량 USD']=frame['USD/DMT']*v['volume']
        st.dataframe(frame.style.format({'USD/DMT':'{:,.2f}','전체 물량 USD':'{:,.2f}'}),hide_index=True,width='stretch')
        st.caption('Free metal은 회수량−지급량이며 음수도 반영. 소계와 마진 행은 중복 합산하지 않아.')
        st.bar_chart(pd.DataFrame(rows[:5],columns=['항목','USD/DMT']).set_index('항목'))
    with tc:
        st.write(f"지급 Cu: **{r['q']*100:.4f}% of DMT** · 지급 Au: {r['qa']:.4f} g/DMT · 지급 Ag: {r['qs']:.4f} g/DMT")
        st.caption('Cu 지급량 = max(0, min(품위 × 지급률, 품위 − 최소공제)). 최소공제 1은 Cu 품위에서 1 percentage point 공제하는 뜻이야.')
        st.write(f"TCRC 계수: **{r['K']:.6f}** · 손익분기 가중 TC: **{fmt(r['breakeven'])}** · 목표 필요 가중 TC: **{fmt(r['required'])}** USD/DMT")
        if r['implied'] is None:
            st.warning(f"Benchmark 비중 100%: Spot 물량이 없어 역산 불가. 현재 목표 대비 마진 차이: {fmt(r['M']-v['target'])} USD/DMT")
        else:
            st.success(f"필요 Spot TC: {fmt(r['implied'])} USD/DMT · 역대입 오차: {calculate(v|{'spot':r['implied']})['M']-v['target']:.8f}")
            if v['share']>=90: st.warning('Spot 물량이 작아 역산값이 크게 변할 수 있어.')
            xs=[v['benchmark']-100+i*10 for i in range(21)]
            chart=pd.DataFrame({'Benchmark TC':xs,'필요 Spot TC':[(r['required']-r['b']*x)/(1-r['b']) for x in xs]}).set_index('Benchmark TC')
            st.line_chart(chart)
        st.caption('목표마진을 만족시키는 조건의 역산이야. 시장가격 전망을 의미하지 않아.')
    with sensitivity:
        st.subheader('Spot TC × 금융기간: 순현금마진 (USD/DMT)')
        spots=[v['spot']+d for d in [-100,-50,0,50,100]]
        days=sorted(set([max(0,v['days']-30),v['days'],v['days']+30]))
        matrix=pd.DataFrame({f'{d:g}일':[calculate(v|{'spot':s,'days':d})['M'] for s in spots] for d in days},index=pd.Index(spots,name='Spot TC'))
        st.dataframe(matrix.style.format('{:,.2f}').map(lambda x:'background-color: '+('#dff2e9' if x>=0 else '#f9e4e3')),width='stretch')
        scenarios=[('현재',{}),('황산 수익 −20%',{'acidPrice':v['acidPrice']-abs(v['acidPrice'])*.2}),('금리 +1%p · 기간 +30일',{'rate':v['rate']+1,'days':v['days']+30}),('Cu·Au·Ag 가격 −10%',{k:v[k]*.9 for k in ['cuPrice','auPrice','agPrice']}),('Spot TC −50',{'spot':v['spot']-50}),('고정계수 1.55',{'mode':'fixed','factor':1.55})]
        results=[]
        for name,patch in scenarios:
            s=calculate(v|patch)
            results.append({'시나리오':name,'마진':s['M'],'현재 대비':s['M']-r['M'],'필요 Spot TC':s['implied']})
        st.dataframe(pd.DataFrame(results).style.format({k:'{:,.2f}' for k in ['마진','현재 대비','필요 Spot TC']},na_rep='산출 불가'),hide_index=True,width='stretch')
        st.caption('각 충격은 분석용 가정이며 발생 확률을 의미하지 않아.')
    with method:
        st.html(Path(__file__).with_name('methodology.html').read_text(encoding='utf-8'))
        st.info('운영비에 금융비가 이미 포함되어 있다면 금융비 차감을 끄거나 운영비에서 먼저 제외해야 해. 금융원금은 실지급 인보이스가 아닌 지급금속 총가치 기준이야.')
    c1,c2=st.columns(2)
    c1.download_button('현재 시나리오 JSON 저장',json.dumps({'schema':1,'inputs':v},ensure_ascii=False,indent=2),'concentrate_scenario.json','application/json')
    export=[['입력',d[1],v[d[0]],d[2]] for d in FIELDS]+[['선택',k,v[k],''] for k in ['mode','finance','metals']]+[['결과',n,x,'USD/DMT'] for n,x in rows]+[['결과','필요 Spot TC',r['implied'],'USD/DMT']]+[['시나리오',s['시나리오'],s['마진'],'USD/DMT'] for s in results]
    c2.download_button('분석 결과 CSV',pd.DataFrame(export,columns=['구분','항목','값','단위']).to_csv(index=False).encode('utf-8-sig'),'concentrate_analysis.csv','text/csv')
