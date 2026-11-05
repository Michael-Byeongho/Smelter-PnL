from pathlib import Path
import streamlit as st
from integrated import render

st.set_page_config(page_title='정광 분석 도구',page_icon='📊',layout='wide')
st.title('정광 분석 도구')
st.caption('독립 모델 3개 + 통합 분석 1개 · 각 탭의 입력은 별도로 유지')
st.info('1~3번은 원본 HTML 기반 독립 도구야. 4번은 품위·payable·가격·금융조건을 함께 연결하는 통합 분석이야. 탭 사이 입력은 자동 동기화되지 않아.')
tabs=st.tabs(['① 제련소 마진','② Benchmark / Spot TC','③ 정광 금융비용','④ 통합 분석'])
for tab,name,title in [(tabs[0],'smelter_margin.html','제련소 마진: Cu 최소공제 반영'),(tabs[1],'tc_model.html','TC 역산: 원본 고정계수 방식'),(tabs[2],'financing.html','금융비용: 직접 지급 Cu 입력 / 최소공제 적용 선택')]:
    with tab:
        st.subheader(title)
        source=(Path(__file__).parent/'html'/name).read_text(encoding='utf-8')
        st.download_button('이 탭 HTML 다운로드',source,name,'text/html',key='download_'+name)
        st.iframe(source,height=1550)
with tabs[3]:
    render()
