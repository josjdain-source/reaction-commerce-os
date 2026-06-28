# -*- coding: utf-8 -*-
"""
coupang_adapter.py — 쿠팡 파트너스 Open API 어댑터 (Reaction Commerce OS).

상품 검색 → 딥링크 → 정규화 → product_scout 후보 / /go 카드 데이터로 변환.
Scout Now → 상품 후보 → /go 카드 → 수익 퍼널의 '상품 자동화' 빈칸을 메운다.

원칙(엄수):
- GitHub 쿠팡 코드 복사 안 함. 공식 Coupang Partners Open API(HMAC-SHA256) 문서 기준 우리 코드 100%.
  출처: developers.coupangcorp.com (Affiliate Open API / HMAC 인증 규격).
- access key / secret key / partner id 등은 하드코딩 금지 → .env(gitignore) / 환경변수에서만 읽음.
- 토큰/키는 어떤 경우에도 로그·출력·예외 메시지에 노출하지 않음(_mask만 노출).
- 스크래핑 금지. 자동 구매/리뷰/댓글/계정 우회 금지. 발행은 사람이.
- 키 없이도 mock/dry-run 으로 동작 검증 가능. 키 없으면 실제 호출은 친절히 실패.

CLI:
  python coupang_adapter.py --self-test                 # 키 없이 mock 검증(완료조건)
  python coupang_adapter.py --keyword "곰팡이 제거제" --dry-run   # 서명/요청만(호출 X)
  python coupang_adapter.py --keyword "욕실 청소" --limit 5       # 실제 호출(키 필요)
  python coupang_adapter.py --deeplink "https://www.coupang.com/vp/products/123"
"""
import os
import sys
import json
import time
import hmac
import hashlib
import argparse
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
ENV_FILE = os.path.join(HERE, ".env")
TEST_REPORT = os.path.join(DATA, "coupang_adapter_test_report.json")

API_HOST = "https://api-gateway.coupang.com"
PATH_SEARCH = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
PATH_DEEPLINK = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"

ENV_KEYS = ["COUPANG_ACCESS_KEY", "COUPANG_SECRET_KEY", "COUPANG_PARTNER_ID",
            "COUPANG_TRACKING_CODE", "COUPANG_SUB_ID"]

# 위험 필터(파트너스 약관/우리 정책). 발행 부적합 후보를 미리 표시.
RISK_WORDS = {
    "성인/19금": ["성인", "19금", "성인용품", "흡연", "전자담배", "술", "주류"],
    "도박/투자": ["도박", "카지노", "토토", "코인", "비트코인", "주식리딩"],
    "의약/과장위험": ["의약품", "처방", "다이어트약", "직구 의약"],
    "가품 표현 주의": ["짝퉁", "가품", "레플", "이미테이션"],
}


