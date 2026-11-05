# 정광 분석 도구 — 독립 3탭 + 통합 1탭

## 로컬 실행
Python 3.11 권장. 이 폴더에서:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud 배포
1. ZIP을 풀고 이 폴더 안의 파일을 GitHub 저장소에 업로드한다. `.streamlit/config.toml`도 포함한다.
2. Streamlit Community Cloud에서 앱 생성을 선택하고 저장소와 브랜치를 지정한다.
3. Main file path를 `app.py`로 지정한다. 하위 폴더째 업로드했다면 `concentrate_streamlit/app.py`처럼 실제 경로를 지정한다.
4. Python 3.11을 선택하고 배포한다.

`app.py`, `model.py`, `fields.json`, `methodology.html`, `requirements.txt`는 같은 폴더에 둔다.
API 키나 별도 DB는 필요하지 않다. 입력은 세션에만 남는다. 재사용하려면 JSON을 다운로드한다.
외부 가격 조회 기능은 없다. 원본 예시 가격을 사용하므로 실제 분석 시 입력을 갱신한다.

## 기능
- 공통 Assay, payable, 회수율, 가격 입력
- 제련 수익·금융비·순현금마진, 전체 물량 손익
- Cu 지급량 연동 TCRC / 고정계수 비교
- 목표 Spot TC 역산 및 Benchmark 대비 차트
- TC × 기간 민감도, 가격·금리 시나리오
- 이전 통합 HTML과 호환되는 JSON 입출력, 결과 CSV

## 검증
```bash
python -m unittest -v test_model.py
```

계산은 제련소 관점. 실제 트레이더 손익, 별도 RC, 페널티, 세금, QP 및 헤지손익은 자동 계산하지 않는다.


## v2 탭 구성
1. 제련소 마진: 원본 HTML 화면과 계산 기능 유지, Cu minimum deduction 추가.
2. Benchmark / Spot TC: 원본 HTML 유지. 100% Benchmark 비중의 표·CSV 예외 수정.
3. 금융비용: 원본 HTML 유지. 직접 지급 Cu량 또는 grade/payable/minimum deduction 계산 선택.
4. 통합 분석: 별도 공통 입력으로 제련 수익 → 금융비용 → 목표 Spot TC 연결.

각 탭의 입력은 독립적이며 자동 동기화하지 않는다. 독립 HTML 입력은 iframe 내부 메모리에만 있다.
Streamlit 재실행 시 독립 HTML 입력은 초기화될 수 있다. 안정적인 시나리오 저장은 통합 탭의 JSON을 사용한다.
1~3번 탭 HTML은 각각 다운로드해서 독립 브라우저에서도 실행 가능하다.

Cu minimum deduction 단위는 percentage points of concentrate Cu grade.
지급 Cu(% of DMT) = max(0, min(Cu grade × payable / 100, Cu grade − minimum deduction)).
예: grade 24%, payable 96.5%, minimum deduction 1pp → min(23.16%,23%) = 23%.
제련소와 통합 신규 기본 공제 1pp는 예시 가정이다. 0이면 원본 계산 재현.
금융 탭 기본은 원본의 직접 지급 Cu 24%; 공제 적용 계산을 체크하면 23%가 된다.
예전 통합 JSON을 불러오면 누락된 공제는 0으로 처리하여 기존 손익을 유지한다.
ZIP 안 html/ 폴더, integrated.py, model.py, fields.json, methodology.html도 함께 업로드해야 한다.
