import streamlit as st
import google.generativeai as genai

# 1. 페이지 설정
st.set_page_config(page_title="맛집 장담 몬한다", page_icon="🍜")

# 2. 사이드바
with st.sidebar:
    st.title("🔧 주인님 설정")
    api_key = st.text_input("구글 API 키 입력", type="password")
    
    # [핵심 기능] 사용 가능한 모델 목록 확인하기
    if api_key:
        genai.configure(api_key=api_key)
        try:
            st.write("📋 사용 가능 모델 목록:")
            valid_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    valid_models.append(m.name)
                    st.caption(f"- {m.name}")
        except:
            st.error("키가 이상하다. 다시 확인해라.")
            valid_models = []

# 3. 메인 화면
st.title("🍜 맛집 장담 몬한다")
st.write("부산대 앞이든 광안리든 가게 이름만 대라.")

# 4. 입력창
restaurant_name = st.text_input("식당 이름 (예: 부산대 톤쇼우)")

# 5. 실행 로직
if st.button("판독 시작 🔍"):
    if not api_key:
        st.error("키부터 넣어라!")
    elif not restaurant_name:
        st.warning("가게 이름 넣어라!")
    else:
        if not valid_models:
            st.error("사용 가능한 모델을 못 찾겠다. API 키가 무료 버전인지 확인해라.")
        else:
            # [수정] 목록에서 'flash'가 들어간 놈을 우선 찾고, 없으면 첫 번째 놈을 쓴다.
            # 주인님 컴퓨터에서 되는 놈을 무조건 잡는 로직
            selected_model = valid_models[0] # 기본값: 첫 번째 놈
            for m in valid_models:
                if "flash" in m:
                    selected_model = m
                    break
            
            st.info(f"🤖 현재 '{selected_model}' 모델로 분석 중이다...")

            try:
                model = genai.GenerativeModel(selected_model)
                
                prompt = f"""
                너는 부산 사투리를 쓰는 까칠한 맛집 판독관이다.
                사용자가 '{restaurant_name}'에 대해 물었다.
                이 식당이 바이럴 마케팅인지 진짜 맛집인지 분석해서 
                1. 한 줄 요약 (반말, 사투리)
                2. 신뢰도 등급
                3. 팩트 체크
                4. 팁
                형식으로 답변해라.
                """
                
                with st.spinner('분석 중이다...'):
                    response = model.generate_content(prompt)
                    st.success("판독 끝났다.")
                    st.markdown(response.text)
            except Exception as e:
                st.error(f"에러 났다: {e}")