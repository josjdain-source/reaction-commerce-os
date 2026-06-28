# Reaction Commerce OS

> An open-source workflow for AI-assisted reaction shorts, affiliate routing,
> and creator monetization pipelines.

대부분의 오픈소스는 "영상 만드는 도구"에서 멈춥니다. **Reaction Commerce OS**는 그 뒤를 잇습니다 —
상품 정찰 → 쇼츠 패턴 → 감정 게이트 → 캐릭터 보이스 → 영상 조립 → 발행 → 링크인바이오 → **제휴 전환**까지
하나의 루프로. 리액션 쇼츠 한 편이 끝나는 게 아니라, **제휴 링크 카드까지 자동으로 연결**됩니다.

📐 **전체 구조(공장 지도)**: [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) — Product Scout → Content Pack → Capture → Emotion → Voice → Assembler → Publisher → Link-in-bio → Metrics

---

## Copyright and License

Reaction Commerce OS is open source software.

**Copyright (c) 2026 투 성 / IGS AI 개발.**
Copyright remains with the original author.

You are allowed to use, modify, and distribute this project under the terms of the
[LICENSE](./LICENSE) file (Apache License 2.0).
**Open source release does not mean copyright waiver or public domain dedication.**

Do not remove copyright notices, license notices, or attribution files
([NOTICE](./NOTICE)).

---

## ⚠️ 먼저 읽으세요 — 이 도구가 아닌 것
**스팸 / 자동 DM / 무단 재업로드 도구가 아닙니다.** 사용 전 [SAFETY_POLICY.md](./SAFETY_POLICY.md)를 반드시 읽으세요.

금지 (도구에 포함하지 않으며, 우회 목적 사용 금지):
- ❌ 자동 팔로우 / 자동 DM / 연락처 업로드 / 봇·대량계정 스팸
- ❌ 남의 영상·이미지 **무단 재업로드**
- ❌ 쿠팡 / 인스타 / 유튜브 / 네이버 **스크래핑·정책 우회** — 공식 API 우선
- ❌ 자동 구매 / 자동 리뷰 / 자동 댓글 / 계정 우회

필수:
- ✅ **제휴 고지 필수** — "쿠팡 파트너스 활동의 일환으로 일정액의 수수료를 제공받습니다."
- ✅ **공식 API 우선** — Instagram Graph API, Coupang Partners Open API
- ✅ **키는 `.env`로만** — 토큰/키 하드코딩 금지 (`.env`는 gitignore)
- ✅ **발행은 사람** — 자동 인터넷 게시 없음. 클릭 = 명시적 승인

---

## 이 공개본(preview)에 포함된 것
재사용 가능한 핵심 모듈 + 안전 도구만 담은 **프리뷰 릴리스**입니다.
운영 오케스트레이션(발행기·미션 콘트롤 등)과 실제 운영 데이터는 비공개로 유지합니다.

| 파일 | 역할 |
|---|---|
| `coupang_adapter.py` | 공식 Coupang Partners Open API(HMAC-SHA256) 어댑터 — 딥링크/상품검색, 키는 `.env`만, mock/dry-run 우선 |
| `github_code_miner.py` | 오픈소스 부품 탐사 — 별점+라이선스 판정, **패턴만 추출·복사 금지**, 출처 기록 |
| `secrets_audit.py` | 공개 전 민감정보 감사 — 토큰/키 스캔, gitignore 확인, 공개/비공개 분류 |
| `docs/COUPANG_ADAPTER.md` | 어댑터 사용법·안전원칙 |
| `SAFETY_POLICY.md` | 안전 정책(절대공개금지·사용금지·필수준수·체크리스트) |
| `.env.example` | 환경변수 예시(실제 키 없음) |

## 빠른 시작
```bash
cp .env.example .env          # 본인 키 입력 (Coupang Partners)
python secrets_audit.py       # 공개 전 안전 점검 → SAFE 확인
python coupang_adapter.py --self-test          # 키 없이 동작 검증(mock)
python coupang_adapter.py --keyword "검색어" --limit 3   # 실제 호출(키 필요)
python github_code_miner.py "coupang partners api"       # OSS 부품 탐사
```

## 표준 출력 (`coupang_adapter.normalize_product`)
```json
{ "title": "...", "price": 8900, "image": "...",
  "product_url": "...", "affiliate_url": "...",
  "source": "coupang_api", "risk_flags": [], "scout_score_ready": true }
```

## 외부 코드 사용 원칙
GitHub에서 발견한 코드는 **그대로 복사하지 않습니다.** 라이선스를 확인하고, 패턴만 참고해
**우리 코드로 새로 작성한 것만** 공개합니다. 탐사한 출처는 `data/mined_repos.json`에 기록됩니다.
(쿠팡 파트너스 관련 공개 repo는 라이선스가 없어 구조만 참고, 어댑터는 공식 문서 기준 100% 자체 작성.)

## 환경변수
[.env.example](./.env.example) 참고. 실제 값은 `.env`에만 (gitignore 됨).

---
*Trademarks (Instagram, Coupang, Naver, GitHub 등) belong to their respective owners.
이 프로젝트는 어떤 플랫폼과도 제휴/후원 관계가 없습니다.*
