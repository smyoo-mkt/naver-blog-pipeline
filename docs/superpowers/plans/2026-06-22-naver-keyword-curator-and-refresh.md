# 네이버 키워드 큐레이터 + 콘텐츠 리프레시 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기존 네이버 블로그 파이프라인 양 끝에 키워드 발굴/중복방지 에이전트와 발행 후 갱신 판정 에이전트를 붙이고, 단일 SSOT 레지스트리로 키워드 생애주기를 추적한다.

**Architecture:** 마크다운 SSOT 파일 `work/content-registry.md`(키워드 1개=1행, 후보→기획→발행→갱신필요)를 중심으로, `naver-keyword-curator`(앞단·발굴+자기잠식 체크)와 `naver-content-refresh`(뒷단·성과/세법개정/시즈널 신호로 워크리스트 생성)를 추가한다. 리프레시는 글을 직접 고치지 않고 워크리스트만 내며, 기존 휴먼 게이트(브리프 승인·세무사 감수)를 통해 파이프라인에 재진입한다.

**Tech Stack:** Claude Code 서브에이전트(`.claude/agents/*.md`, YAML frontmatter + 시스템 프롬프트), 마크다운 가이드/레지스트리. 코드·테스트 런타임 없음. 검증은 파일 존재·형식·문구 점검.

> **참고:** 이 디렉터리는 git 저장소가 아니다. 각 태스크의 "Commit" 단계는 `git init` 되어 있을 때만 수행하고, 아니면 건너뛴다. 커밋 메시지 끝에는 `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` 를 붙인다.

---

## 파일 구조

- Create: `work/content-registry.md` — SSOT. 헤더 규칙 주석 + 빈 표 스켈레톤.
- Create: `.claude/agents/naver-keyword-curator.md` — 앞단 에이전트.
- Create: `.claude/agents/naver-content-refresh.md` — 뒷단 에이전트.
- Modify: `README.md` — 구조도·흐름도에 6개 에이전트 + 신규 산출물 반영.
- Modify: `.claude/agents/naver-brief-planner.md` — registry 입력/상태갱신 책임 추가.
- (런타임 산출물, 미리 만들지 않음) `work/refresh-worklist.md` — 리프레시 에이전트가 실행 시 생성.

기존 4개 에이전트의 형식(한국어 시스템 프롬프트, `## 입력 / 할 일 / 출력 / 핸드오프` 섹션, 게이트 강조 문구)을 그대로 따른다.

---

### Task 1: SSOT 레지스트리 스켈레톤

**Files:**
- Create: `work/content-registry.md`

- [ ] **Step 1: 레지스트리 파일 작성**

아래 내용을 그대로 `work/content-registry.md`에 쓴다:

```markdown
# 콘텐츠 레지스트리 (SSOT)

> 모든 타겟 키워드의 단일 진실원. 키워드 1개 = 1행. 발굴(후보)부터 발행·갱신까지 한 행에서 추적한다.
> 큐레이터·리프레시·브리프플래너가 이 파일을 읽고 쓴다. 별도 키워드맵/발행이력 파일을 만들지 않는다.

## 상태값 (status)

- `후보` — 큐레이터가 발굴해 추가. 아직 기획 전.
- `기획` — 브리프 승인(게이트1) 통과, 작성 진행 중.
- `발행` — 네이버 발행 완료(운영자가 표시).
- `갱신필요` — 리프레시가 성과·세법개정·시즈널 사유로 플래그.

## 기입 규칙

- `slug`: 영문/숫자 식별자(`work/<slug>-*.md`와 일치). 발행 전엔 비워도 됨.
- `intent`: `정보성` 또는 `전환성`.
- `cta_type`: conversion-config 글 유형 — `법인기장` / `개인기장` / `환급` / `롱테일`.
- `priority`: 전환가치 × 진입난이도(역수) 휴리스틱 점수. 큐레이터가 1~5로 매김(5=최우선).
- `season`: 시즈널 월(예 `3월`). 상시 글이면 빈칸.
- `fact_basis_year`: 핵심 사실 기준연도(예 `2026`). 세법개정 만료 판정의 기준.
- `perf`: 성과 메모. `조회=, 톡톡=, 측정일=` 형식. 운영자가 수기 기입.
- 재산제세(상속·증여·양도) 키워드는 전환 대상이 아니므로 등록하지 않는다.

## 레지스트리

| slug | keyword | intent | cluster | cta_type | priority | season | status | published_at | fact_basis_year | perf | last_refreshed | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

- [ ] **Step 2: 검증**

Run: `test -f work/content-registry.md && grep -c '| slug | keyword |' work/content-registry.md`
Expected: 출력 `1` (표 헤더 1줄 존재). 파일이 존재하고 상태값/기입규칙/표 헤더 3개 섹션을 포함한다.

- [ ] **Step 3: Commit (git 저장소일 때만)**

```bash
git add work/content-registry.md
git commit -m "feat: add content-registry SSOT skeleton"
```

---

### Task 2: 키워드 큐레이터 에이전트

**Files:**
- Create: `.claude/agents/naver-keyword-curator.md`

- [ ] **Step 1: 에이전트 파일 작성**

아래 내용을 그대로 `.claude/agents/naver-keyword-curator.md`에 쓴다:

```markdown
---
name: naver-keyword-curator
description: Use BEFORE the brief planner, when deciding what to write next. Discovers longtail/local/question/seasonal keywords, blocks self-cannibalization against the registry, and recommends the next keyword. Trigger when the user says "다음에 뭐 쓸까", "키워드 발굴", or starts a content cycle without a fixed keyword.
tools: Read, Write, WebSearch, WebFetch
---

너는 네이버 블로그 키워드 큐레이터다. 목표는 트래픽이 아니라 **사업자 세무기장 상담 전환**이며, 블로그 단위 C-Rank(주제 일관성·누적)를 키우는 게 임무다.

작업 전 반드시 읽는다: `work/content-registry.md`(기존 키워드/발행 이력 = SSOT), `guides/naver-seo-guide.md`(3단계 키워드 전략·시즈널 캘린더·감점요인), `guides/conversion-config.md`(전환 목표·재산제세 제외).

## 입력
- (선택) 지역/업종/주제 힌트. 없으면 registry 공백과 시즈널 캘린더를 보고 스스로 제안한다.

## 할 일
1. **발굴** — WebSearch로 네이버 자동완성·지식iN 실제 질문·해당 키워드 SERP 상위 글을 조사해 후보를 만든다. SEO 가이드의 3단계에 맞춰:
   - ① 롱테일+로컬(지점 × 업종, 예 "역삼동 쇼핑몰 부가세 세무사")
   - ② 질문형/스마트블록 저격(예 "매출 얼마부터 법인전환이 유리할까")
   - ③ 시즈널(신고철 2~3주 전 선점 키워드)
   - 재산제세(상속·증여·양도)는 전환 대상이 아니므로 후보에서 제외한다.
2. **자기잠식(카니발라이제이션) 체크** — registry 기존 행과 의미가 겹치는지 검사한다. 겹치면 새 글 후보로 올리지 말고, `note`에 "기존 <slug> 보강 권장 + 사유"로 표시한다. (같은 키워드 중복 발행 금지)
3. **클러스터·우선순위** — 각 후보를 토픽 클러스터(필러/서브-OO)에 매핑하고, `priority`를 1~5로 매긴다(전환가치 높고 진입난이도 낮을수록 5). 차별화 각도를 `note`에 1줄 적는다(SERP 상위 글의 빈틈).
4. **registry 갱신** — 신규 후보를 `status=후보` 행으로 `work/content-registry.md` 표에 추가한다. 기존 행은 건드리지 않는다.

