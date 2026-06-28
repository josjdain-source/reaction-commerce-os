# Architecture — Reaction Commerce OS

> 전체 지도. 이 프로젝트는 "영상 만드는 도구"가 아니라, **리액션 쇼츠 한 편이 제휴 수익 카드까지
> 자동으로 연결되는 안전한 제작 파이프라인**이다. 자동발행 스팸이 아니라 사람이 승인하는 루프.

핵심 선언: **AI 쇼츠 수익화 = 자동발행 스팸이 아니라, 안전한 제작 파이프라인으로 만들 수 있다.**

---

## 한눈에 — 파이프라인

```
 ① Product Scout      상품/소재 정찰 → 5축 점수 → 콘텐츠 후보
        │
 ② Content Pack       세계관·대본·컷 설계(단위 = 멀티채널 원본)
        │
 ③ Capture Board      참고 스샷 수집·정리 (정찰/검수용, 발행 소재 아님)
        │
 ④ Emotion Director   대사 감정 게이트 (그림↔목소리 일치 강제)
        │
 ⑤ Voice OS           캐릭터별 TTS (이미지에서 화자·감정·톤 역산)
        │
 ⑥ Video Assembler    이미지+음성+자막+SFX → 9:16 초벌 mp4
        │
 ⑦ Publisher          호스팅 → 릴스 게시 (공식 API · 사람 클릭 승인)
        │
 ⑧ Link-in-bio (/go)  영상별 제휴 카드 자동 누적 (단일 bio 링크)
        │
 ⑨ Metrics            성과 추적 → 다음 정찰로 환류
```

가로지르는 3축(모든 단계 공통):
- **Safety** — 키는 `.env`만, 공개 전 `secrets_audit`, 민감정보 분리
- **Official-API-first** — 스크래핑 금지, 공식 API 우선
- **Human-in-the-loop** — 자동 인터넷 게시 없음, 발행은 사람 승인

---

## 단계별 상세

### ① Product Scout `product_scout` · `scout_now`
상품/소재를 받아 **쇼츠화 가능성 5축 100점**으로 점수화하고 콘텐츠팩 후보를 만든다.
쿠팡 어댑터(`coupang_adapter`)로 상품 후보를 불러올 수 있다(mock/dry-run 우선).
- 입력: 키워드 · 수동 상품 · (선택) Coupang Partners 검색
- 출력: 점수화된 후보 TOP3 → 콘텐츠팩 각도
- 원칙: 쿠팡 스크래핑 금지 → 공식 API 또는 수동 입력

### ② Content Pack `content_pack`
릴스 단위가 아니라 **멀티채널 원본 단위**. 세계관/대본/컷 설계가 한 팩에 묶인다.
제작 단계(음성→이미지→실사→조립→발행)를 파일 상태에서 자동 산출.

### ③ Capture Board `capture_board`
참고 스크린샷을 컷 단위로 수집·정리한다. **정찰/검수용이며 발행 소재가 아니다** —
최종 소재는 직접 촬영 / AI 재생성 / 사람 승인.

### ④ Emotion Director `emotion_director`
대사의 감정을 5축으로 게이트한다. 핵심 규칙: **그림을 먼저 읽고 거기서 화자·감정·톤·내용을 역산** —
화면의 사실과 소리가 어긋나면 코미디가 깨지므로 이미지↔목소리 일치를 강제한다.

### ⑤ Voice OS `voice_director` · voice profiles
캐릭터별 TTS 프리셋으로 컷마다 다른 목소리를 입힌다. 음성은 **계획 시간이 아니라 실제 길이로 순차 배치**
(겹침 금지). 캐릭터 시트로 일관성 유지.

### ⑥ Video Assembler `video_assembler` / `assemble_sequence`
이미지(켄번스) + 음성(순차) + 자막(번인) + SFX → 9:16 세로 초벌 mp4.
길이 초과 시 피치 보존 압축. 결과는 검수용 draft.

