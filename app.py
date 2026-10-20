import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import os
import uuid
from datetime import datetime

st.set_page_config(page_title="컴뚜라미 컴퓨터 매입계산기", layout="wide", page_icon="💾")

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
        padding: 10px 0; font-weight: bold; border-radius: 6px; text-align: center; margin-bottom: 8px; font-size: 14px;
    }
    .header-item { flex: 1; border-right: 1px solid rgba(255,255,255,0.2); }
    .header-item:last-child { border-right: none; }

    .cell-center { 
        text-align: center; display: flex; align-items: center; justify-content: center; 
        height: 44px; border-right: 1px solid #f0f2f6; font-size: 14px;
    }
    .cell-left { 
        display: flex; align-items: center; padding-left: 10px; 
        height: 44px; border-right: 1px solid #f0f2f6; font-size: 14px;
    }

    div.stButton > button[key^="add_"] {
        width: 34px !important; min-width: 34px !important; height: 34px !important; 
        border-radius: 50% !important; margin: 0 auto !important; display: flex !important;
        align-items: center !important; justify-content: center !important;
    }
    
    .price-text { color: #d93838; font-weight: 700; font-size: 15px; margin: 0; }
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

    /* 쿠팡 파트너스 배너 카드 스타일 */
    .coupang-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 16px;
        margin-top: 20px;
        color: #333333;
    }
    .coupang-item {
        background: #f9fafb;
        border: 1px solid #edf2f7;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    .coupang-link {
        display: inline-block;
        background-color: #0073E9;
        color: #ffffff !important;
        padding: 5px 12px;
        border-radius: 6px;
        text-decoration: none;
        font-size: 12px;
        font-weight: 600;
        margin-top: 8px;
    }
    .ad-notice {
        font-size: 11px;
        color: #888888;
        margin-top: 8px;
        text-align: right;
    }

    /* 쿠팡 블러 처리 스타일 */
    .coupang-blur-container {
        position: relative;
        overflow: hidden;
        border-radius: 10px;
    }
    .coupang-blur-content {
        filter: blur(4px);
        pointer-events: none;
        user-select: none;
        opacity: 0.55;
    }
    .coupang-blur-badge {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background-color: rgba(30, 41, 59, 0.9);
        color: #ffffff;
        padding: 10px 20px;
        border-radius: 25px;
        font-weight: 700;
        font-size: 13px;
        z-index: 10;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- 링크 및 기본 설정 -----------------
KAKAO_CHAT_URL = "http://pf.kakao.com/_AxcDFX/chat"
CATEGORY_OPTIONS = ["CPU", "메인보드", "메모리", "SSD", "HDD", "그래픽카드", "파워/케이스", "완본체", "기타"]

# ----------------- 1. 상단 타이틀 배너 이미지 -----------------
BANNER_IMAGE_PATH = "네이버블로그-타이틀-이미지_컴뚜라미.jpg"
if os.path.exists(BANNER_IMAGE_PATH):
    st.image(BANNER_IMAGE_PATH, use_container_width=True)
else:
    # 이미지가 로컬에 없을 때 대체 헤더
    st.title("컴뚜라미 컴퓨터 부품 전문 매입 🖥️")

# ----------------- Session State 초기화 (동적 리스트 관리) -----------------
if 'calc_items' not in st.session_state:
    # 기본 시작용 3개 기본 행
    st.session_state['calc_items'] = [
        {"id": str(uuid.uuid4())[:8], "category": "CPU", "name": "", "price": 0, "qty": 1},
        {"id": str(uuid.uuid4())[:8], "category": "그래픽카드", "name": "", "price": 0, "qty": 1},
        {"id": str(uuid.uuid4())[:8], "category": "메모리", "name": "", "price": 0, "qty": 1},
    ]

def add_empty_item():
    st.session_state['calc_items'].append({
        "id": str(uuid.uuid4())[:8],
        "category": "기타",
        "name": "",
        "price": 0,
        "qty": 1
    })

def add_price_item(category, name, price):
    # 검색 테이블에서 담기 버튼을 누를 때 호출
    cat = category if category in CATEGORY_OPTIONS else "기타"
    st.session_state['calc_items'].append({
        "id": str(uuid.uuid4())[:8],
        "category": cat,
        "name": name,
        "price": int(price),
        "qty": 1
    })
    st.toast(f"'{name}' 품목이 계산 리스트에 추가되었습니다! 🛒", icon="✅")

def remove_item(item_id):
    st.session_state['calc_items'] = [item for item in st.session_state['calc_items'] if item['id'] != item_id]

def reset_all_items():
    st.session_state['calc_items'] = []

# ----------------- 데이터 로딩 함수 -----------------
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

    # 백업 크롤링 (월드메모리 기준)
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

# ----------------- UI 렌더링 -----------------

# 카카오톡 상담 배너
st.markdown(f"""
    <div class="consult-banner">
        <div>
            <div style="font-size: 17px; font-weight: 800; margin-bottom: 2px;">💬 대량 매입 / 단품 시세 문의 & 접수</div>
            <div style="font-size: 13px; opacity: 0.85;">당일 신속 검수! 즉시 입금해 드립니다.</div>
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
    st.warning("⚠️ 시세 데이터를 불러오는 중입니다. 잠시 후 새로고침해 주세요.")

# 2. 검색 및 시세 리스트
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

    with st.container(height=340):
        for i, row in f_df.iterrows():
            cols = st.columns([1, 2.5, 1.5, 0.8])
            cols[0].markdown(f'<div class="cell-center">{row["분류"]}</div>', unsafe_allow_html=True)
            cols[1].markdown(f'<div class="cell-left"><span class="truncate-text">{row["상품명"]}</span></div>', unsafe_allow_html=True)
            cols[2].markdown(f'<div class="cell-center price-text">{int(row["매입가"]):,}원</div>', unsafe_allow_html=True)
            with cols[3]:
                st.button("➕", key=f"add_tbl_{i}", on_click=add_price_item, args=(row["분류"], row['상품명'], int(row['매입가'])))

st.divider()

# ----------------- 3. 동적 매입 계산 리스트 (추가/삭제 지원) -----------------
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.subheader("🛒 내 매입 계산 리스트")
with col_h2:
    st.button("➕ 항목 직접 추가", on_click=add_empty_item, use_container_width=True)

st.markdown("""
    <div style="display: flex; background-color: #1e3a29; color: white; padding: 8px 0; font-weight: bold; border-radius: 4px; text-align: center; margin-bottom: 12px; font-size: 13px;">
        <div style="flex: 1.2;">분류</div>
        <div style="flex: 2.8;">모델명</div>
        <div style="flex: 1.3;">단가(원)</div>
        <div style="flex: 0.8;">수량</div>
        <div style="flex: 1.4;">합계금액(원)</div>
        <div style="flex: 0.5;">삭제</div>
    </div>
""", unsafe_allow_html=True)

total_sum = 0
export_rows = []

if not st.session_state['calc_items']:
    st.info("리스트가 비어 있습니다. 상단 테이블에서 [➕] 버튼을 누르거나 [➕ 항목 직접 추가]를 눌러 품목을 추가하세요.")
else:
    for item in st.session_state['calc_items']:
        item_id = item['id']
        c_cat, c_name, c_pr, c_qty, c_subtotal, c_del = st.columns([1.2, 2.8, 1.3, 0.8, 1.4, 0.5])
        
        with c_cat:
            cat_idx = CATEGORY_OPTIONS.index(item['category']) if item['category'] in CATEGORY_OPTIONS else 0
            selected_cat = st.selectbox(
                f"분류_{item_id}",
                CATEGORY_OPTIONS,
                index=cat_idx,
                key=f"cat_w_{item_id}",
                label_visibility="collapsed"
            )
            item['category'] = selected_cat

        with c_name:
            item_name = st.text_input(
                f"품목_{item_id}",
                value=item['name'],
                key=f"nm_w_{item_id}",
                placeholder="부품 모델명 입력",
                label_visibility="collapsed"
            )
            item['name'] = item_name

        with c_pr:
            item_price = st.number_input(
                f"단가_{item_id}",
                min_value=0,
                step=1000,
                value=int(item['price']),
                key=f"pr_w_{item_id}",
                label_visibility="collapsed"
            )
            item['price'] = item_price

        with c_qty:
            item_qty = st.number_input(
                f"수량_{item_id}",
                min_value=1,
                step=1,
                value=int(item['qty']),
                key=f"qty_w_{item_id}",
                label_visibility="collapsed"
            )
            item['qty'] = item_qty

        subtotal = item['price'] * item['qty']
        total_sum += subtotal

        with c_subtotal:
            st.markdown(
                f'<div class="cell-center" style="font-size: 14px; font-weight: bold; color: #d93838; background-color: rgba(217, 56, 56, 0.08); border-radius: 6px;">'
                f'{subtotal:,}원</div>',
                unsafe_allow_html=True
            )

        with c_del:
            st.button("❌", key=f"del_{item_id}", on_click=remove_item, args=(item_id,))

        export_rows.append({
            "분류": item['category'],
            "모델명": item['name'],
            "단가": item['price'],
            "수량": item['qty'],
            "합계": subtotal
        })

# 최종 합계 표시
st.markdown(f"### 💰 최종 매입 합계: :red[{total_sum:,}원]")

# 하단 컨트롤 버튼 (초기화, CSV 다운로드)
b_col1, b_col2, _ = st.columns([1.5, 1.5, 2.5])
with b_col1:
    st.button("🗑️ 전체 목록 비우기", use_container_width=True, on_click=reset_all_items)
with b_col2:
    res_df = pd.DataFrame(export_rows)
    st.download_button(
        "💾 견적서 CSV 다운로드",
        data=res_df.to_csv(index=False).encode('utf-8-sig'),
        file_name="컴뚜라미_매입견적서.csv",
        use_container_width=True
    )

# ----------------- 4. 하단 제휴 배너 (준비 중 블러) -----------------
st.markdown(f"""
    <div class="coupang-blur-container">
        <div class="coupang-blur-badge">
            🔒 추천 제휴 상품 서비스 준비 중입니다
        </div>
        <div class="coupang-blur-content">
            <div class="coupang-card">
                <div style="font-size: 15px; font-weight: bold; color: #1e293b; margin-bottom: 10px;">
                    📦 PC 택배 포장 & 부품 정리에 필요한 추천 아이템
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                    <div class="coupang-item">
                        <div style="font-size: 14px; font-weight: bold;">📦 에어캡 / 뽁뽁이 롤</div>
                        <div style="font-size: 12px; color: #64748b; margin-top: 3px;">그래픽카드·본체 파손 방지 완충재</div>
                        <span class="coupang-link">쿠팡 최저가 보기</span>
                    </div>
                    <div class="coupang-item">
                        <div style="font-size: 14px; font-weight: bold;">🧪 가성비 써멀구리스</div>
                        <div style="font-size: 12px; color: #64748b; margin-top: 3px;">CPU/쿨러 재조립 필수용품</div>
                        <span class="coupang-link">쿠팡 최저가 보기</span>
                    </div>
                    <div class="coupang-item">
                        <div style="font-size: 14px; font-weight: bold;">⚡ 정전기 방지 봉투 (ESD)</div>
                        <div style="font-size: 12px; color: #64748b; margin-top: 3px;">RAM / SSD / 그래픽카드 안전 보관</div>
                        <span class="coupang-link">쿠팡 최저가 보기</span>
                    </div>
                </div>
                <div class="ad-notice">
                    ※ 이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.
                </div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)
