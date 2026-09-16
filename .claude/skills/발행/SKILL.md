---
name: 발행
description: 인스타 자동 발행. 캡션까지 끝난 세트를 자동예약.py가 랜덤 시각(06:00~08:30 / 15:00~18:00)으로 예약표에 넣고, 이미지·예약표는 Cloudflare R2에 올린다. Cloudflare Worker 크론(45분)이 시간 맞춰 Make 웹훅으로 발행하고 24시간 뒤 R2에서 지운다. 깃허브 안 씀. 사람 검수 없음.
---

# 발행 (전자동 — 사람 검수 없음, 2026-09-16 사용자 지시 / 2026-09-17 깃허브 → Cloudflare Worker로 교체)

**시작 전 관문: `.claude/skills/지침/SKILL.md` 를 읽고 `지침확인: 한 줄` 을 적은 뒤 진행한다. 이 줄 없이 한 작업은 무효 (지침 5절).**

## 흐름

1. 캡션작성이 끝난 폴더마다 실행: `python 작업파일/자동예약.py <제작폴더명>`
2. 자동예약.py가 시각을 뽑는다 — 오전 06:00~08:30 / 오후 15:00~18:00 두 창, 창마다 하루 1건(하루 최대 2건), 창 고르는 순서는 날마다 랜덤, 창 안 분 단위 랜덤. 자리 없으면 다음 날로 넘어간다(최대 2주). 제작은 루틴이 하루 1건·2건 번갈아 만든다
3. 이어서 크롬 PNG 촬영 → JPEG 변환 → **R2 업로드**(`insta-cards/폴더명/` 접두어, babcheck-img 버킷) → **예약표 `insta-cards/예약.json`에 한 건(시각·캡션·이미지 주소 전부 포함) 추가해 R2에 올림.** 깃허브 푸시 없음
4. **Cloudflare Worker**(같은 계정 bobomusic83, Cron Trigger `0,45 * * * *`)가 매시 :00·:45에 깨서 예약.json에서 시간 지난 건을 발행한다: R2에서 이미지 받아 base64 → Make 웹훅 전송. PC 꺼져 있어도 돈다
   - 크론은 "정확히 45분마다"가 안 된다. :00·:45라 실제 간격은 45분·15분이 번갈아 온다. 예약 시각보다 최대 45분 늦게 나갈 수 있다 (사용자 확정 2026-09-17: 15분마다 깨우지 말 것)
5. Make 시나리오 `instagram_publish`: 웹훅 → Iterator → 구글 드라이브 업로드 → 공유 링크 → Array aggregator → Instagram 캐러셀 게시
6. 성공 시 Worker가 R2의 `insta-cards/발행대장.txt`에 한 줄, 실패 시 `insta-cards/오류기록.txt`에 한 줄 추가. 확인서버 현황판이 이 두 파일을 받아와 로컬 발행대장·오류기록과 합쳐 보여준다
7. 발행(성공·실패 무관) **24시간 뒤** Worker가 그 세트의 R2 이미지를 지운다 (예약.json 안의 삭제예정 시각 기준)

보내는 JSON 모양 (Make 쪽 필드명과 맞춰져 있음. 바꾸면 양쪽 다 바꿔야 함):
`{"caption": 캡션, "count": 장수, "images": [{"name": "카드01.jpg", "data": base64}, ...]}`

## 저장소·비밀값

- R2 (PC 쪽): 사용자 환경변수 `R2_ACCESS_KEY_ID`·`R2_SECRET_ACCESS_KEY`·`R2_BUCKET`(babcheck-img)·`R2_PUBLIC_URL`·`CLOUDFLARE_ACCOUNT_ID_2`(bobomusic83). `insta-cards/` 접두어 밖은 코드가 못 지우게 막음
- Worker 쪽: R2는 바인딩으로 직접 붙임(키 불필요). 비밀값은 `MAKE_WEBHOOK` 하나만 Worker Secret에 등록 (`wrangler secret put MAKE_WEBHOOK`). 웹훅 주소는 파일에 적지 않는다
- Worker 코드·설정: `작업파일/worker/` (wrangler.toml + index.js). 배포는 `wrangler deploy`
- 깃허브 저장소(koii0803/insta-cardnews1)·액션·Secrets는 더 안 쓴다. 남아 있는 옛 예약이 다 나간 뒤 워크플로 파일 삭제

## 수동 발행 (예외 상황용)

- 최종확인 화면(`전체확인열기.bat`)의 발행/PC예약/자동예약 버튼은 그대로 살아 있다. PC 즉시 발행은 `작업파일/webhook.txt` 주소를 쓴다
- 예약 버튼도 R2 예약표 경로로 돈다

## 확인할 것

- 인스타에 게시가 안 보이면: Cloudflare 대시보드 → Workers → 해당 Worker → Logs에서 크론 실행이 초록인지 → Make 시나리오 히스토리에서 어느 모듈이 빨간지
- 급하면 Worker의 수동 실행 주소(`/run`, 토큰 필요)를 호출한다
- 카드 한 세트 약 0.5MB, 4.5MB 넘으면 전송 막힘 (카드 10장 이상이면 확인)
- Make 무료 한도 월 1,000 작업. 4장 세트 = 12 작업. 하루 1·2건 격일(월 45건)이면 월 약 540 작업 — 무료 한도 안
- Workers 무료: 하루 10만 요청. 크론 하루 32번이라 한참 남는다
- R2 무료: 저장 10GB — 세트당 0.5MB에 24시간 뒤 삭제라 늘 거의 비어 있다

## 아직 남은 것

- 카드 하단 `@계정명` 자리표시자 교체 (계정명 확정 후)
- Worker 코드 작성·배포 + MAKE_WEBHOOK 시크릿 등록 (코드는 사용자 승인 후)
- 자동예약.py·확인서버.py를 깃허브 푸시 → R2 예약표로 바꾸기 (코드는 사용자 승인 후)
