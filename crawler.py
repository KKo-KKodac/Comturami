import io
import re
from datetime import datetime
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
import pandas as pd

# 1. 구글 스프레드시트 연동 설정 (기존에 쓰시던 시트 ID를 따옴표 안에 넣어주세요!)
SHEET_ID = ""18Jbbs1qvp9rYew6gaJglcqMzpCUGR0iTlep8NTjyltM""

# 2. 기존 수집 URL 기본 목록 (56개)
BASE_URLS = [
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=10&ctgry_no2=966&ctgry_no3=4220",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=10&ctgry_no2=966&ctgry_no3=967",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=10&ctgry_no2=966&ctgry_no3=4221",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=8&ctgry_no2=9&ctgry_no3=4083",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=8&ctgry_no2=9&ctgry_no3=31",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=8&ctgry_no2=9&ctgry_no3=993",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=8&ctgry_no2=9&ctgry_no3=1684",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=8&ctgry_no2=9&ctgry_no3=3682",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=8&ctgry_no2=9&ctgry_no3=3838",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=8&ctgry_no2=9&ctgry_no3=3918",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=8&ctgry_no2=9&ctgry_no3=25",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=8&ctgry_no2=9&ctgry_no3=4020",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=8&ctgry_no2=9&ctgry_no3=4089",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=8&ctgry_no2=9&ctgry_no3=4137",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=8&ctgry_no2=9&ctgry_no3=4144",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=8&ctgry_no2=9&ctgry_no3=4303",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=8&ctgry_no2=9&ctgry_no3=4304",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=14&ctgry_no2=58&ctgry_no3=3784",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=14&ctgry_no2=58&ctgry_no3=3775",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=14&ctgry_no2=58&ctgry_no3=3768",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=14&ctgry_no2=58&ctgry_no3=3808",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=14&ctgry_no2=58&ctgry_no3=4075",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=14&ctgry_no2=58&ctgry_no3=4145",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=14&ctgry_no2=59&ctgry_no3=3901",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=14&ctgry_no2=59&ctgry_no3=3902",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=14&ctgry_no2=59&ctgry_no3=4085",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=14&ctgry_no2=59&ctgry_no3=4146",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=14&ctgry_no2=59&ctgry_no3=4218",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=12&ctgry_no2=42&ctgry_no3=3701",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=12&ctgry_no2=42&ctgry_no3=3932",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=12&ctgry_no2=42&ctgry_no3=4021",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=12&ctgry_no2=42&ctgry_no3=4090",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=12&ctgry_no2=42&ctgry_no3=4305",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=12&ctgry_no2=4026&ctgry_no3=4029",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=12&ctgry_no2=4026&ctgry_no3=4139",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=14&ctgry_no2=58&ctgry_no3=4199",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=10&ctgry_no2=57",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=1&ctgry_no2=2&ctgry_no3=3866",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=1&ctgry_no2=2&ctgry_no3=4141",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=1&ctgry_no2=2&ctgry_no3=3608",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=1&ctgry_no2=2&ctgry_no3=7",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=8&ctgry_no2=24&ctgry_no3=3943",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=8&ctgry_no2=24&ctgry_no3=3945",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=8&ctgry_no2=24&ctgry_no3=30",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=8&ctgry_no2=24&ctgry_no3=4072",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=8&ctgry_no2=24&ctgry_no3=4138",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=8&ctgry_no2=24&ctgry_no3=4197",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=1&ctgry_no2=2&ctgry_no3=651",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=1&ctgry_no2=2&ctgry_no3=5",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=12&ctgry_no2=42&ctgry_no3=1208",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=4273&ctgry_no2=4274",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=4273&ctgry_no2=4275",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=4273&ctgry_no2=4276",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=4273&ctgry_no2=4280",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=4277&ctgry_no2=4278",
    "https://www.worldmemory.co.kr/price/computer.do?ctgry_no1=4277&ctgry_no2=4279"
]