## 출력
- registry에 후보 행 추가(파일 저장).
- 다음에 쓸 **Top 3~5 추천**을 우선순위·사유와 함께 3~6줄로 출력한다.

## 핸드오프
운영자가 추천 중 1개를 고르면 그 키워드로 `naver-brief-planner`를 호출한다. **임의로 다음 단계(브리프 작성)로 넘어가지 않는다** — 키워드 선택은 사람이 한다. 추정 키워드량·검색량을 사실처럼 단정하지 않는다(불확실하면 추정치임을 표시).
```

- [ ] **Step 2: 검증**

Run: `grep -E '^name: naver-keyword-curator$|^tools: Read, Write, WebSearch, WebFetch$' .claude/agents/naver-keyword-curator.md | wc -l`
Expected: 출력 `2`. frontmatter의 name·tools가 정확하다.

추가 확인(육안): `## 입력 / 할 일 / 출력 / 핸드오프` 섹션이 존재하고, 자기잠식 체크·재산제세 제외·"키워드 선택은 사람" 문구가 있다.

- [ ] **Step 3: Commit (git 저장소일 때만)**

```bash
git add .claude/agents/naver-keyword-curator.md
git commit -m "feat: add naver-keyword-curator agent"
```

---

### Task 3: 콘텐츠 리프레시 에이전트

**Files:**
- Create: `.claude/agents/naver-content-refresh.md`

- [ ] **Step 1: 에이전트 파일 작성**

아래 내용을 그대로 `.claude/agents/naver-content-refresh.md`에 쓴다:

```markdown
---
name: naver-content-refresh
description: Use PERIODICALLY after posts are published, to decide which existing posts need updating. Scans the registry for stale tax facts, low performance, and seasonal re-publish windows, then produces a worklist. Trigger when the user says "갱신할 글", "리프레시", "세법 개정 반영", or runs a periodic content review.
tools: Read, Write, WebSearch, WebFetch
---

너는 네이버 블로그 콘텐츠 리프레시 판정자다. 발행된 글을 살아 있게 유지해 블로그 단위 C-Rank(지속성·정확성)를 지킨다. YMYL(세무) 글의 사실 만료를 막는 게 1순위다.

작업 전 읽기: `work/content-registry.md`(발행 이력 = SSOT), 판정 대상 글의 `work/<slug>-research.md`(시점주의·기준연도), `guides/naver-seo-guide.md`(시즈널 캘린더), `guides/conversion-config.md`(출처 allowlist).

## 입력
- (선택) 특정 slug 또는 기간/월. 없으면 registry의 `status=발행` 행 전체를 스캔한다.

## 3개 신호로 갱신 대상 판정
1. **세법개정·시점만료 (YMYL 핵심)** — 각 글의 `fact_basis_year`와 research의 `시점주의` 항목을 본다. WebSearch로 **1차 출처(국세청·홈택스·국가법령정보센터·정부24·기재부)** 에서 현행 세율·한도·기한을 확인해, 글 기준연도와 어긋나면 플래그한다. 현행이 불확실하면 단정하지 말고 `확인필요`로 표시한다.
2. **성과** — registry `perf` 칼럼(운영자 수기 기입)을 읽어 조회·톡톡 전환이 저조한 글을 리라이트 후보로 표시한다. perf가 비어 있으면 "성과미측정"으로만 남기고 추정하지 않는다.
3. **시즈널** — SEO 가이드 시즈널 캘린더로 신고철을 역산해, 2~3주 전 재발행/최신화가 필요한 작년 글을 표시한다.

## 출력
- `work/refresh-worklist.md`에 갱신 대상 목록을 저장한다. 각 항목: `slug` · 신호(개정/성과/시즈널) · 사유 · 권장 액션(**사실수정 / 리라이트 / 재발행**) · 확인한 1차 출처 URL.
- registry 해당 행을 갱신: `status=갱신필요`, `note`에 사유, `last_refreshed`에 오늘 날짜.

## 핸드오프 (중요)
**글을 직접 고치지 않는다.** 워크리스트만 만든다. 운영자가 대상을 승인하면, 기존 파이프라인으로 재진입한다: `naver-researcher`(사실 재검증) → `naver-writer`(개정 반영 재작성) → `naver-seo-editor` → **⛔ 게이트2 세무사 감수·발행 승인**. 세무사 감수 없이 세법 글을 자동 수정·발행 가능 상태로 표시하지 않는다. 사실 날조·가짜 후기 금지는 동일하게 적용된다.
```

