# Coupang Adapter — 쿠팡 파트너스 자동화

Reaction Commerce OS의 **수익 퍼널** 모듈. 상품 검색 → 딥링크 → 정규화 →
`product_scout` 후보 / `/go` 카드 데이터로 변환한다.
**Scout Now → 상품 후보 → /go 카드 → 수익**의 '상품 자동화' 빈칸을 메운다.

> 코드 출처: 공식 Coupang Partners Open API (HMAC-SHA256) 문서 기준 **새로 작성**.
> GitHub 쿠팡 코드 복사 안 함(발견 repo는 라이선스 없음 → 구조 참고만).

## 안전 원칙
- 키는 **`.env`(gitignore) / 환경변수에서만** 읽음. 하드코딩 금지.
- 토큰/키는 로그·출력·예외 메시지에 **절대 노출 안 함** (`_mask`만).
- 스크래핑 금지. 자동 구매/리뷰/댓글/계정 우회 금지. **발행은 사람이.**
- 키 없이도 mock/dry-run 으로 검증 가능. 키 없으면 실제 호출은 친절히 실패.

## 환경변수 (`.env`)
`.env.example` 복사 후 값 입력 (대시보드 > API 발급):
```
COUPANG_ACCESS_KEY=     # 필수
COUPANG_SECRET_KEY=     # 필수
COUPANG_PARTNER_ID=     # 선택(X-Requested-By)
COUPANG_TRACKING_CODE=  # 선택
COUPANG_SUB_ID=         # 선택(딥링크 subId)
```

## 사용법
```bash
python coupang_adapter.py --self-test                      # 키 없이 mock 검증
python coupang_adapter.py --keyword "곰팡이 제거제" --dry-run  # 서명/요청만(호출 X)
python coupang_adapter.py --keyword "욕실 청소" --limit 5      # 실제 호출(키 필요)
python coupang_adapter.py --deeplink "<쿠팡상품URL>"          # 딥링크 단축
python coupang_adapter.py --deeplink "<URL>" --mock           # mock 딥링크
```

## 코드에서
```python
import coupang_adapter as CA
res = CA.search_products("곰팡이 제거제", limit=5)   # {ok, mode, items:[...]}
item = res["items"][0]
CA.to_scout_candidate(item)        # product_scout.add_candidate(**dict) 호환
CA.to_go_card(item, pack="mold_city_collapse", emoji="🦠", reel_url="...")  # /go links.json 카드
CA.create_deeplink(["https://www.coupang.com/vp/products/123"])             # 딥링크 단축
```

## 표준 출력 구조 (`normalize_product`)
```json
{
  "title": "...", "price": 8900, "image": "...",
  "product_url": "...", "affiliate_url": "...",
  "source": "coupang_api", "risk_flags": [], "scout_score_ready": true
}
```

## 완료 조건 (self-test로 검증)
- [x] 키 없이 mock 테스트 통과
- [x] 키 없으면 실제 호출 안 하고 친절히 실패
- [x] 토큰/키가 로그에 출력되지 않음(마스킹만)
- [x] `product_scout.add_candidate` 가 어댑터 결과를 받음
- [x] `/go links.json` 카드 형태로 변환 가능
- [x] `.env.example` 포함(공개 시 안전)

## 다음 연결 (예정)
1. `scout_now` / `product_scout` 에서 `search_products` 호출 → 후보 자동 적재
2. 발행 시 `to_go_card` → `/go links.json` 자동 카드 (현재는 수동 CARDS)
