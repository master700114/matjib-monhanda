import streamlit as st
import google.generativeai as genai

# 1. 페이지 설정 (토스 스타일)
st.set_page_config(
    page_title="맛집 장담 몬한다",
    page_icon="💸",
    layout="centered"
)

# [디자인] 토스 스타일 CSS (파란 버튼, 깔끔함)
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1 {
        color: #191F28;
        font-family: sans-serif;
        font-weight: 700;
        padding-bottom: 10px;
    }
    div.stButton > button {
        background-color: #3182F6;
        color: white;
        border: none;
        border-radius: 12px;
        padding: 16px 20px;
        font-size: 17px;
        font-weight: 600;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #1B64DA;
        color: white;
        border: none;
    }
    .stTextInput > div > div > input {
        border-radius: 12px;
        padding: 12px;
        font-size: 16px;
        background-color: #F2F4F6;
        border: none;
        color: #333D4B;
    }
    .result-box {
        background-color: #F9FAFB;
        padding: 24px;
        border-radius: 20px;
        margin-top: 24px;
        color: #333D4B;
        line-height: 1.6;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# 2. API 키 자동 로드 (비밀 금고에서 꺼내기)
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        st.error("⚠️ '.streamlit/secrets.toml' 파일이 없거나 키가 비어있어요.")
        st.stop()
except FileNotFoundError:
    st.error("⚠️ 비밀 금고 파일(.streamlit/secrets.toml)을 못 찾겠어요.")
    st.stop()

# 3. 메인 화면
st.title("어떤 식당이\n궁금하신가요?")

restaurant_name = st.text_input(
    label="식당 이름",
    placeholder="예: 부산대 톤쇼우",
    label_visibility="collapsed"
)

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# 4. 실행 버튼 및 로직
if st.button("지금 확인하기"):
    if not restaurant_name:
        st.warning("식당 이름을 입력해주세요.")
    else:
        try:
            # AI 설정
            genai.configure(api_key=api_key)
            
            # [핵심 수정] 되는 모델 자동으로 찾기 (아까 성공한 방식)
            valid_models = []
            try:
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        valid_models.append(m.name)
            except:
                st.error("API 키가 올바르지 않아요.")
                st.stop()

            # 모델 선택 로직 (flash 우선, 없으면 아무거나)
            target_model = ""
            if valid_models:
                target_model = valid_models[0] # 일단 첫 번째 거 잡고
                for m in valid_models:
                    if "flash" in m: # flash 있으면 그걸로 교체
                        target_model = m
                        break
            else:
                st.error("사용 가능한 AI 모델이 없어요.")
                st.stop()
            
            # 분석 시작
            model = genai.GenerativeModel(target_model)
            
            prompt = f"""
            너는 부산 사투리를 쓰는 까칠한 맛집 판독관이다.
            사용자가 '{restaurant_name}'에 대해 물었다.
            토스 앱처럼 간결하고 명확하게, 하지만 말투는 부산 사투리 반말로 해라.
            
            [형식]
            ### 1. 한 줄 결론 (임팩트 있게)
            ### 2. 신뢰도: OO%
            ### 3. 상세 분석
            - 맛/분위기: 
            - 광고 여부:
            ### 4. 꿀팁
            """
            
            with st.spinner('데이터 분석하는 중...'):
                response = model.generate_content(prompt)
                
                # 결과 출력
                st.markdown(f"""
                <div class="result-box">
                    {response.text}
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"잠시 문제가 생겼어요. (에러: {e})")