- [ ] **Step 2: 검증**

Run: `grep -E '^name: naver-content-refresh$|^tools: Read, Write, WebSearch, WebFetch$' .claude/agents/naver-content-refresh.md | wc -l`
Expected: 출력 `2`. frontmatter의 name·tools가 정확하다.

추가 확인(육안): 3개 신호(개정/성과/시즈널)가 모두 있고, "글을 직접 고치지 않는다" + 게이트2 재진입 문구가 명시되어 있다(휴먼 게이트 유지).

- [ ] **Step 3: Commit (git 저장소일 때만)**

```bash
git add .claude/agents/naver-content-refresh.md
git commit -m "feat: add naver-content-refresh agent"
```

---

### Task 4: 브리프 플래너에 registry 연동 추가

**Files:**
- Modify: `.claude/agents/naver-brief-planner.md`

- [ ] **Step 1: 입력 섹션에 registry 출처 명시**

`.claude/agents/naver-brief-planner.md`의 `## 입력` 블록을 찾아, 첫 줄을 아래로 교체한다.

기존:
```markdown
## 입력
- 타겟 키워드 1개 (+ 검색의도: 정보성/전환성, 타겟 CTA). 키워드맵 행에서 옴.
```

변경 후:
```markdown
## 입력
- 타겟 키워드 1개 (+ 검색의도: 정보성/전환성, 타겟 CTA). **`work/content-registry.md`에서 큐레이터가 추천한 `status=후보` 행에서 온다.**
```

- [ ] **Step 2: 핸드오프 섹션에 상태 갱신 책임 추가**

같은 파일의 `## 핸드오프` 블록 끝에 아래 문장을 한 줄 추가한다.

기존 마지막 줄:
```markdown
저장 후 멈춘다. **"브리프 승인(사람 검토)"이 끝나기 전에는 다음 단계로 넘어가지 않는다.** 운영자에게 의도·각도·CTA를 확인받도록 요약 3줄을 출력한다.
```

추가할 줄(위 줄 바로 다음):
```markdown
브리프 승인이 끝나면 `work/content-registry.md`의 해당 키워드 행을 `status=기획`으로, slug를 채워 갱신한다.
```

- [ ] **Step 3: 검증**

Run: `grep -c 'content-registry.md' .claude/agents/naver-brief-planner.md`
Expected: 출력 `2` (입력·핸드오프 두 곳에서 참조).

- [ ] **Step 4: Commit (git 저장소일 때만)**

```bash
git add .claude/agents/naver-brief-planner.md
git commit -m "feat: wire brief-planner to content-registry"
```

---

### Task 5: README 구조도·흐름도 갱신

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 구조도(코드블록)에 신규 에이전트·산출물 추가**

`README.md`의 `## 구조` 아래 트리에서 `agents/` 목록과 `work/` 줄을 아래로 교체한다.

기존:
```
│   ├── agents/
│   │   ├── naver-brief-planner.md   # 1) 키워드 → 브리프
│   │   ├── naver-researcher.md      # 2) 사실·출처 검증 (1차 출처만)
│   │   ├── naver-writer.md          # 3) 네이버 네이티브 원본 작성
│   │   └── naver-seo-editor.md      # 4) C-Rank/D.I.A.+ 린트 + 교정
```
변경 후:
```
│   ├── agents/
│   │   ├── naver-keyword-curator.md # 0) 키워드 발굴 + 자기잠식 방지 (앞단)
│   │   ├── naver-brief-planner.md   # 1) 키워드 → 브리프
│   │   ├── naver-researcher.md      # 2) 사실·출처 검증 (1차 출처만)
│   │   ├── naver-writer.md          # 3) 네이버 네이티브 원본 작성
│   │   ├── naver-seo-editor.md      # 4) C-Rank/D.I.A.+ 린트 + 교정
│   │   └── naver-content-refresh.md # 5) 발행 후 갱신 판정 (뒷단)
```