def fetch_sheet_urls(sheet_id):
    """구글 시트 '월드_수집 URL' 탭의 D열에서 URL 목록을 가져오는 함수"""
    sheet_urls = []
    
    # 실제 시트 탭 이름인 '월드_수집 URL'(언더바 포함)을 우선 탐색하도록 설정
    sheet_names = ["월드_수집 URL", "월드 수집 URL"]
    export_urls = [
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={quote(name)}"
        for name in sheet_names
    ]
    # 탭 이름 조회가 모두 실패할 경우 기본 시트 조회
    export_urls.append(f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    for export_url in export_urls:
        try:
            res = requests.get(export_url, headers=headers, timeout=10)
            res.encoding = "utf-8"
            
            # 정상적으로 CSV 데이터를 받아왔는지 확인 (권한 문제로 로그인 HTML 페이지가 뜨는 경우 제외)
            if res.status_code == 200 and "text/html" not in res.headers.get("Content-Type", ""):
                # 첫 줄이 비어있을 수 있으므로 header=None으로 모든 행을 빠짐없이 읽음
                df_sheet = pd.read_csv(io.StringIO(res.text), header=None)
                
                current_urls = []
                # D열(인덱스 3)이 존재하면 D열을 우선 탐색, 없으면 전체 열 탐색
                target_cols = [3] if 3 in df_sheet.columns else df_sheet.columns
                
                for col in target_cols:
                    for item in df_sheet[col].dropna().astype(str):
                        url = item.strip()
                        if url.startswith("http") and "worldmemory.co.kr" in url:
                            current_urls.append(url)
                
                # 첫 번째 시트('매입품목 및 가격')와 헷갈리지 않도록 최소 10개 이상의 URL이 발견되었을 때만 채택
                if len(set(current_urls)) >= 10:
                    sheet_urls = current_urls
                    break
        except Exception as e:
            continue

    return list(dict.fromkeys(sheet_urls))

def get_final_url_list():
    """기존 URL과 시트 URL을 병합 및 중복 제거"""
    print(f"[{datetime.now()}] 구글 시트 URL 조회 시도 중...")
    sheet_urls = fetch_sheet_urls(SHEET_ID)
    
    # 순서를 보장하면서 중복 제거 병합
    combined = list(dict.fromkeys(BASE_URLS + sheet_urls))
    added_count = len(combined) - len(BASE_URLS)
    
    print(f"기존 등록 URL: {len(BASE_URLS)}개")
    print(f"구글 시트 연동 URL: {len(sheet_urls)}개 (새로 추가된 항목: {added_count}개)")
    print(f"최종 수집 대상 URL: {len(combined)}개")
    return combined

def crawl_and_save():
    target_urls = get_final_url_list()
    print(f"[{datetime.now()}] 크롤링 시작 (총 {len(target_urls)}개 URL)...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    all_rows = []
    
    for idx, url in enumerate(target_urls, 1):
        try:
            res = requests.get(url, headers=headers, timeout=8)
            res.encoding = "utf-8"
            soup = BeautifulSoup(res.text, "html.parser")
            rows = soup.select("tr")
            for row in rows:
                c = row.find("td", class_="price_table_ctgry_nm")
                n = row.find("td", class_="price_table_prduct_nm")
                p = row.find("td", class_="price_table_prduct_pc")
                if c and n and p:
                    price_str = re.sub(r'[^0-9]', '', p.text)
                    if price_str:
                        price_num = int(price_str)
                        if price_num > 0:
                            all_rows.append({
                                "분류": c.text.strip(),
                                "상품명": n.text.strip(),
                                "매입가": price_num
                            })
            print(f"[{idx}/{len(target_urls)}] 수집 완료")
        except Exception as e:
            print(f"[{idx}/{len(target_urls)}] 수집 에러 ({url}): {e}")
            continue

    if all_rows:
        df = pd.DataFrame(all_rows)
        # 분류 및 상품명 기준 중복 데이터 제거
        df.drop_duplicates(subset=["분류", "상품명"], inplace=True)
        # CSV 파일로 저장
        df.to_csv("price_data.csv", index=False, encoding="utf-8-sig")
        print(f"[{datetime.now()}] 총 {len(df)}개 품목 저장 완료 -> price_data.csv")
    else:
        print("수집된 데이터가 없습니다.")

if __name__ == "__main__":
    crawl_and_save()
