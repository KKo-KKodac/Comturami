import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="컴뚜라미 컴퓨터 매입계산기", layout="wide", page_icon="💾")

# ----------------- 링크 및 기본 설정 -----------------
KAKAO_CHAT_URL = "http://pf.kakao.com/_AxcDFX/chat"
labels = ["CPU", "메인보드", "메모리", "SSD", "HDD", "그래픽카드"]

# ----------------- 최상단 메인 이미지 노출 -----------------
IMAGE_FILES = [
    "메인이미지.png"
]

banner_shown = False
for img_path in IMAGE_FILES:
    if os.path.exists(img_path):
        st.image(img_path, use_container_width=True)
        banner_shown = True
        break

if not banner_shown:
    st.title("컴뚜라미 컴퓨터 매입계산기 🖥️")

# ----------------- 스타일 정의 -----------------
st.markdown("""
    <style>
    div[data-baseweb="select"], div[data-baseweb="input"], .stTextInput input, .stSelectbox div[role="button"] {
        height: 44px !important; min-height: 44px !important;
        display: flex !important; align-items: center !important;
    }
    div[data-baseweb="select"] > div { padding: 0 !important; display: flex !important; align-items: center !important; }
    
    .table-header {
        display: flex; background-color: #1e3a29; color: white; 
        padding: 10px 0; font-weight: bold; border-radius: 6px; text-align: center; margin-bottom: 6px; font-size: 14px;
    }
    .header-item { flex: 1; border-right: 1px solid rgba(255,255,255,0.2); }
    .header-item:last-child { border-right: none; }

    .cell-center { 
        text-align: center; display: flex; align-items: center; justify-content: center; 
        height: 44px; border-right: 1px solid #2d3748; font-size: 14px;
    }
    .cell-left { 
        display: flex; align-items: center; padding-left: 10px; 
        height: 44px; border-right: 1px solid #2d3748; font-size: 14px;
    }

    div.stButton > button[key^="add_"] {
        width: 34px !important; min-width: 34px !important; height: 34px !important; 
        border-radius: 50% !important; margin: 0 auto !important; display: flex !important;
        align-items: center !important; justify-content: center !important;
    }
    
    .price-text { color: #ff5252; font-weight: 700; font-size: 15px; margin: 0; }
    .truncate-text { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; max-width: 100%; }

    /* 상담 배너 스타일 */
    .consult-banner {
        background: linear-gradient(135deg, #FFE812 0%, #FEE500 100%);
        color: #3C1E1E;
        padding: 14px 20px;
        border-radius: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 12px 0 18px 0;
        box-shadow: 0 3px 8px rgba(0,0,0,0.06);
    }
    .consult-btn {
        background-color: #3C1E1E;
        color: #FFE812 !important;
        font-weight: 700;
        padding: 8px 18px;
        border-radius: 20px;
        text-decoration: none;
        display: inline-block;
        font-size: 14px;
    }
    .consult-btn:hover {
        background-color: #241111;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- Session State 초기화 -----------------
if 'target_idx' not in st.session_state: 
    st.session_state['target_idx'] = 0

for i in range(6):
    if f"nm_{i}" not in st.session_state: 
        st.session_state[f"nm_{i}"] = ""
    if f"qty_{i}" not in st.session_state: 
        st.session_state[f"qty_{i}"] = 1
    if f"pr_{i}" not in st.session_state: 
        st.session_state[f"pr_{i}"] = 0

def add_item_callback(name, price):
    idx = st.session_state['target_idx']
    st.session_state[f"nm_{idx}"] = name
    st.session_state[f"pr_{idx}"] = price
    st.session_state[f"qty_{idx}"] = 1
    # 담은 후 다음 품목으로 자동 이동
    st.session_state['target_idx'] = (idx + 1) % 6

def reset_callback():
    for i in range(6):
        st.session_state[f"nm_{i}"] = ""
        st.session_state[f"qty_{i}"] = 1
        st.session_state[f"pr_{i}"] = 0
    st.session_state['target_idx'] = 0

# ----------------- 로컬 CSV 데이터 로딩 -----------------
@st.cache_data
def load_price_data():
    file_path = "price_data.csv"
    if os.path.exists(file_path):
        mtime = os.path.getmtime(file_path)
        last_updated = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        try:
            df = pd.read_csv(file_path, encoding="utf-8-sig")
            return df, last_updated
        except Exception:
            pass
    return pd.DataFrame(columns=["분류", "상품명", "매입가"]), "데이터 없음"

# ----------------- UI 렌더링 -----------------

# 1. 카카오톡 상담 배너
st.markdown(f"""
    <div class="consult-banner">
        <div>
            <div style="font-size: 17px; font-weight: 800; margin-bottom: 2px;">💬 대량 매입 / 단품 시세 문의 & 접수</div>
            <div style="font-size: 13px; opacity: 0.85;">당일 검수! 즉시 입금해 드립니다.</div>
        </div>
        <div>
            <a href="{KAKAO_CHAT_URL}" target="_blank" class="consult-btn">카톡 상담하기 ➜</a>
        </div>
    </div>
""", unsafe_allow_html=True)

df, last_updated = load_price_data()

if not df.empty:
    st.caption(f"⚡ 시세 데이터 기준: {last_updated}")
else:
    st.warning("⚠️ 시세 데이터(price_data.csv)가 없습니다. 크롤러 실행 후 새로고침해 주세요.")

# 2. 검색 및 시세 리스트
if not df.empty:
    c_cat, c_search = st.columns([1, 2.5])
    with c_cat:
        cat = st.selectbox("분류", ["전체보기"] + sorted(df["분류"].dropna().unique().tolist()), label_visibility="collapsed")
    with c_search:
        query = st.text_input("검색", placeholder="상품명 검색 (예: 4070, i5, DDR5)", label_visibility="collapsed")

    f_df = df.copy()
    if cat != "전체보기":
        f_df = f_df[f_df["분류"] == cat]
    if query:
        f_df = f_df[f_df["상품명"].astype(str).str.contains(query, case=False, na=False)]

    total_count = len(f_df)
    
    st.markdown("""
        <div class="table-header">
            <div class="header-item" style="flex:1;">분류</div>
            <div class="header-item" style="flex:2.5;">상품명</div>
            <div class="header-item" style="flex:1.5;">금액</div>
            <div class="header-item" style="flex:0.8; border-right:none;">담기</div>
        </div>
    """, unsafe_allow_html=True)

    # 렌더링 과부하 방지: 최대 30개만 표시
    display_df = f_df.head(30)
    with st.container(height=340):
        for i, row in display_df.iterrows():
            cols = st.columns([1, 2.5, 1.5, 0.8])
            cols[0].markdown(f'<div class="cell-center">{row["분류"]}</div>', unsafe_allow_html=True)
            cols[1].markdown(f'<div class="cell-left"><span class="truncate-text">{row["상품명"]}</span></div>', unsafe_allow_html=True)
            cols[2].markdown(f'<div class="cell-center price-text">{int(row["매입가"]):,}원</div>', unsafe_allow_html=True)
            with cols[3]:
                st.button("➕", key=f"add_{i}", on_click=add_item_callback, args=(row['상품명'], int(row['매입가'])))

    if total_count > 30:
        st.caption(f"💡 검색 결과 {total_count}개 중 상위 30개 표시 중입니다. 더 정확한 부품명으로 검색해 보세요.")

st.divider()

# 3. 매입 계산 리스트
st.subheader("🛒 매입 계산 리스트")
st.radio("현재 담을 대상 부품:", range(6), format_func=lambda x: labels[x], key="target_idx", horizontal=True)

st.markdown("""
    <div style="display: flex; background-color: #1e3a29; color: white; padding: 8px 0; font-weight: bold; border-radius: 4px; text-align: center; margin-bottom: 12px; font-size: 13px;">
        <div style="flex: 3;">모델명</div>
        <div style="flex: 1.2;">단가(원)</div>
        <div style="flex: 0.9;">수량</div>
        <div style="flex: 1.4;">합계금액(원)</div>
    </div>
""", unsafe_allow_html=True)

total_sum = 0
for i in range(6):
    st.caption(f"**{labels[i]}**")
    c1, c2, c3, c4 = st.columns([3, 1.2, 0.9, 1.4])
    
    with c1:
        st.text_input(f"모델명_{i}", key=f"nm_{i}", label_visibility="collapsed")
    with c2:
        st.number_input(f"단가_{i}", step=1000, key=f"pr_{i}", label_visibility="collapsed")
    with c3:
        st.number_input(f"수량_{i}", min_value=1, step=1, key=f"qty_{i}", label_visibility="collapsed")
    
    item_total = st.session_state[f"pr_{i}"] * st.session_state[f"qty_{i}"]
    total_sum += item_total
    
    with c4:
        st.markdown(
            f'<div class="cell-center" style="font-size: 15px; font-weight: bold; color: #ff5252; background-color: rgba(255, 82, 82, 0.1); border-radius: 6px;">'
            f'{item_total:,}원</div>',
            unsafe_allow_html=True
        )

# --- 최종 매입 합계 금액: 표 우측 라인에 맞춰 큰 글씨로 배치 ---
tot_col1, tot_col2 = st.columns([5.1, 1.4])
with tot_col1:
    st.markdown(
        '<div style="text-align: right; font-size: 20px; font-weight: 800; padding-top: 10px; color: #ffffff;">'
        '💰 최종 매입 합계 금액</div>',
        unsafe_allow_html=True
    )
with tot_col2:
    st.markdown(
        f'<div style="text-align: center; font-size: 22px; font-weight: 900; color: #ff5252; '
        f'background-color: rgba(255, 82, 82, 0.2); border: 1.5px solid rgba(255, 82, 82, 0.5); '
        f'border-radius: 8px; padding: 6px 0; margin-top: 2px;">'
        f'{total_sum:,}원</div>',
        unsafe_allow_html=True
    )

st.write("")

# 4. 하단 버튼 영역 (CSV 다운로드 시 최종 합계 행 포함)
b_col1, b_col2, _ = st.columns([1.5, 1.5, 2.5])
with b_col1:
    st.button("🗑️ 전체 초기화", use_container_width=True, on_click=reset_callback)
with b_col2:
    # 6개 품목 데이터 아래에 '최종 매입 합계' 행을 맨 끝에 추가
    res_df = pd.DataFrame({
        "항목": labels + ["최종 매입 합계"], 
        "모델": [st.session_state[f"nm_{k}"] for k in range(6)] + [""],
        "단가": [st.session_state[f"pr_{k}"] for k in range(6)] + [""],
        "수량": [st.session_state[f"qty_{k}"] for k in range(6)] + [""],
        "합계": [st.session_state[f"pr_{k}"] * st.session_state[f"qty_{k}"] for k in range(6)] + [total_sum]
    })
    st.download_button(
        "💾 CSV 다운로드",
        data=res_df.to_csv(index=False).encode('utf-8-sig'),
        file_name="컴뚜라미_매입견적.csv",
        use_container_width=True
    )