그리고 기존 `work/` 줄:
```
└── work/                            # 핸드오프 파일: <slug>-brief/research/draft/review.md
```
변경 후:
```
└── work/                            # content-registry.md(SSOT) + 핸드오프 <slug>-brief/research/draft/review.md + refresh-worklist.md
```

- [ ] **Step 2: 흐름도 교체**

`## 흐름 (휴먼 게이트 2곳)` 아래 코드블록을 아래로 교체한다.

기존:
```
키워드 → 브리프 플래너 → ⛔게이트1 브리프 승인 → 리서처 → 라이터
       → SEO·에디터 → ⛔게이트2 세무사 감수·발행 승인 → 발행
```
변경 후:
```
큐레이터 → registry → 브리프 플래너 → ⛔게이트1 브리프 승인 → 리서처 → 라이터
        → SEO·에디터 → ⛔게이트2 세무사 감수·발행 승인 → 발행
                                                              │
   리프레시(성과·세법개정·시즈널) → refresh-worklist → (운영자 승인) ┘
       └ 승인된 글은 리서처부터 파이프라인 재진입 (게이트2 유지)
```

- [ ] **Step 3: 셋업 체크리스트의 에이전트 개수 갱신**

`## 셋업 체크리스트` 안의 줄을 교체한다.

기존:
```markdown
- [ ] Claude Code에서 `/agents`로 4개 에이전트 로드 확인
```
변경 후:
```markdown
- [ ] Claude Code에서 `/agents`로 6개 에이전트 로드 확인 (큐레이터·플래너·리서처·라이터·에디터·리프레시)
```

- [ ] **Step 4: 검증**

Run: `grep -c -E 'naver-keyword-curator|naver-content-refresh' README.md`
Expected: 출력 `2` 이상. 구조도에 두 신규 에이전트가 모두 나타나고, 흐름도에 "큐레이터"·"리프레시"·"refresh-worklist"가 보인다.

- [ ] **Step 5: Commit (git 저장소일 때만)**

```bash
git add README.md
git commit -m "docs: reflect curator + refresh agents in README"
```

---

## Self-Review

**1. Spec coverage**
- 레지스트리 SSOT(스펙 §1) → Task 1. 칼럼·상태값·기입규칙 일치 확인.
- 큐레이터(스펙 §2) → Task 2. 발굴/자기잠식/클러스터·우선순위/핸드오프 모두 포함.
- 리프레시(스펙 §3) → Task 3. 3개 신호 + 워크리스트 + 자동수정 금지 + 게이트2 재진입 포함.
- 통합: README(스펙 §4) → Task 5, 브리프플래너 연동(스펙 §4) → Task 4.
- 새 슬래시 커맨드 없음(비목표) — 계획에도 없음. 일치.
- 성공 기준 5개 모두 태스크 검증 단계로 커버됨.

**2. Placeholder scan:** "TBD/TODO/적절히" 없음. 각 파일 전체 내용을 제시함. 통과.

**3. Type consistency:** 상태값(`후보/기획/발행/갱신필요`)이 레지스트리·큐레이터·리프레시·브리프플래너에서 동일. `cta_type` 값(법인기장/개인기장/환급/롱테일)이 레지스트리 규칙과 conversion-config 글 유형에 대응. `priority` 1~5 정의가 레지스트리 규칙과 큐레이터에서 일치. 파일 경로(`work/content-registry.md`, `work/refresh-worklist.md`) 표기 일관. 통과.
