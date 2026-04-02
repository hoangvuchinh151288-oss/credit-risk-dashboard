#!/usr/bin/env python3
"""Fetch CBTT TTC AgriS (SBT) - chay tu dong boi GitHub Actions moi ngay"""
import json, requests, re, os
from bs4 import BeautifulSoup
from datetime import datetime

OUTPUT_FILE = "data/sbt.json"
URLS = [
    "https://ttcagris.com.vn/quan-he-nha-dau-tu/cong-bo-thong-tin?year=2026&cate=3",
    "https://ttcagris.com.vn/quan-he-nha-dau-tu/cong-bo-thong-tin?year=2026&cate=4",
    "https://ttcagris.com.vn/quan-he-nha-dau-tu/cong-bo-thong-tin?year=2025&cate=3",
    "https://ttcagris.com.vn/quan-he-nha-dau-tu/cong-bo-thong-tin?year=2025&cate=4",
]
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept-Language": "vi-VN,vi;q=0.9"}

def extract_date(text):
    m = re.search(r"(\d{1,2}/\d{2}/\d{4})", text)
    return m.group(1) if m else datetime.now().strftime("%d/%m/%Y")

def classify(text):
    t = text.lower()
    if any(x in t for x in ["bctc","kiem toan","tai chinh","loi nhuan"]): return "bctc"
    if any(x in t for x in ["trai phieu","bond","phat hanh"]): return "trai-phieu"
    if any(x in t for x in ["co phieu","co tuc","thoai von","mua lai"]): return "co-phieu"
    if any(x in t for x in ["bo nhiem","nhan su","giam doc","hoi dong"]): return "nhan-su"
    return "hanh-chinh"

def fetch(url):
    items = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for row in soup.select("table tbody tr"):
            tds = row.select("td")
            link_el = row.select_one("a")
            if len(tds) >= 2 and tds[1].get_text(strip=True):
                title = tds[1].get_text(strip=True)
                href = link_el.get("href","") if link_el else ""
                full_url = href if href.startswith("http") else f"https://ttcagris.com.vn{href}"
                items.append({"date": extract_date(tds[0].get_text()), "title": title[:250], "link": full_url, "cat": classify(title)})
    except Exception as e:
        print(f"  Error {url}: {e}")
    return items

def main():
    print("Fetching SBT CBTT...")
    existing = json.load(open(OUTPUT_FILE, encoding="utf-8")) if os.path.exists(OUTPUT_FILE) else {"cbtt": []}
    existing_titles = {i["title"] for i in existing.get("cbtt", [])}
    
    all_items = []
    for url in URLS:
        items = fetch(url)
        all_items.extend(items)
        print(f"  {url}: {len(items)} items")
    
    seen, unique = set(), []
    for item in all_items:
        k = item["title"][:80]
        if k not in seen:
            seen.add(k); unique.append(item)
    
    new_count = sum(1 for i in unique if i["title"] not in existing_titles)
    merged = {i["title"] for i in unique}
    old_only = [i for i in existing.get("cbtt",[]) if i["title"] not in merged]
    final = sorted(unique + old_only, key=lambda x: x.get("date",""), reverse=True)[:80]
    
    os.makedirs("data", exist_ok=True)
    result = {"cbtt": final, "updated": datetime.now().strftime("%d/%m/%Y %H:%M"), "source": "ttcagris.com.vn", "new_count": new_count}
    json.dump(result, open(OUTPUT_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Saved {len(final)} items. New: {new_count}")

if __name__ == "__main__":
    main()