# ---------------------------------------------------------------- env / 보안
def load_env():
    """.env(있으면) → os.environ 순으로 읽음. 값은 반환만, 로그 금지."""
    env = {}
    if os.path.exists(ENV_FILE):
        for line in open(ENV_FILE, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    for k in ENV_KEYS:
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


def _mask(s):
    if not s:
        return "(없음)"
    s = str(s)
    return (s[:3] + "***" + s[-2:]) if len(s) > 6 else "***"


def keys_ready(env):
    return bool(env.get("COUPANG_ACCESS_KEY") and env.get("COUPANG_SECRET_KEY"))


# ---------------------------------------------------------------- HMAC 서명
def _signed_date():
    # 공식 규격: yyMMdd'T'HHmmss'Z' (GMT)
    return time.strftime("%y%m%dT%H%M%SZ", time.gmtime())


def _authorization(method, path, query, env):
    """CEA HmacSHA256 Authorization 헤더 생성. message = date+method+path+query."""
    secret = env["COUPANG_SECRET_KEY"]
    access = env["COUPANG_ACCESS_KEY"]
    dt = _signed_date()
    message = dt + method + path + query
    signature = hmac.new(secret.encode("utf-8"), message.encode("utf-8"),
                         hashlib.sha256).hexdigest()
    return (f"CEA algorithm=HmacSHA256, access-key={access}, "
            f"signed-date={dt}, signature={signature}")


def _request(method, path, query="", body=None, env=None, timeout=20):
    """서명 후 호출. 반환: (ok, status, json_or_text). 키/서명 본문은 로그 안 함."""
    url = API_HOST + path + (("?" + query) if query else "")
    headers = {
        "Authorization": _authorization(method, path, query, env),
        "Content-Type": "application/json;charset=UTF-8",
        "X-Requested-By": env.get("COUPANG_PARTNER_ID", "") or "reaction-commerce-os",
    }
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return True, r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # 키 값은 절대 노출하지 않음. 상태/응답 본문만.
        try:
            return False, e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return False, e.code, {"error": "http_error"}
    except Exception as e:
        return False, 0, {"error": type(e).__name__}


# ---------------------------------------------------------------- 정규화/변환
def _risk_flags(blob):
    blob = (blob or "").lower()
    flags = [label for label, words in RISK_WORDS.items() if any(w in blob for w in words)]
    return flags


def normalize_product(raw):
    """쿠팡 search 응답 항목 → 우리 표준 구조."""
    title = raw.get("productName") or raw.get("title") or ""
    purl = raw.get("productUrl") or raw.get("product_url") or ""
    return {
        "title": title,
        "price": raw.get("productPrice") or raw.get("price"),
        "image": raw.get("productImage") or raw.get("image") or "",
        "product_url": purl,
        # search 결과 productUrl은 본인 계정 제휴링크. 필요 시 create_deeplink로 단축.
        "affiliate_url": raw.get("affiliate_url") or purl,
        "product_id": raw.get("productId") or raw.get("product_id"),
        "is_rocket": bool(raw.get("isRocket")),
        "category": raw.get("categoryName") or "",
        "source": "coupang_api",
        "risk_flags": _risk_flags(title + " " + (raw.get("categoryName") or "")),
        "scout_score_ready": bool(title and purl),
    }


def to_scout_candidate(item):
    """product_scout.add_candidate(...) 인자로 바로 쓸 dict."""
    return {
        "name": item["title"],
        "price": str(item.get("price") or ""),
        "url": item.get("affiliate_url") or item.get("product_url") or "",
        "thumbnail": item.get("image") or "",
        "keywords": item.get("category") or "",
        "source": "coupang_api",
    }


def to_go_card(item, pack, emoji="🛍️", reel_url="", desc=None):
    """/go links.json items[] 카드 형태(ig_publish CARDS와 호환)."""
    return {
        "pack": pack, "card_id": pack, "source": "coupang_api", "emoji": emoji,
        "thumb": item.get("image") or "",
        "title": item.get("title") or "",
        "desc": desc or "영상 속 준비물, 여기서 바로 확인해요.",
        "btn": "준비물 보기",
        "coupang": item.get("affiliate_url") or item.get("product_url") or "",
        "reel_url": reel_url, "banner": "",
        "disclosure": "쿠팡 파트너스 활동의 일환으로 이에 따른 일정액의 수수료를 제공받습니다.",
        "click_count": 0, "last_clicked_at": None,
    }


# ---------------------------------------------------------------- 공개 기능
def search_products(keyword, limit=10, env=None, dry_run=False, mock=None):
    env = env or load_env()
    query = urllib.parse.urlencode({"keyword": keyword, "limit": limit})
    if mock is not None:
        items = [normalize_product(p) for p in mock]
        return {"ok": True, "mode": "mock", "keyword": keyword, "items": items}
    if dry_run:
        return {"ok": True, "mode": "dry-run", "keyword": keyword,
                "would_call": f"GET {PATH_SEARCH}?{query}",
                "signed": keys_ready(env), "items": []}
    if not keys_ready(env):
        return {"ok": False, "mode": "live", "error": "키 없음 — .env에 "
                "COUPANG_ACCESS_KEY/COUPANG_SECRET_KEY 필요(대시보드에서 발급).",
                "need_env": ENV_KEYS, "items": []}
    ok, status, resp = _request("GET", PATH_SEARCH, query, env=env)
    if not ok:
        return {"ok": False, "mode": "live", "status": status,
                "error": resp.get("rMessage") or resp.get("error") or "api_error",
                "items": []}
    raw = (resp.get("data") or {})
    rows = raw.get("productData") if isinstance(raw, dict) else raw
    items = [normalize_product(p) for p in (rows or [])]
    return {"ok": True, "mode": "live", "status": status, "keyword": keyword, "items": items}


def create_deeplink(urls, env=None, sub_id=None, dry_run=False, mock=None):
    env = env or load_env()
    sub_id = sub_id or env.get("COUPANG_SUB_ID") or None
    body = {"coupangUrls": urls}
    if sub_id:
        body["subId"] = sub_id
    if mock is not None:
        links = [{"original": d.get("originalUrl"), "shorten": d.get("shortenUrl"),
                  "landing": d.get("landingUrl")} for d in mock]
        return {"ok": True, "mode": "mock", "links": links}
    if dry_run:
        return {"ok": True, "mode": "dry-run",
                "would_call": f"POST {PATH_DEEPLINK}", "body": body,
                "signed": keys_ready(env), "links": []}
    if not keys_ready(env):
        return {"ok": False, "mode": "live", "error": "키 없음 — .env 필요.",
                "need_env": ENV_KEYS, "links": []}
    ok, status, resp = _request("POST", PATH_DEEPLINK, body=body, env=env)
    if not ok:
        return {"ok": False, "mode": "live", "status": status,
                "error": resp.get("rMessage") or resp.get("error") or "api_error",
                "links": []}
    data = resp.get("data") or []
    links = [{"original": d.get("originalUrl"), "shorten": d.get("shortenUrl"),
              "landing": d.get("landingUrl")} for d in data]
    return {"ok": True, "mode": "live", "status": status, "links": links}


# ---------------------------------------------------------------- self-test (mock)
MOCK_PRODUCTS = [
    {"productId": 111, "productName": "곰팡이 제거제 욕실 청소 스프레이 500ml",
     "productPrice": 8900, "productImage": "https://img.example/mock1.jpg",
     "productUrl": "https://link.coupang.com/a/MOCK111",
     "categoryName": "생활용품", "isRocket": True},
    {"productId": 222, "productName": "하수구 냄새 제거 트랩 2개입",
     "productPrice": 12900, "productImage": "https://img.example/mock2.jpg",
     "productUrl": "https://link.coupang.com/a/MOCK222",
     "categoryName": "욕실용품", "isRocket": False},
    {"productId": 333, "productName": "욕실 곰팡이 방지 실리콘 테이프 5m",
     "productPrice": 6500, "productImage": "https://img.example/mock3.jpg",
     "productUrl": "https://link.coupang.com/a/MOCK333",
     "categoryName": "생활용품", "isRocket": True},
]
MOCK_DEEPLINK = [{"originalUrl": "https://www.coupang.com/vp/products/999",
                  "shortenUrl": "https://link.coupang.com/a/MOCK999",
                  "landingUrl": "https://landing.coupang.com/MOCK999"}]


def self_test():
    env = load_env()
    checks, ok = [], True

    def chk(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        checks.append({"check": name, "pass": bool(cond)})

    s = search_products("곰팡이 제거제", limit=2, env=env, mock=MOCK_PRODUCTS)
    chk("mock 검색 동작(키 불필요)", s["ok"] and len(s["items"]) == 2)
    item = s["items"][0]
    chk("정규화 필드 완비", all(k in item for k in
        ("title", "price", "image", "product_url", "affiliate_url",
         "source", "risk_flags", "scout_score_ready")))
    chk("source=coupang_api", item["source"] == "coupang_api")
    chk("scout_score_ready=True", item["scout_score_ready"] is True)

    cand = to_scout_candidate(item)
    chk("product_scout 후보 변환", all(k in cand for k in ("name", "price", "url", "source")))
    chk("product_scout 연동 가능", _scout_accepts(cand))

    card = to_go_card(item, pack="mock_pack", emoji="🦠")
    chk("/go 카드 변환", all(k in card for k in ("pack", "title", "coupang", "thumb", "btn")))

    d = create_deeplink(["https://www.coupang.com/vp/products/999"], env=env, mock=MOCK_DEEPLINK)
    chk("mock 딥링크 동작", d["ok"] and d["links"][0]["shorten"].endswith("MOCK999"))

    dry = search_products("욕실 청소", env=env, dry_run=True)
    chk("dry-run은 호출 안 함", dry["ok"] and dry["mode"] == "dry-run")

    nokey = {k: "" for k in ENV_KEYS}
    live = search_products("x", env=nokey)
    chk("키 없으면 친절히 실패(예외 X)", live["ok"] is False and "need_env" in live)

    report = {
        "ok": ok,
        "keys_present": {k: (_mask(env.get(k))) for k in ENV_KEYS},  # 값 노출 없이 마스킹만
        "keys_ready_for_live": keys_ready(env),
        "checks": checks,
        "note": "mock/dry-run은 키 없이 통과. 실제 호출은 .env에 키 넣은 뒤.",
    }
    os.makedirs(DATA, exist_ok=True)
    json.dump(report, open(TEST_REPORT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return report


def _scout_accepts(cand):
    """product_scout.add_candidate가 이 dict를 받는지 시그니처로 확인(실제 추가는 안 함)."""
    try:
        import inspect
        import product_scout
        params = inspect.signature(product_scout.add_candidate).parameters
        return all(k in params for k in cand.keys())
    except Exception:
        return False


# ---------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keyword")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--deeplink")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        rep = self_test()
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        print("\n결과:", "✅ 통과" if rep["ok"] else "❌ 실패", "→", TEST_REPORT)
        sys.exit(0 if rep["ok"] else 1)

    env = load_env()
    if a.deeplink:
        res = create_deeplink([a.deeplink], env=env, dry_run=a.dry_run,
                              mock=(MOCK_DEEPLINK if a.mock else None))
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return
    if a.keyword:
        res = search_products(a.keyword, limit=a.limit, env=env, dry_run=a.dry_run,
                              mock=(MOCK_PRODUCTS if a.mock else None))
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return
    ap.print_help()


if __name__ == "__main__":
    main()