### ⑦ Publisher `publisher`
영상을 공개 CDN에 호스팅 → 공식 API로 릴스 게시. **매 발행은 사람의 명시적 클릭 = 승인.**
자동 인터넷 게시·봇·자동 DM·자동 팔로우 없음.

### ⑧ Link-in-bio `/go`
**단일 bio 링크** 아래에 영상별 제휴 카드가 자동으로 쌓인다. bio는 한 번만 박고,
새 영상마다 카드만 prepend. 카드 = 썸네일 + 제휴 링크 + 제휴 고지.
이게 이 프로젝트의 칼끝: **영상 → /go 카드 → 제휴 전환**.

### ⑨ Metrics
조회/좋아요/댓글/저장/링크클릭/제휴클릭을 추적해 다음 정찰(①)로 환류한다.
발행 완료 콘텐츠는 작업판에서 빠지고 **성과 추적 보관함**으로 이동.

---

## 커머스 퍼널 (차별점)

```
 Reel  ──▶  /go (단일 bio 링크)  ──▶  Affiliate deep link  ──▶  구매(24h)  ──▶  수수료
            (영상별 카드 자동 누적)        (Coupang Partners HMAC)
```

`coupang_adapter`가 공식 Coupang Partners Open API(HMAC-SHA256)로 딥링크/상품검색을 처리하고,
결과를 `/go` 카드 데이터로 변환한다. 키는 `.env`만, mock/dry-run으로 키 없이 검증 가능.

---

## 가로지르는 시스템

| 시스템 | 역할 | repo 포함 |
|---|---|---|
| `secrets_audit` | 공개 전 민감정보 감사 (토큰 스캔·gitignore·공개/비공개 분류) | ✅ |
| `github_code_miner` | 오픈소스 부품 탐사 (별점+라이선스 판정, **패턴만·복사 금지**) | ✅ |
| `coupang_adapter` | 제휴 API 어댑터 (HMAC, `.env`-only) | ✅ |
| `.env` 모델 | 모든 키/토큰은 `.env`에서만, 코드 하드코딩 0 | ✅ (`.env.example`) |

### 외부 코드 흡수 원칙
GitHub 코드는 **복사하지 않는다.** 라이선스 확인 → 패턴만 참고 → 우리 코드로 새로 작성 → 출처 기록
(`data/mined_repos.json`). 쿠팡 관련 공개 repo는 라이선스가 없어 구조만 참고, 어댑터는 공식 문서 기준 100% 자체 작성.

---

## 공개 / 비공개 경계 (v0.1)

| 계층 | 상태 | 이유 |
|---|---|---|
| 철학 · 안전정책 · 라이선스 | 🟢 공개 | 프로젝트 정체성 |
| `coupang_adapter` · `github_code_miner` · `secrets_audit` | 🟢 공개 | 일반화된 핵심 부품 |
| Publisher · Mission Control(조종판) · Scout/Pack 오케스트레이터 | 🟡 보류 | 실경로·계정 흐름·팩 이름 포함 → sanitized 2차 공개 예정 |
| 운영 데이터 · 미디어 원본 · `.env` | ⚫ 비공개 | 민감/운영 자산, 영구 비공개 |

> 처음부터 공장 전체를 열지 않는다. 엔진룸 일부 + 안전 매뉴얼만 공개 → 점진적 sanitized 확장.

---

## 로드맵
1. ✅ v0.1 — 철학·안전·라이선스 + 핵심 부품 3종
2. `docs/ARCHITECTURE.md` (이 문서)
3. `examples/mock_coupang_flow/` — 키 없이 돌아가는 예제
4. sanitized `product_scout` 공개판
5. sanitized `mission_control`(조종판) 공개판
6. 사용 화면 캡처 / GIF

---

## Copyright
Copyright (c) 2026 투 성 / IGS AI 개발. Apache-2.0.
**Open source release does not mean copyright waiver.** See [LICENSE](../LICENSE) · [NOTICE](../NOTICE).
