#!/usr/bin/env python3
"""Fetch CBTT VietJet Air (VJC) - chay tu dong boi GitHub Actions moi ngay"""
import json, requests, re, os
from bs4 import BeautifulSoup
from datetime import datetime

OUTPUT_FILE = "data/vjc.json"
BASE = "https://ir.vietjetair.com"
URLS = [
    "https://ir.vietjetair.com/Home/Menu/thong-tin-khac",
    "https://ir.vietjetair.com/Home/Menu/thong-tin-dinh-ky",
    "https://ir.vietjetair.com/Home/Menu/bao-cao-tai-chinh-quy",
    "https://ir.vietjetair.com/Home/Menu/ket-qua-hoat-dong-quy",
]
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8", "Referer": BASE}

def extract_date(text):
    m = re.search(r"(\d{2}/\d{2}/\d{4})", text)
    return m.group(1) if m else datetime.now().strftime("%d/%m/%Y")

def clean_title(text):
    return re.sub(r"^\d{2}/\d{2}/\d{4}:\s*", "", text).strip()[:250]

def classify(text, href=""):
    t = (text + href).lower()
    if any(x in t for x in ["bctc","tai chinh","kiem toan","loi nhuan","doanh thu"]): return "bctc"
    if any(x in t for x in ["trai phieu","tprl","bond","phat-hanh-trai"]): return "trai-phieu"
    if any(x in t for x in ["toa an","tranh chap","fwa","phap ly"]): return "phap-ly"
    if any(x in t for x in ["tau bay","doi bay","airbus","boeing"]): return "doi-bay"
    if any(x in t for x in ["co phieu","co tuc","niem yet","chao ban"]): return "co-phieu"
    if any(x in t for x in ["bo nhiem","nhan su","giam doc","ke toan"]): return "nhan-su"
    return "hanh-chinh"

def fetch(url):
    items = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a.get("href","")
            text = a.get_text(strip=True)
            if len(text) < 15 or len(text) > 400: continue
            if not (href.endswith(".pdf") or "ir.vietjetair.com" in href or (href.startswith("/") and len(href) > 5)): continue
            full_url = href if href.startswith("http") else f"{BASE}{href}"
            items.append({"date": extract_date(text), "title": clean_title(text), "link": full_url, "cat": classify(text, href)})
        for el in soup.find_all(string=re.compile(r"\d{2}/\d{2}/\d{4}:")):
            text = str(el).strip()
            if 20 < len(text) < 300:
                parent = el.parent
                href = parent.get("href","") if parent and parent.name=="a" else ""
                items.append({"date": extract_date(text), "title": clean_title(text), "link": href or url, "cat": classify(text)})
    except Exception as e:
        print(f"  Error {url}: {e}")
    return items

def main():
    print("Fetching VJC CBTT...")
    existing = json.load(open(OUTPUT_FILE, encoding="utf-8")) if os.path.exists(OUTPUT_FILE) else {"cbtt": []}
    existing_titles = {i["title"] for i in existing.get("cbtt",[])}
    
    all_items = []
    for url in URLS:
        items = fetch(url)
        all_items.extend(items)
        print(f"  {url}: {len(items)} items")
    
    seen, unique = set(), []
    for item in all_items:
        k = item["title"][:80]
        if k not in seen and len(item["title"]) > 10:
            seen.add(k); unique.append(item)
    
    new_count = sum(1 for i in unique if i["title"] not in existing_titles)
    merged = {i["title"] for i in unique}
    old_only = [i for i in existing.get("cbtt",[]) if i["title"] not in merged]
    final = sorted(unique + old_only, key=lambda x: x.get("date",""), reverse=True)[:100]
    
    os.makedirs("data", exist_ok=True)
    result = {"cbtt": final, "updated": datetime.now().strftime("%d/%m/%Y %H:%M"), "source": "ir.vietjetair.com", "new_count": new_count}
    json.dump(result, open(OUTPUT_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Saved {len(final)} items. New: {new_count}")

if __name__ == "__main__":
    main()
