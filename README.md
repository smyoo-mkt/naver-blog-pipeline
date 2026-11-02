# 네이버 블로그 콘텐츠 파이프라인 (세무기장 전환 전용)

heumtax 파이프라인과 **완전히 분리된** 네이버 전용 멀티에이전트 세트. 트래픽이 아니라 **사업자 세무기장 상담 전환**을 목표로 한다. (재산제세는 전환 대상 아님)

## 구조

```
naver-blog-pipeline/
├── .claude/
│   ├── agents/
│   │   ├── naver-keyword-curator.md # 0) 키워드 발굴 + 자기잠식 방지 (앞단)
│   │   ├── naver-brief-planner.md   # 1) 키워드 → 브리프
│   │   ├── naver-editorial-planner.md # 1.5) 발행 캘린더 + 내부링크 그래프
│   │   ├── naver-researcher.md      # 2) 사실·출처 검증 (1차 출처만)
│   │   ├── naver-writer.md          # 3) 네이버 네이티브 원본 작성
│   │   ├── naver-seo-editor.md      # 4) C-Rank/D.I.A.+ 린트 + 교정
│   │   └── naver-content-refresh.md # 5) 발행 후 갱신 판정 (뒷단)
│   └── commands/
│       ├── naver-api.md             # 수요 실측: /naver-api <키워드> (큐레이터 앞단)
│       └── naver-post.md            # 오케스트레이터: /naver-post <키워드>
├── scripts/
│   └── naver-data.py                # 네이버 API 래퍼 (검색광고·블로그·카페·지식iN·DataLab·자동완성)
├── guides/
│   ├── naver-seo-guide.md           # C-Rank·D.I.A.+·역피라미드·3단계 키워드·시즌·감점요인
│   ├── naver-style-guide.md         # 1인칭 전문가 톤·구조 템플릿·제목·CTA 문구
│   └── conversion-config.md         # CTA/UTM·바이라인·출처 allowlist·복제금지
└── work/                            # content-registry.md(SSOT) + editorial-plan.md + 핸드오프 <slug>-brief/research/draft/review.md + refresh-worklist.md
```

## 흐름 (휴먼 게이트 2곳)

```
큐레이터 → registry → 브리프 플래너 → ⛔게이트1 브리프 승인 → 리서처 → 라이터
        → SEO·에디터 → ⛔게이트2 세무사 감수·발행 승인 → 발행
                                                              │
   리프레시(성과·세법개정·시즈널) → refresh-worklist → (운영자 승인) ┘
       └ 승인된 글은 리서처부터 파이프라인 재진입 (게이트2 유지)
```

게이트 2는 YMYL 필수 관문이다. 세무사가 ① 사실 정확성 확인 ② `[세무사 사례 삽입]` 실제 사례 채우기 ③ 과장표현 제거를 끝내야 발행한다. AI는 세율·기한을 만들어내거나 가짜 후기를 쓰지 않는다.

## 사용법

```
/naver-api  법인 기장료          # ① 수요 실측 → work/<slug>-keyword-data.md
/naver-post 역삼동 쇼핑몰 부가세 세무사   # ② 기획~발행 파이프라인
```

또는 명시 호출: `naver-brief-planner 서브에이전트로 "법인 기장 비용" 글 기획해줘`

### /naver-api — 수요 실측 (추정 금지)

키워드를 고르기 **전에** 돌린다. 답하는 질문 4개: ① 사람들이 어떤 문구로 검색하는가
② 그 문구가 실제 검색되는 문구인가(조합어 판별) ③ 실제로 무엇을 묻는가(지식iN·카페 원문)
④ 그 니즈가 수임으로 이어지는가(conversion-config 실측 수임률 매핑).

문구 실존 판정은 **DataLab 비영개월 + 자동완성 개수**로 한다. 문서수는 형태소 광의매칭이라 근거가 못 된다 —
`법인 세무기장 위탁 절차 안내`는 아무도 검색하지 않는데 블로그 문서수가 891건 나온다.

```
python3 scripts/naver-data.py exists "법인 기장료" "법인 세무기장 위탁 절차 안내"
```

산출물은 큐레이터·브리프플래너가 물려 쓰는 SSOT다. **이 수치를 추정으로 덮어쓰지 않는다.**

## 셋업 체크리스트 (발행 전)

- [ ] `guides/conversion-config.md`의 바이라인 레지스트리를 실제 세무사 정보로 교체
- [ ] CTA 링크(톡톡/무료진단/더낸세금)와 UTM 베이스 URL 확정
- [ ] 키워드맵 xlsx를 옆에 두고 입력 키워드 선택 (롱테일+로컬 우선)
- [ ] Claude Code에서 `/agents`로 7개 에이전트 로드 확인 (큐레이터·브리프플래너·에디토리얼플래너·리서처·라이터·에디터·리프레시)

> 서브에이전트/커맨드 형식은 `.claude/agents/`·`.claude/commands/` 마크다운(YAML frontmatter + 시스템 프롬프트) 기준이다. 사용 중인 Claude Code 버전에서 `/agents`로 인식되는지 한 번 확인할 것. 모델은 frontmatter에 `model:`로 에이전트별 지정 가능(미지정 시 메인 세션 상속).
