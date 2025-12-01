import streamlit as st
import google.generativeai as genai
import plotly.graph_objects as go
import json
import os

# 1. 페이지 설정
st.set_page_config(page_title="맛집 장담 몬한다", page_icon="🚫", layout="centered")

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
    .detail-card { background-color: #ffffff; border: 1px solid #E5E8EB; border-radius: 16px; padding: 20px; margin-top: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.03); }
    .detail-title { font-size: 18px; font-weight: 700; color: #191F28; margin-bottom: 10px; display: flex; align-items: center; }
    .detail-content { font-size: 16px; line-height: 1.7; color: #333D4B; }
    
    .action-btn { display: block; width: 100%; padding: 16px; text-align: center; text-decoration: none; border-radius: 12px; font-weight: 700; font-size: 16px; margin-top: 10px; }
    .catch-btn { background-color: #FF3B30; color: white; }
    .tabling-btn { background-color: #FF2D55; color: white; }
    .call-btn { background-color: #333D4B; color: white; }
    .naver-btn { background-color: #03C75A; color: white; }
    
    /* 후원 버튼 스타일 */
    .donate-btn {
        background: linear-gradient(90deg, #FFD700 0%, #FFA500 100%);
        color: #333D4B;
    }
    
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
    """, unsafe_allow_html=True)

# 3. 상태 관리
if 'step' not in st.session_state: st.session_state.step = 0
if 'persona' not in st.session_state: st.session_state.persona = ""
if 'companion' not in st.session_state: st.session_state.companion = ""
if 'restaurant' not in st.session_state: st.session_state.restaurant = ""

# 4. API 키 로드
api_key = None
if "GOOGLE_API_KEY" in st.secrets: api_key = st.secrets["GOOGLE_API_KEY"]

# 5. [핵심] 캐싱 함수 (돈 아끼는 기능)
# @st.cache_data 데코레이터를 쓰면, 똑같은 질문에는 AI를 안 부르고 저장된 답을 줍니다.
@st.cache_data(show_spinner=False)
def analyze_restaurant(_model, restaurant, companion, persona):
    
    # 성격 설정
    persona_inst = ""
    if "착한" in persona: persona_inst = "너는 '착한 부산 행님'이다. 친절한 사투리 사용. 내용은 구체적으로."
    elif "지옥" in persona: persona_inst = "너는 '지옥의 독설가'다. 거친 부산 사투리 사용. 내용은 아주 구체적으로."
    else: persona_inst = "너는 '친근한 동네 형'이다. 수다스러운 TMI 스타일. 부산 사투리 사용."

    companion_key = companion.split(' ')[1]
    
    prompt = f"""
    {persona_inst}
    식당: {restaurant}, 동행: {companion_key}
    [규칙] 
    1. 메뉴 팩트체크 필수. 
    2. 점수는 100점 만점 기준.
    JSON 포맷: {{ "scores": [맛,가성비,서비스,위생,분위기], "summary": "한줄평", "hours": "시간", "reservation": "예약", "phone": "번호", "menu_tip": "꿀조합", "atmosphere": "분위기", "verdict": "결론" }}
    """
    response = _model.generate_content(prompt)
    return response.text

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
    if st.button("← 뒤로"): st.session_state.step = 0; st.rerun()
    st.markdown("<div class='step-title'>어떤 행님한테 물어볼래?</div>", unsafe_allow_html=True)
    persona_choice = st.radio("말투", ["😇 착한 부산햄 (순한맛/칭찬봇)", "😎 친근한 부산햄 (중간맛/팩트/츤데레)", "🤬 지옥의 부산햄 (매운맛/독설/고든램지) ⚠️주의"], label_visibility="collapsed")
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    if st.button("다음"):
        st.session_state.persona = persona_choice
        st.session_state.step = 2
        st.rerun()

# ==================== STEP 2: 동행인 선택 ====================
elif st.session_state.step == 2:
    if st.button("← 뒤로"): st.session_state.step = 1; st.rerun()
    st.markdown("<div class='step-title'>누구랑 같이 가나요?</div>", unsafe_allow_html=True)
    companion_choice = st.radio("동행인", ["❤️ 연인 (분위기/웨이팅)", "😎 친구 (맛/가성비)", "👨‍👩‍👧‍👦 가족 (주차/아이들)", "💼 직장동료 (법카/눈치)"], label_visibility="collapsed")
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    if st.button("다음"):
        st.session_state.companion = companion_choice
        st.session_state.step = 3
        st.rerun()

# ==================== STEP 3: 식당 입력 ====================
elif st.session_state.step == 3:
    if st.button("← 뒤로"): st.session_state.step = 2; st.rerun()
    if "착한" in st.session_state.persona: q_text = "어떤 맛집이 궁금한데? 내한테 말해봐라."
    elif "지옥" in st.session_state.persona: q_text = "어디 가서 돈 낭비하려고? 이름 대."
    else: q_text = "어떤 식당이 궁금하노?"
    st.markdown(f"<div class='step-title'>{q_text}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='step-sub'><b>{st.session_state.companion.split(' ')[1]}</b>랑 가는군요.</div>", unsafe_allow_html=True)
    name_input = st.text_input("식당 이름", value=st.session_state.restaurant, placeholder="예: 부산대 톤쇼우", label_visibility="collapsed")
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    if st.button("분석 시작 🚀"):
        if not name_input: st.warning("식당 이름을 입력해주세요.")
        else:
            st.session_state.restaurant = name_input
            st.session_state.step = 4
            st.rerun()

# ==================== STEP 4: 결과 화면 ====================
elif st.session_state.step == 4:
    col_nav1, col_nav2 = st.columns([1, 1])
    with col_nav1:
        if st.button("← 다른 식당"): st.session_state.step = 3; st.rerun()
    with col_nav2:
        if st.button("🔄 처음으로"): st.session_state.step = 0; st.session_state.restaurant = ""; st.rerun()

    if not api_key: st.error("⚠️ API 키가 없습니다."); st.stop()
    
    try:
        genai.configure(api_key=api_key)
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        safe_models = [m for m in all_models if "exp" not in m]
        target_model = next((m for m in safe_models if "flash" in m), safe_models[0] if safe_models else None)
        if not target_model: st.error("모델 없음"); st.stop()
        model = genai.GenerativeModel(target_model)

        with st.spinner('AI 행님이 점수 계산기 두드리는 중...'):
            # [수정] 캐싱된 함수 호출
            result_text = analyze_restaurant(model, st.session_state.restaurant, st.session_state.companion, st.session_state.persona)
            
            # JSON 파싱
            data = None
            try:
                clean_text = result_text.replace("```json", "").replace("```", "").strip()
                if "{" in clean_text:
                    clean_text = clean_text[clean_text.find("{"):clean_text.rfind("}")+1]
                    data = json.loads(clean_text)
                else: raise Exception("JSON 아님")
            except:
                data = { "scores": [50,50,50,50,50], "summary": "분석 실패. 다시 시도해주이소.", "hours":"정보없음", "reservation":"", "phone":"", "menu_tip":"오류발생", "atmosphere":"", "verdict":"" }

            # 점수 변환
            raw_scores = data.get("scores", [50, 50, 50, 50, 50])
            if sum(raw_scores) / 5 <= 10: scores = [int(s * 20) for s in raw_scores]
            else: scores = [int(s) for s in raw_scores]

            categories = ['맛', '가성비', '서비스', '위생', '분위기']
            total_score = int(sum(scores) / 5)
            max_val = max(scores); min_val = min(scores)
            best_cat = categories[scores.index(max_val)]
            worst_cat = categories[scores.index(min_val)]
            
            # --- 결과 출력 ---
            companion_key = st.session_state.companion.split(' ')[1]
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: center; color: #8B95A1; font-weight: 600;'>{companion_key}랑 갈 때 점수</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='total-score-val'>{total_score}점</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='summary-box'>🗣️ {data['summary']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='time-box'>⏰ <b>영업시간</b><br>{data['hours']}</div>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1: st.markdown(f"<div class='stat-box'><div class='stat-label'>👍 베스트</div><div class='stat-val highlight-blue'>{best_cat} ({max_val})</div></div>", unsafe_allow_html=True)
            with col2: st.markdown(f"<div class='stat-box'><div class='stat-label'>👎 워스트</div><div class='stat-val highlight-red'>{worst_cat} ({min_val})</div></div>", unsafe_allow_html=True)

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=scores, theta=categories, fill='toself', name='점수', line_color='#3182F6'))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, margin=dict(l=40, r=40, t=20, b=20), height=250)
            st.plotly_chart(fig, use_container_width=True)
            
            menu_tip = str(data.get('menu_tip', '')).replace('\n', '<br>')
            atmos = str(data.get('atmosphere', '')).replace('\n', '<br>')
            verdict = str(data.get('verdict', ''))

            st.markdown(f"""
            <div class='detail-card'><div class='detail-title'>🍖 행님의 꿀조합 & 메뉴 추천</div><div class='detail-content'>{menu_tip}</div></div>
            <div class='detail-card'><div class='detail-title'>🏠 분위기 & 웨이팅 팩트체크</div><div class='detail-content'>{atmos}</div></div>
            <div class='detail-card'><div class='detail-title'>⚖️ 최종 판결</div><div class='detail-content' style='font-weight:700; color:#3182F6;'>{verdict}</div></div>
            """, unsafe_allow_html=True)
            
            # [돈 벌기] 복사하기 & 후원하기 버튼
            st.markdown("---")
            copy_text = f"[{st.session_state.restaurant}] 맛집 장담 몬한다 분석 결과\n종합점수: {total_score}점\n한줄평: {data['summary']}\n\n👉 나도 분석하러 가기: https://share.streamlit.io"
            st.code(copy_text, language="text")
            st.caption("👆 위 내용을 복사해서 친구한테 보내주이소.")
            
            # [후원 버튼] - 본인의 토스 익명 송금 주소나 카카오페이 코드를 넣으세요
            st.markdown(f"""
            <a href='https://toss.me/주인님아이디' target='_blank' class='action-btn donate-btn'>
                ☕ 개발자 행님 커피 한 잔 사주기
            </a>
            """, unsafe_allow_html=True)

            # 예약/지도 버튼
            res_type = data.get('reservation', '')
            phone = data.get('phone', '정보없음')
            if "캐치테이블" in res_type: st.markdown(f"<a href='https://www.google.com/search?q={st.session_state.restaurant}+캐치테이블' target='_blank' class='action-btn catch-btn'>📱 캐치테이블로 줄서기</a>", unsafe_allow_html=True)
            elif "테이블링" in res_type: st.markdown(f"<a href='https://www.google.com/search?q={st.session_state.restaurant}+테이블링' target='_blank' class='action-btn tabling-btn'>📱 테이블링으로 줄서기</a>", unsafe_allow_html=True)
            else:
                if phone != "정보없음": st.markdown(f"<div class='action-btn call-btn'>📞 가게 문의: {phone}</div>", unsafe_allow_html=True)
                else: st.markdown(f"<div class='action-btn call-btn'>🏃‍♂️ 현장 웨이팅 필수</div>", unsafe_allow_html=True)
            st.markdown(f"<a href='https://map.naver.com/v5/search/{st.session_state.restaurant}' target='_blank' class='action-btn naver-btn'>📍 네이버 지도로 위치 확인</a>", unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"오류: {e}")
        if st.button("다시 시도"): st.rerun()