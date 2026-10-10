import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime

st.set_page_config(page_title="꼬꼬닥'S 컴퓨터 매입계산기", layout="wide")

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
    </style>
    """, unsafe_allow_html=True)

labels = ["CPU", "메인보드", "메모리", "SSD", "HDD", "그래픽카드"]
if 'target_idx' not in st.session_state: 
    st.session_state['target_idx'] = 0

for i in range(6):
    if f"nm_{i}" not in st.session_state: 
        st.session_state[f"nm_{i}"] = ""
    if f"pr_{i}" not in st.session_state: 
        st.session_state[f"pr_{i}"] = 0

def add_item_callback(name, price):
    idx = st.session_state['target_idx']
    st.session_state[f"nm_{idx}"] = name
    st.session_state[f"pr_{idx}"] = price
    st.session_state['target_idx'] = (idx + 1) % 6

def reset_callback():
    for i in range(6):
        st.session_state[f"nm_{i}"], st.session_state[f"pr_{i}"] = "", 0
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

    # 만약 CSV 파일이 아직 없을 경우 기본 URL 백업 수집
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

st.title("🐔꼬꼬닥'S 컴퓨터 매입계산기🖥️")

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

total_sum = 0
for i in range(6):
    st.write(f"**{labels[i]}**")
    c1, c2 = st.columns([3, 1])
    with c1:
        st.text_input(f"모델명_{i}", key=f"nm_{i}", label_visibility="collapsed")
    with c2:
        st.number_input(f"금액_{i}", step=1000, key=f"pr_{i}", label_visibility="collapsed")
    total_sum += st.session_state[f"pr_{i}"]

st.markdown(f"### 💰 최종 합계: :red[{total_sum:,}원]")

b_col1, b_col2, _ = st.columns([1.5, 1.5, 2.5])
with b_col1:
    st.button("🗑️ 전체 초기화", use_container_width=True, on_click=reset_callback)
with b_col2:
    res_df = pd.DataFrame({
        "항목": labels, 
        "모델": [st.session_state[f"nm_{k}"] for k in range(6)], 
        "금액": [st.session_state[f"pr_{k}"] for k in range(6)]
    })
    st.download_button("💾 CSV 저장", data=res_df.to_csv(index=False).encode('utf-8-sig'), file_name="purchase_list.csv", use_container_width=True)
