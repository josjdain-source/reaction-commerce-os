# -*- coding: utf-8 -*-
"""
github_code_miner.py — Reaction Commerce OS 부품 탐사기.

GitHub 오픈소스를 검색해 "우리 루프에 보강할 부품"을 찾는다.
원칙(엄수): 코드를 그대로 베끼지 않는다 → 라이선스 확인 → 패턴만 추출 → 우리 코드로 새로 작성 → 출처 기록.

CLI:
  python github_code_miner.py "coupang partners"
  python github_code_miner.py "instagram reels api" 10
출력: 콘솔 표 + data/mined_repos.json (출처·라이선스 기록)
"""
import os
import sys
import json
import datetime
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "mined_repos.json")

# 라이선스별 흡수 가이드 (패턴 추출 기준 — 직접 복붙은 어느 경우든 금지)
LIC_OK = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "Unlicense", "0BSD", "MPL-2.0"}
LIC_WARN = {"GPL-3.0", "GPL-2.0", "AGPL-3.0", "LGPL-3.0"}


def _lic_note(spdx):
    if not spdx or spdx == "NOASSERTION":
        return "⚠ 라이선스 없음 → 무단 사용 X, 아이디어/구조만 참고"
    if spdx in LIC_OK:
        return f"✅ {spdx} → 패턴 추출 OK(출처 표기)"
    if spdx in LIC_WARN:
        return f"⚠ {spdx} → 전염성/카피레프트, 직접 통합 주의(우리 코드 새로 작성)"
    return f"❓ {spdx} → 확인 필요"


def search(query, n=10):
    url = ("https://api.github.com/search/repositories?q="
           + urllib.parse.quote(query) + f"&sort=stars&order=desc&per_page={n}")
    req = urllib.request.Request(url, headers={
        "User-Agent": "reaction-commerce-os-miner",
        "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        data = json.load(r)
    rows = []
    for it in data.get("items", []):
        lic = (it.get("license") or {}).get("spdx_id")
        rows.append({
            "name": it.get("full_name"), "stars": it.get("stargazers_count"),
            "lang": it.get("language"), "license": lic, "license_note": _lic_note(lic),
            "desc": (it.get("description") or "")[:120], "url": it.get("html_url"),
            "updated": (it.get("pushed_at") or "")[:10],
        })
    return rows


def mine(query, n=10):
    rows = search(query, n)
    rec = {"query": query, "mined_at": datetime.datetime.now().isoformat(timespec="minutes"),
           "principle": "코드 복사 금지 — 라이선스 확인 → 패턴만 추출 → 우리 코드로 새로 작성 → 출처 기록",
           "results": rows}
    db = []
    if os.path.exists(OUT):
        try:
            db = json.load(open(OUT, encoding="utf-8"))
        except Exception:
            db = []
    db = [d for d in db if d.get("query") != query]  # 같은 쿼리는 갱신
    db.insert(0, rec)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(db, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return rec


def main():
    if len(sys.argv) < 2:
        print('사용: python github_code_miner.py "검색어" [개수]')
        return
    q = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    try:
        rec = mine(q, n)
    except Exception as e:
        print("검색 오류(레이트리밋/네트워크일 수 있음):", e)
        return
    print(f'=== GitHub 탐사: "{q}" ({len(rec["results"])}개, 별점순) ===')
    print("원칙:", rec["principle"], "\n")
    for r in rec["results"]:
        print(f"★{r['stars']:<6} {r['name']}  [{r['lang'] or '-'}]")
        print(f"   {r['license_note']}")
        print(f"   {r['desc']}")
        print(f"   {r['url']}  (updated {r['updated']})\n")


if __name__ == "__main__":
    main()
