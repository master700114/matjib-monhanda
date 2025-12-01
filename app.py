
import streamlit as st
import google.generativeai as genai
import plotly.graph_objects as go
import json
import os
import streamlit.components.v1 as components


# 1. 페이지 설정
st.set_page_config(page_title="맛집 장담 몬한다", page_icon="🚫", layout="centered")


# ==============================================================================
# [🚨 주인님! 앱 배포 주소 확인하셨죠?]
# ==============================================================================
REAL_APP_URL = "https://matjib-monhanda-tfkwuykhzlvyykmg5tipe7.streamlit.app/"


# 2. 토스 스타일 CSS
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .step-title { font-size: 26px; font-weight: 700; color: #191F28; margin-bottom: 10px; animation: fadeIn 0.5s; }
    .step-sub { font-size: 16px; color: #8B95A1; margin-bottom: 30px; }
    div.stButton > button { background-color: #3182F6; color: white; border: none; border-radius: 16px; padding: 18px; font-size: 18px; font-weight: 700; width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: 0.2s; }
    div.stButton > button:hover { background-color: #1B64DA; transform: translateY(-2px); }
    .secondary-btn button { background-color: #F2F4F6 !important; color: #4E5968 !important; box-shadow: none !important; }
    div[role="radiogroup"] label { background-color: #F2F4F6; padding: 16px; border-radius: 14px; margin-bottom: 12px; border: 2px solid transparent; transition: 0.2s; width: 100%; color: #4E5968; font-weight: 500; cursor: pointer; }
    div[role="radiogroup"] label:hover { background-color: #E5E8EB; }
    div[role="radiogroup"] label:has(input:checked) { background-color: #E8F3FF; border: 2px solid #3182F6; color: #3182F6; font-weight: 700; }
    div[role="radiogroup"] label:has(input:checked) p { color: #3182F6 !important; }
    div[role="radiogroup"] > label > div:first-of-type { display: none; }
    .total-score-val { font-size: 60px; font-weight: 900; color: #3182F6; text-align: center; line-height: 1.0; margin-bottom: 20px; }
    .stat-box { background-color: #F9FAFB; border-radius: 12px; padding: 15px; text-align: center; }
    .stat-val { font-size: 16px; font-weight: 700; color: #333D4B; }
    .highlight-blue { color: #3182F6; }
    .highlight-red { color: #E9463D; }
    .summary-box { background-color: #E8F3FF; padding: 20px; border-radius: 16px; color: #1B64DA; font-weight: 600; text-align: center; margin-bottom: 15px; border: 1px solid #3182F6; line-height: 1.5; }
    .time-box { background-color: #F9FAFB; padding: 15px; border-radius: 12px; color: #4E5968; font-size: 15px; text-align: center; margin-bottom: 20px; border: 1px solid #E5E8EB; }
    .time-warning { font-size: 12px; color: #E9463D; margin-top: 5px; }
    .detail-card { background-color: #ffffff; border: 1px solid #E5E8EB; border-radius: 16px; padding: 20px; margin-top: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.03); }
    .detail-title { font-size: 18px; font-weight: 700; color: #191F28; margin-bottom: 10px; display: flex; align-items: center; }
    .detail-content { font-size: 16px; line-height: 1.7; color: #333D4B; }
    .action-btn { display: block; width: 100%; padding: 16px; text-align: center; text-decoration: none; border-radius: 12px; font-weight: 700; font-size: 16px; margin-top: 10px; }
    .catch-btn { background-color: #FF3B30; color: white; }
    .tabling-btn { background-color: #FF2D55; color: white; }
    .call-btn { background-color: #333D4B; color: white; }
    .naver-btn { background-color: #03C75A; color: white; }
    .share-container { display: flex; gap: 10px; margin-top: 10px; }
    .share-btn { display: block; width: 100%; padding: 18px; border-radius: 16px; text-align: center; text-decoration: none; font-weight: 700; font-size: 18px; color: #191F28; background-color: #F2F4F6; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .kakao-link { background-color: #FEE500; color: #191F28; } 
    .insta-link { background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); color: white; }
    .error-box { background-color: #FFF0F0; border: 1px solid #E9463D; border-radius: 12px; padding: 15px; color: #E9463D; font-size: 14px; margin-bottom: 15px; }
    .info-box { background-color: #F0F8FF; border: 1px solid #3182F6; border-radius: 12px; padding: 12px; color: #333D4B; font-size: 13px; margin-top: 8px; }
    
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
    """, unsafe_allow_html=True)


# 3. 상태 관리
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'persona' not in st.session_state:
    st.session_state.persona = ""
if 'companion' not in st.session_state:
    st.session_state.companion = ""
if 'restaurant' not in st.session_state:
    st.session_state.restaurant = ""
if 'show_copy' not in st.session_state:
    st.session_state.show_copy = False
if 'analysis_error' not in st.session_state:
    st.session_state.analysis_error = ""


# 4. API 키 로드
api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]


# 5. 캐싱 함수 - 개선된 프롬프트
@st.cache_data(show_spinner=False)
def analyze_restaurant(_model, restaurant, companion, persona):
    """
    개선사항:
    1. 페르소나별 명확한 캐릭터 정의
    2. JSON 형식 엄격하게 강제
    3. 점수는 반드시 0~100 정수
    4. 동행인 맥락을 분석 로직에 명시적으로 반영
    5. 팩트체크 및 "모르면 말하기" 강조
    """
    
    # 페르소나별 캐릭터 + 지시사항
    if "착한" in persona:
        persona_inst = """너는 '착한 부산 행님'이다.
- 말투: 따뜻하고 친절한 부산 사투리 사용
- 스타일: 칭찬을 많이 하고 긍정적인 리뷰"""
    elif "지옥" in persona:
        persona_inst = """너는 '지옥의 독설가'다.
- 말투: 거칠지만 핵심을 찌르는 부산 사투리 사용
- 스타일: 고든 램지처럼 직설적이고 건설적인 비판"""
    else:
        persona_inst = """너는 '친근한 동네 형'이다.
- 말투: 수다스럽고 친절한 부산 사투리 사용
- 스타일: TMI 많지만 실용적인 정보 제공"""
    
    companion_key = companion.split(' ')[1]
    
    # 동행인별 분석 중점
    if "연인" in companion:
        companion_focus = "분위기, 웨이팅 시간, 데이트 적합도를 우선시해라."
    elif "친구" in companion:
        companion_focus = "맛, 가성비, 분위기를 균형있게 평가해라."
    elif "가족" in companion:
        companion_focus = "주차, 아이들 가능 여부, 시끄러운 정도, 아이 메뉴 유무를 중요하게 봐라."
    else:  # 직장동료
        companion_focus = "법카 가능 여부, 직장인들 분위기, 점심/저녁 웨이팅, 카드 결제 여부를 중요하게 봐라."
    
    prompt = f"""
[당신의 역할]
{persona_inst}

[분석 대상]
식당명: {restaurant}
동행인: {companion_key}
{companion_focus}

[필수 규칙]
1. 반드시 아래 JSON 형식만 출력하라. 다른 설명글은 절대 쓰지 마라.
2. 각 점수는 반드시 0~100 사이의 정수여야 한다.
3. 메뉴·영업시간·예약 방식·전화번호는 웹 검색 기반으로만 작성하라.
4. 확신 없는 정보는 "추측 금지" - "정보 없음"이라고 적어라.
5. 한줄평은 "{companion_key}와 함께" 맥락을 명시적으로 넣어라.
6. 최종 판결은 "{companion_key}이라는 점을 고려해서" 재추천 또는 재고할 이유를 구체적으로 적어라.

[출력 JSON 형식 (이것만 출력)]
{{
  "scores": [맛(0~100), 가성비(0~100), 서비스(0~100), 위생(0~100), 분위기(0~100)],
  "summary": "{companion_key}랑 가기에 좋은 이유를 한 문장으로(부산 사투리, 30자 이내)",
  "hours": "영업시간 또는 '정보 없음'",
  "reservation": "예약 방식(캐치테이블/테이블링/전화/현장) 또는 '정보 없음'",
  "phone": "전화번호 또는 '정보 없음'",
  "menu_tip": "이 {companion_key}한테 추천하는 메뉴 조합 및 꿀팁(부산 사투리, 3~5줄)",
  "atmosphere": "분위기, 웨이팅, {companion_key} 중심의 조언(부산 사투리, 3~5줄)",
  "verdict": "{companion_key}라는 조건에서의 최종 판결(부산 사투리, 2~3줄). 가면 후회할 가능성 또는 꼭 가볼 이유"
}}
"""
    
    response = _model.generate_content(prompt)
    return response.text


def safe_parse_json(text):
    """JSON 파싱 실패 시 더 자세한 에러 정보 제공"""
    try:
        clean_text = text.replace("```json", "").replace("```", "").strip()
        if "{" in clean_text:
            clean_text = clean_text[clean_text.find("{"):clean_text.rfind("}")+1]
            data = json.loads(clean_text)
            return data, None
        else:
            return None, "AI가 JSON 형식으로 응답하지 않았습니다. 다시 시도해주세요."
    except json.JSONDecodeError as e:
        return None, f"JSON 파싱 오류: {str(e)[:50]}. 다시 시도해주세요."
    except Exception as e:
        return None, f"예상치 못한 오류: {str(e)[:50]}. 다시 시도해주세요."


def validate_scores(scores):
    """점수 유효성 검증"""
    if not isinstance(scores, list) or len(scores) != 5:
        return None, "점수 형식이 잘못되었습니다."
    
    try:
        scores = [int(s) for s in scores]
        if any(s < 0 or s > 100 for s in scores):
            return None, "점수가 0~100 범위를 벗어났습니다."
        return scores, None
    except:
        return None, "점수가 숫자로 변환될 수 없습니다."


# ==================== STEP 0: 인트로 ====================
if st.session_state.step == 0:
    if os.path.exists("image_0.png"):
        st.image("image_0.png", use_container_width=True)
    else:
        st.markdown("<div style='text-align:center; margin-top:50px;'><div style='font-size: 40px; font-weight: 800;'>맛집,<br>장담 몬한다.</div></div>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    if st.button("시작하기"):
        st.session_state.step = 1
        st.rerun()


# ==================== STEP 1: AI 말투 선택 ====================
elif st.session_state.step == 1:
    if st.button("← 뒤로"):
        st.session_state.step = 0
        st.rerun()
    st.markdown("<div class='step-title'>어떤 행님한테 물어볼래?</div>", unsafe_allow_html=True)
    persona_choice = st.radio("말투", ["😇 착한 부산햄 (순한맛/칭찬봇)", "😎 친근한 부산햄 (중간맛/팩트/츤데레)", "🤬 지옥의 부산햄 (매운맛/독설/고든램지) ⚠️주의"], label_visibility="collapsed")
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    if st.button("다음"):
        st.session_state.persona = persona_choice
        st.session_state.step = 2
        st.rerun()


# ==================== STEP 2: 동행인 선택 ====================
elif st.session_state.step == 2:
    if st.button("← 뒤로"):
        st.session_state.step = 1
        st.rerun()
    st.markdown("<div class='step-title'>누구랑 같이 가나요?</div>", unsafe_allow_html=True)
    companion_choice = st.radio("동행인", ["❤️ 연인 (분위기/웨이팅)", "😎 친구 (맛/가성비)", "👨‍👩‍👧‍👦 가족 (주차/아이들)", "💼 직장동료 (법카/눈치)"], label_visibility="collapsed")
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    if st.button("다음"):
        st.session_state.companion = companion_choice
        st.session_state.step = 3
        st.rerun()


# ==================== STEP 3: 식당 입력 ====================
elif st.session_state.step == 3:
    if st.button("← 뒤로"):
        st.session_state.step = 2
        st.rerun()
    if "착한" in st.session_state.persona:
        q_text = "어떤 맛집이 궁금한데? 내한테 말해봐라."
    elif "지옥" in st.session_state.persona:
        q_text = "어디 가서 돈 낭비하려고? 이름 대."
    else:
        q_text = "어떤 식당이 궁금하노?"
    st.markdown(f"<div class='step-title'>{q_text}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='step-sub'><b>{st.session_state.companion.split(' ')[1]}</b>랑 가는군요.</div>", unsafe_allow_html=True)
    name_input = st.text_input("식당 이름", value=st.session_state.restaurant, placeholder="예: 부산대 톤쇼우", label_visibility="collapsed")
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    if st.button("분석 시작 🚀"):
        if not name_input:
            st.warning("식당 이름을 입력해주세요.")
        else:
            st.session_state.restaurant = name_input
            st.session_state.step = 4
            st.rerun()


# ==================== STEP 4: 결과 화면 ====================
elif st.session_state.step == 4:
    col_nav1, col_nav2 = st.columns([1, 1])
    with col_nav1:
        if st.button("← 다른 식당"):
            st.session_state.step = 3
            st.session_state.show_copy = False
            st.session_state.analysis_error = ""
            st.rerun()
    with col_nav2:
        if st.button("🔄 처음으로"):
            st.session_state.step = 0
            st.session_state.restaurant = ""
            st.session_state.show_copy = False
            st.session_state.analysis_error = ""
            st.rerun()

    if not api_key:
        st.markdown("<div class='error-box'>⚠️ <b>API 키 오류</b><br>앱의 API 키가 설정되지 않았습니다. 개발자에게 연락해주세요.</div>", unsafe_allow_html=True)
        st.stop()
    
    try:
        genai.configure(api_key=api_key)
        
        # 모델 리스트 조회 with 에러 처리 개선
        try:
            all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            safe_models = [m for m in all_models if "exp" not in m]
            target_model = next((m for m in safe_models if "flash" in m), safe_models[0] if safe_models else None)
            
            if not target_model:
                st.markdown("<div class='error-box'>⚠️ <b>모델 로드 실패</b><br>AI 모델을 불러올 수 없습니다. 잠시 후 다시 시도해주세요.</div>", unsafe_allow_html=True)
                st.stop()
            
            model = genai.GenerativeModel(target_model)
        
        except Exception as model_err:
            st.markdown(f"<div class='error-box'>⚠️ <b>AI 서버 오류</b><br>현재 AI 서버가 응답하지 않습니다. 10초 후 다시 시도해주세요.<br><small>({str(model_err)[:30]})</small></div>", unsafe_allow_html=True)
            st.stop()

        with st.spinner('AI 행님이 점수 계산기 두드리는 중...'):
            try:
                result_text = analyze_restaurant(model, st.session_state.restaurant, st.session_state.companion, st.session_state.persona)
                
                # 개선된 JSON 파싱
                data, parse_error = safe_parse_json(result_text)
                
                if parse_error:
                    st.markdown(f"<div class='error-box'>⚠️ <b>분석 형식 오류</b><br>{parse_error}</div>", unsafe_allow_html=True)
                    if st.button("🔄 다시 분석"):
                        st.session_state.analysis_error = ""
                        st.rerun()
                    st.stop()
                
                # 점수 유효성 검증
                raw_scores = data.get("scores", [50, 50, 50, 50, 50])
                scores, score_error = validate_scores(raw_scores)
                
                if score_error:
                    st.markdown(f"<div class='error-box'>⚠️ <b>점수 오류</b><br>{score_error}</div>", unsafe_allow_html=True)
                    if st.button("🔄 다시 분석"):
                        st.session_state.analysis_error = ""
                        st.rerun()
                    st.stop()

                categories = ['맛', '가성비', '서비스', '위생', '분위기']
                total_score = int(sum(scores) / 5)
                max_val = max(scores)
                min_val = min(scores)
                best_cat = categories[scores.index(max_val)]
                worst_cat = categories[scores.index(min_val)]
                
                # --- 결과 출력 ---
                companion_key = st.session_state.companion.split(' ')[1]
                st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align: center; color: #8B95A1; font-weight: 600;'>{companion_key}랑 갈 때 점수</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='total-score-val'>{total_score}점</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='summary-box'>🗣️ {data['summary']}</div>", unsafe_allow_html=True)
                
                hours = data.get('hours', '정보 없음')
                st.markdown(f"<div class='time-box'>⏰ <b>영업시간</b><br>{hours}<div class='time-warning'>*최종 확인은 지도/전화로 권장합니다</div></div>", unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"<div class='stat-box'><div class='stat-label'>👍 베스트</div><div class='stat-val highlight-blue'>{best_cat} ({max_val})</div></div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<div class='stat-box'><div class='stat-label'>👎 워스트</div><div class='stat-val highlight-red'>{worst_cat} ({min_val})</div></div>", unsafe_allow_html=True)

                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(r=scores, theta=categories, fill='toself', name='점수', line_color='#3182F6'))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, margin=dict(l=40, r=40, t=20, b=20), height=250)
                st.plotly_chart(fig, use_container_width=True)
                
                menu_tip = str(data.get('menu_tip', '정보 없음')).replace('\n', '<br>')
                atmos = str(data.get('atmosphere', '정보 없음')).replace('\n', '<br>')
                verdict = str(data.get('verdict', '정보 없음'))

                st.markdown(f"""
                <div class='detail-card'><div class='detail-title'>🍖 행님의 꿀조합 & 메뉴 추천</div><div class='detail-content'>{menu_tip}</div></div>
                <div class='detail-card'><div class='detail-title'>🏠 분위기 & 웨이팅 팩트체크</div><div class='detail-content'>{atmos}</div></div>
                <div class='detail-card'><div class='detail-title'>⚖️ 최종 판결</div><div class='detail-content' style='font-weight:700; color:#3182F6;'>{verdict}</div></div>
                """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # [공유 기능] - 동행인 컨텍스트 포함
                copy_text = f"[{st.session_state.restaurant}] 맛집 장담 몬한다 분석 ({companion_key}이랑 기준)\n종합점수: {total_score}점\n한줄평: {data['summary']}\n\n👉 나도 분석하러 가기: {REAL_APP_URL}"
                safe_copy_text = copy_text.replace("'", "\\'")

                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1:
                    if st.button("📢 자랑하기", use_container_width=True):
                        st.session_state.show_copy = True
                with col_s2:
                    st.markdown(f"<a href='kakaotalk://' class='share-btn kakao-link' target='_blank'>🟡 카카오톡</a>", unsafe_allow_html=True)
                with col_s3:
                    st.markdown(f"<a href='instagram://' class='share-btn insta-link' target='_blank'>🟣 인스타그램</a>", unsafe_allow_html=True)
                
                # [자랑하기 버튼 눌렀을 때만 표시되는 영역]
                if st.session_state.show_copy:
                    st.markdown("<div style='margin-top: 10px; font-weight: 700; color: #3182F6;'>👇 아래 글을 복사해서 보내세요!</div>", unsafe_allow_html=True)
                    st.code(copy_text.replace("\\n", "\n"), language="text")
                    
                    # 원터치 복사 버튼 (JS)
                    components.html(f"""
                    <html>
                        <head>
                            <style>
                                @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
                                body {{ margin: 0; font-family: 'Pretendard', sans-serif; }}
                                .copy-btn {{
                                    display: block; width: 100%; padding: 16px; border-radius: 12px;
                                    text-align: center; text-decoration: none; font-weight: 700; font-size: 16px;
                                    color: white; background-color: #333D4B; border: none; cursor: pointer;
                                    box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: 0.2s;
                                }}
                                .copy-btn:hover {{ background-color: #191F28; }}
                            </style>
                        </head>
                        <body>
                            <button class="copy-btn" onclick="copyText()">📋 원터치 복사 (클릭)</button>
                            <script>
                                function copyText() {{
                                    const text = '{safe_copy_text}';
                                    navigator.clipboard.writeText(text).then(function() {{
                                        alert('복사되었습니다! 카톡창에 붙여넣기 하세요.');
                                    }}, function(err) {{
                                        alert('복사 실패. 위 텍스트 박스를 직접 복사해주세요.');
                                    }});
                                }}
                            </script>
                        </body>
                    </html>
                    """, height=60)
                
                st.markdown("---")

                # 예약/지도 버튼
                res_type = data.get('reservation', '정보 없음')
                phone = data.get('phone', '정보 없음')
                
                if "캐치테이블" in res_type:
                    st.markdown(f"<a href='https://www.google.com/search?q={st.session_state.restaurant}+캐치테이블' target='_blank' class='action-btn catch-btn'>📱 캐치테이블로 줄서기</a>", unsafe_allow_html=True)
                elif "테이블링" in res_type:
                    st.markdown(f"<a href='https://www.google.com/search?q={st.session_state.restaurant}+테이블링' target='_blank' class='action-btn tabling-btn'>📱 테이블링으로 줄서기</a>", unsafe_allow_html=True)
                else:
                    if phone != "정보 없음":
                        st.markdown(f"<div class='action-btn call-btn'>📞 가게 문의: {phone}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='action-btn call-btn'>🏃‍♂️ 현장 웨이팅 필수</div>", unsafe_allow_html=True)
                
                st.markdown(f"<a href='https://map.naver.com/v5/search/{st.session_state.restaurant}' target='_blank' class='action-btn naver-btn'>📍 네이버 지도로 위치 확인</a>", unsafe_allow_html=True)
            
            except Exception as analysis_err:
                st.markdown(f"<div class='error-box'>⚠️ <b>분석 중 오류 발생</b><br>{str(analysis_err)[:80]}<br>다시 시도해주세요.</div>", unsafe_allow_html=True)
                if st.button("🔄 다시 분석"):
                    st.rerun()
    
    except Exception as e:
        st.markdown(f"<div class='error-box'>⚠️ <b>예상치 못한 오류</b><br>{str(e)[:80]}<br>개발자에게 연락해주세요.</div>", unsafe_allow_html=True)
        if st.button("🔄 처음으로"):
            st.session_state.step = 0
            st.rerun()