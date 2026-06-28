# SAFETY POLICY — Reaction Commerce OS

이 도구는 **검증된 리액션 커머스 루프**(상품 정찰 → 쇼츠 패턴 → 감정 게이트 → 캐릭터 보이스
→ 영상 조립 → 발행 → 링크인바이오 → 제휴 전환)를 공개하기 위한 것입니다.
**스팸·자동 DM·무단 재업로드 도구가 아닙니다.** 공개·사용 전 이 정책을 반드시 따르세요.

## 1. 절대 공개 금지 (민감정보)
다음은 코드/공개 repo/커밋/이슈/스크린샷 어디에도 넣지 않습니다. **`.env`(gitignore) 또는 환경변수에서만** 읽습니다.
- Instagram / Graph API access token, IG user id
- Coupang Partners **access key / secret key**
- 실제 계정 인증정보(비밀번호, 세션, 쿠키)
- 실제 비공개 영상 원본 / 음성 원본 (`outputs/`, `voice_outputs/`, `visual_voice_sync/output/`, `*.mp4`)
- 남의 화면 원본 스샷 모음 (`captures/`, `pack_assets/`)
- 쿠팡/인스타 정책 우회·자동 팔로우·자동 DM·자동 구매/리뷰/댓글 코드 (애초에 만들지 않음)

검증: `python secrets_audit.py` → `verdict: SAFE` 여야 함. 결과는 `data/secrets_audit_report.json`.

## 2. 공개 가능 (엔진·구조)
- 파이프라인 코드(`.py`), 문서(`.md`), 템플릿, `.env.example`
- 사례는 **구조 중심**으로만(크록스/곰팡이 등 실제 링크·원본 미디어 제외)

## 3. 키 관리
- `.env.example`을 `.env`로 복사 후 본인 값 입력. `.env`는 `.gitignore` 됨.
- 토큰/키는 로그·출력·예외 메시지에 노출 금지(코드가 마스킹 처리).
- 공개 배포 시 하드코딩된 파트너스 코드(AF########)는 본인 값으로 교체하거나 `.env`로 이동.
  (현재 위치는 secrets_audit 리포트의 `af_hardcoded` 참고.)

## 4. 사용 금지 행위
- ❌ 자동 팔로우 / 자동 언팔 / 자동 DM / 연락처 업로드 — 플랫폼 차단·약관 위반
- ❌ 봇·대량 계정·스팸 발행
- ❌ 남의 영상/이미지 무단 재업로드 — 정찰/검수용만, 발행 소재는 직접 촬영/AI 재생성/사람 승인
- ❌ 쿠팡/인스타/유튜브 **스크래핑** — 공식 API 우선, 없으면 수동 입력
- ❌ 자동 구매 / 자동 리뷰 / 자동 댓글 / 계정 우회

## 5. 필수 준수
- ✅ **제휴 고지 필수**: 쿠팡 파트너스 문구를 게시물 첫머리/링크 페이지에 항상 표기
  ("쿠팡 파트너스 활동의 일환으로 일정액의 수수료를 제공받습니다.")
- ✅ **공식 API 우선**: Instagram Graph API(발행), Coupang Partners Open API(딥링크/검색)
- ✅ **발행은 사람**: 자동 인터넷 게시 없음. 버튼 클릭 = 그 건에 대한 명시적 승인
- ✅ 투자추천·수익보장 표현 금지

## 6. 공개 전 체크리스트
- [ ] `python secrets_audit.py` → `SAFE`
- [ ] `.env` 가 모든 repo의 `.gitignore`에 있음
- [ ] `outputs/`·`voice_outputs/`·`*.mp4`·원본 스샷이 gitignore 됨
- [ ] 공개 repo에는 `data/`의 운영 데이터(후보·세션·팔로우·발행 링크) 미포함 → 예시 데이터로 대체
- [ ] AF 파트너스 코드 = 본인 값/`.env`로 이동
- [ ] `README` 에 본 정책 링크
