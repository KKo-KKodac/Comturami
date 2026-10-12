import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime

st.set_page_config(page_title="컴뚜라미 컴퓨터 매입계산기", layout="wide", page_icon="💾")

st.markdown("""
    <style>
    div[data-baseweb="select"], div[data-baseweb="input"], .stTextInput input, .stSelectbox div[role="button"] {
        height: 48px !important; min-height: 48px !important;
        display: flex !important; align-items: center !important;
    }
    div[data-baseweb="select"] > div { padding: 0 !important; display: flex !important; align-items: center !important; }
    
    .table-header {
        display: flex; background-color: #4A90E2; color: white; 
        padding: 12px 0; font-weight: bold; border-radius: 4px; text-align: center; margin-bottom: 8px;
    }
    .header-item { flex: 1; border-right: 1px solid rgba(255,255,255,0.3); }
    .header-item:last-child { border-right: none; }

    .cell-center { 
        text-align: center; display: flex; align-items: center; justify-content: center; 
        height: 48px; border-right: 1px solid #f0f2f6; 
    }
    .cell-left { 
        display: flex; align-items: center; padding-left: 10px; 
        height: 48px; border-right: 1px solid #f0f2f6; 
    }

    div.stButton > button[key^="add_"] {
        width: 38px !important; min-width: 38px !important; height: 38px !important; 
        border-radius: 50% !important; margin: 0 auto !important; display: flex !important;
        align-items: center !important; justify-content: center !important;
    }
    
    .price-text { color: red; font-weight: bold; font-size: 16px; margin: 0; }
    .truncate-text { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; max-width: 100%; }

    /* 상담 배너 스타일 */
    .consult-banner {
        background: linear-gradient(135deg, #FFE812 0%, #FEE500 100%);
        color: #3C1E1E;
        padding: 16px 20px;
        border-radius: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 15px 0;
        box-shadow: 0 4px 10px rgba(0,0,0,0.06);
    }
    .consult-btn {
        background-color: #3C1E1E;
        color: #FFE812 !important;
        font-weight: 700;
        padding: 10px 22px;
        border-radius: 24px;
        text-decoration: none;
        display: inline-block;
        font-size: 15px;
    }
    .consult-btn:hover {
        background-color: #241111;
    }

    /* 쿠팡 파트너스 배너 카드 스타일 */
    .coupang-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 16px;
        margin-top: 25px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        color: #333333;
    }
    .coupang-item {
        background: #f9fafb;
        border: 1px solid #edf2f7;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
        transition: 0.2s ease-in-out;
    }
    .coupang-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
    }
    .coupang-link {
        display: inline-block;
        background-color: #0073E9;
        color: #ffffff !important;
        padding: 6px 14px;
        border-radius: 6px;
        text-decoration: none;
        font-size: 13px;
        font-weight: 600;
        margin-top: 8px;
    }
    .ad-notice {
        font-size: 11px;
        color: #888888;
        margin-top: 10px;
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

# ----------------- 링크 설정 (원하시는 실제 주소로 변경하세요) -----------------
KAKAO_CHAT_URL = "http://pf.kakao.com/_AxcDFX/chat"        # 본인의 카카오톡 채널 또는 오픈채팅방 링크
#COUPANG_LINK_1 = "https://link.coupang.com/"       # 쿠팡 파트너스 링크 1 (예: 택배 안전 뽁뽁이/에어캡)
#COUPANG_LINK_2 = "https://link.coupang.com/"       # 쿠팡 파트너스 링크 2 (예: 고성능 써멀구리스)
#COUPANG_LINK_3 = "https://link.coupang.com/"       # 쿠팡 파트너스 링크 3 (예: 정전기 방지 포장재)
# -------------------------------------------------------------------------

labels = ["CPU", "메인보드", "메모리", "SSD", "HDD", "그래픽카드"]
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
    st.session_state['target_idx'] = (idx + 1) % 6

def reset_callback():
    for i in range(6):
        st.session_state[f"nm_{i}"] = ""
        st.session_state[f"qty_{i}"] = 1
        st.session_state[f"pr_{i}"] = 0
    st.session_state['target_idx'] = 0

@st.cache_data(ttl=3600)
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

    # CSV 파일이 없을 경우 기본 백업 수집
    URLS = [
        "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=10&ctgry_no2=966&ctgry_no3=4220",
        "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=10&ctgry_no2=966&ctgry_no3=967",
        "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=8&ctgry_no2=9&ctgry_no3=4083",
        "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=14&ctgry_no2=58&ctgry_no3=3784"
    ]
    all_rows = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for u in URLS:
        try:
            res = requests.get(u, headers=headers, timeout=5)
            soup = BeautifulSoup(res.text, "html.parser")
            for row in soup.select("tr"):
                c = row.find("td", class_="price_table_ctgry_nm")
                n = row.find("td", class_="price_table_prduct_nm")
                p = row.find("td", class_="price_table_prduct_pc")
                if c and n and p:
                    p_num = int(re.sub(r'[^0-9]', '', p.text))
                    if p_num > 0:
                        all_rows.append({"분류": c.text.strip(), "상품명": n.text.strip(), "매입가": p_num})
        except Exception:
            continue
    if all_rows:
        return pd.DataFrame(all_rows), "실시간 임시 로드"
    return pd.DataFrame(columns=["분류", "상품명", "매입가"]), "데이터 없음"

st.title("컴뚜라미 컴퓨터 매입계산기🖥️")

# 1. 카카오톡 실시간 상담 배너
st.markdown(f"""
    <div class="consult-banner">
        <div>
            <div style="font-size: 18px; font-weight: 800; margin-bottom: 4px;">💬 대량 매입 / 단품 시세 문의 & 접수</div>
            <div style="font-size: 13px; opacity: 0.85;">당일 검수 후 즉시 입금해 드립니다!</div>
        </div>
        <div>
            <a href="{KAKAO_CHAT_URL}" target="_blank" class="consult-btn">카톡 상담하기 ➜</a>
        </div>
    </div>
""", unsafe_allow_html=True)

df, last_updated = load_price_data()

if not df.empty:
    st.success(f"⚡ 시세 데이터 준비 완료 (기준: {last_updated})")
else:
    st.warning("⚠️ 시세 데이터를 불러오는 중입니다. 잠시 후 새로고침해 주세요.")

st.divider()

if not df.empty:
    c_cat, c_search = st.columns([1, 2.5])
    with c_cat:
        cat = st.selectbox("분류", ["전체보기"] + sorted(df["분류"].dropna().unique().tolist()), label_visibility="collapsed")
    with c_search:
        query = st.text_input("검색", placeholder="상품명 입력 (예: 4070, i5, DDR5)", label_visibility="collapsed")

    f_df = df.copy()
    if cat != "전체보기":
        f_df = f_df[f_df["분류"] == cat]
    if query:
        f_df = f_df[f_df["상품명"].astype(str).str.contains(query, case=False, na=False)]

    st.markdown("""
        <div class="table-header">
            <div class="header-item" style="flex:1;">분류</div>
            <div class="header-item" style="flex:2.5;">상품명</div>
            <div class="header-item" style="flex:1.5;">금액</div>
            <div class="header-item" style="flex:0.8; border-right:none;">담기</div>
        </div>
        """, unsafe_allow_html=True)

    with st.container(height=380):
        for i, row in f_df.iterrows():
            cols = st.columns([1, 2.5, 1.5, 0.8])
            cols[0].markdown(f'<div class="cell-center">{row["분류"]}</div>', unsafe_allow_html=True)
            cols[1].markdown(f'<div class="cell-left"><span class="truncate-text">{row["상품명"]}</span></div>', unsafe_allow_html=True)
            cols[2].markdown(f'<div class="cell-center price-text">{int(row["매입가"]):,}</div>', unsafe_allow_html=True)
            with cols[3]:
                st.button("➕", key=f"add_{i}", on_click=add_item_callback, args=(row['상품명'], int(row['매입가'])))

st.divider()

st.subheader("🛒 매입 계산 리스트")
st.radio("항목 선택:", range(6), format_func=lambda x: labels[x], key="target_idx", horizontal=True)

# 모델명 / 단가 / 수량 / 합계금액 헤더
st.markdown("""
    <div style="display: flex; background-color: #2c3e50; color: white; padding: 8px 0; font-weight: bold; border-radius: 4px; text-align: center; margin-bottom: 12px;">
        <div style="flex: 3;">모델명</div>
        <div style="flex: 1.2;">단가(원)</div>
        <div style="flex: 0.9;">수량</div>
        <div style="flex: 1.4;">합계금액(원)</div>
    </div>
""", unsafe_allow_html=True)

total_sum = 0
for i in range(6):
    st.write(f"**{labels[i]}**")
    c1, c2, c3, c4 = st.columns([3, 1.2, 0.9, 1.4])
    
    with c1:
        st.text_input(f"모델명_{i}", key=f"nm_{i}", label_visibility="collapsed")
    with c2:
        st.number_input(f"단가_{i}", step=1000, key=f"pr_{i}", label_visibility="collapsed")
    with c3:
        st.number_input(f"수량_{i}", min_value=1, value=st.session_state[f"qty_{i}"], step=1, key=f"qty_{i}", label_visibility="collapsed")
    
    item_total = st.session_state[f"pr_{i}"] * st.session_state[f"qty_{i}"]
    total_sum += item_total
    
    with c4:
        st.markdown(
            f'<div class="cell-center" style="font-size: 16px; font-weight: bold; color: #ff4b4b; background-color: rgba(255, 75, 75, 0.08); border-radius: 6px;">'
            f'{item_total:,}원</div>',
            unsafe_allow_html=True
        )

st.markdown(f"### 💰 최종 합계: :red[{total_sum:,}원]")

b_col1, b_col2, _ = st.columns([1.5, 1.5, 2.5])
with b_col1:
    st.button("🗑️ 전체 초기화", use_container_width=True, on_click=reset_callback)
with b_col2:
    res_df = pd.DataFrame({
        "항목": labels, 
        "모델": [st.session_state[f"nm_{k}"] for k in range(6)],
        "수량": [st.session_state[f"qty_{k}"] for k in range(6)],
        "단가": [st.session_state[f"pr_{k}"] for k in range(6)],
        "합계": [st.session_state[f"pr_{k}"] * st.session_state[f"qty_{k}"] for k in range(6)]
    })
    st.download_button("💾 CSV 저장", data=res_df.to_csv(index=False).encode('utf-8-sig'), file_name="purchase_list.csv", use_container_width=True)

# 2. 쿠팡 파트너스 추천 & 택배 포장재 배너 (하단)
st.markdown(f"""
    <div class="coupang-card">
        <div style="font-size: 15px; font-weight: bold; color: #1e293b; margin-bottom: 10px;">
            📦 PC 택배 포장 & 부품 정리에 필요한 추천 아이템
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
            <div class="coupang-item">
                <div style="font-size: 14px; font-weight: bold;">📦 에어캡 / 뽁뽁이 롤</div>
                <div style="font-size: 12px; color: #64748b; margin-top: 3px;">그래픽카드·본체 파손 방지 완충재</div>
                <a href="{COUPANG_LINK_1}" target="_blank" class="coupang-link">쿠팡 최저가 보기</a>
            </div>
            <div class="coupang-item">
                <div style="font-size: 14px; font-weight: bold;">🧪 가성비 써멀구리스</div>
                <div style="font-size: 12px; color: #64748b; margin-top: 3px;">CPU/쿨러 재조립 필수용품</div>
                <a href="{COUPANG_LINK_2}" target="_blank" class="coupang-link">쿠팡 최저가 보기</a>
            </div>
            <div class="coupang-item">
                <div style="font-size: 14px; font-weight: bold;">⚡ 정전기 방지 봉투 (ESD)</div>
                <div style="font-size: 12px; color: #64748b; margin-top: 3px;">RAM / SSD / 그래픽카드 안전 보관</div>
                <a href="{COUPANG_LINK_3}" target="_blank" class="coupang-link">쿠팡 최저가 보기</a>
            </div>
        </div>
        <div class="ad-notice">
            ※ 이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.
        </div>
    </div>
""", unsafe_allow_html=True)
