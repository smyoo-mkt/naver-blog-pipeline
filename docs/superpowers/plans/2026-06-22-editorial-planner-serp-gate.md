# 에디토리얼 플래너 + SERP 분석 + 감수 양식 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 블로그 단위 구조(발행 캘린더 + 내부링크 그래프) 에이전트를 추가하고, 브리프 단계에 SERP 경쟁 분석을, 감수 게이트에 세무사 기입 양식을 더한다.

**Architecture:** 신규 `naver-editorial-planner`가 registry·발행물을 읽어 `work/editorial-plan.md`(캘린더 + 내부링크 그래프)를 제안한다(초안 직접 수정 안 함). 기존 brief-planner에 SERP 분석 단계를, seo-editor에 내부링크 검증 강화 + 세무사 기입란 첨부를 더한다. 모든 변경은 휴먼 게이트를 유지한다.

**Tech Stack:** Claude Code 서브에이전트(`.claude/agents/*.md`), 마크다운. 코드·테스트 런타임 없음. 검증은 파일 존재·형식·문구 점검.

> **참고:** 이 디렉터리는 git 저장소가 아니다. "Commit" 단계는 `git init` 되어 있을 때만 수행한다. 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

---

## 파일 구조

- Create: `.claude/agents/naver-editorial-planner.md` — 발행 캘린더 + 내부링크 그래프 제안.
- Modify: `.claude/agents/naver-brief-planner.md` — SERP 경쟁 분석 단계 + 차별화 각도 출력.
- Modify: `.claude/agents/naver-seo-editor.md` — 내부링크 검증 강화 + 세무사 기입란 첨부.
- Modify: `README.md` — 7개 에이전트 + `editorial-plan.md` 반영.
- (런타임 산출물) `work/editorial-plan.md` — 에디토리얼 플래너가 실행 시 생성.

---

### Task 1: 에디토리얼 플래너 에이전트

**Files:**
- Create: `.claude/agents/naver-editorial-planner.md`

- [ ] **Step 1: 에이전트 파일 작성**

아래 내용을 그대로 `.claude/agents/naver-editorial-planner.md`에 쓴다:

```markdown
---
name: naver-editorial-planner
description: Use to plan blog-level structure — the publishing calendar and internal-link graph across posts. Trigger when the user says "발행 일정", "에디토리얼 캘린더", "내부링크 정리", or after several keywords/posts accumulate in the registry.
tools: Read, Write
---

너는 네이버 블로그 에디토리얼 플래너다. 글 1편이 아니라 **블로그 전체 구조**(발행 리듬·시즈널 선점·클러스터 내부링크)를 설계해 C-Rank를 키운다.

작업 전 읽기: `work/content-registry.md`(키워드/발행 이력 = SSOT), 기존 `work/*-draft.md`·`*-review.md`(발행물 본문), `guides/naver-seo-guide.md`(시즈널 캘린더·C-Rank 지속성).

## 입력
- (선택) 기준 월 또는 특정 클러스터. 없으면 registry 전체를 본다.

## 할 일 — 출력은 `work/editorial-plan.md` 한 파일, 두 섹션
1. **발행 캘린더**
   - registry의 `status=후보/기획` 행과 `season` 값, SEO 가이드 시즈널 캘린더를 대조한다.
   - 시즈널 글은 신고철 **2~3주 전** 발행되도록 역산해 배치한다.
   - 주 3~5회 일정한 리듬(C-Rank 지속성)을 고려해 발행 순서를 제안한다(몰아쓰기 금지).
   - 표로 출력: `주차/월 · slug 또는 keyword · 사유(시즈널/우선순위)`.
2. **내부링크 그래프**
   - registry `cluster`별로 발행물(`status=발행`)을 묶어 **필러↔서브** 링크 관계를 제안한다.
   - 작성 중인 초안이 있으면, 그 글의 `[내부링크: ...]` 자리에 넣을 **구체적 slug/제목**을 추천한다(같은 클러스터 우선).
   - 표로 출력: `출발 slug → 도착 slug · 관계(필러→서브/서브→필러/형제)`.

## 핸드오프
**초안을 직접 수정하지 않는다.** `work/editorial-plan.md` 제안만 낸다. 라이터/에디터가 이 파일을 참고해 `[내부링크: ...]`를 채운다. registry에 없는 글이나 미발행 글을 발행물처럼 단정하지 않는다.
```

- [ ] **Step 2: 검증**

Run: `grep -E '^name: naver-editorial-planner$|^tools: Read, Write$' .claude/agents/naver-editorial-planner.md | wc -l | tr -d ' '`
Expected: 출력 `2`. frontmatter의 name·tools 정확.

추가 확인(육안): `발행 캘린더`·`내부링크 그래프` 두 섹션, "초안을 직접 수정하지 않는다" 문구 존재.

- [ ] **Step 3: Commit (git 저장소일 때만)**

```bash
git add .claude/agents/naver-editorial-planner.md
git commit -m "feat: add naver-editorial-planner agent"
```

---

### Task 2: 브리프 플래너에 SERP 경쟁 분석 추가

**Files:**
- Modify: `.claude/agents/naver-brief-planner.md`

- [ ] **Step 1: 할 일에 SERP 분석 단계 추가**

`.claude/agents/naver-brief-planner.md`에서 아래 줄을 찾는다:

```markdown
2. 1차/2차 키워드 선정. SEO 가이드의 3단계 전략에 따라 롱테일·로컬·질문형 변형을 함께 제안.
```

그 줄 바로 다음에 새 줄을 삽입한다(번호는 그대로 두고 한 항목 추가):

```markdown
2-1. **SERP 경쟁 분석.** 타겟 키워드를 WebSearch해 네이버 상위 글을 살핀다. 상위 글이 공통으로 다루는 소재와 **빠진 각도(우리가 다르게 갈 차별화 지점)** 를 정리한다.
```

- [ ] **Step 2: 출력에 차별화 각도 섹션 추가**

같은 파일의 아래 줄을 찾는다:

```markdown
`work/<slug>-brief.md`에 위 항목을 구조화해 저장. slug는 키워드 기반 영문/숫자.
```

그 줄 바로 앞에 새 줄을 삽입한다:

```markdown
출력에 `경쟁 글 분석 + 차별화 각도` 섹션을 포함한다(상위 글 요지 3줄 + 우리가 다르게 갈 지점).
```

- [ ] **Step 3: 검증**

Run: `grep -c -E 'SERP 경쟁 분석|차별화 각도' .claude/agents/naver-brief-planner.md | tr -d ' '`
Expected: 출력 `2` 이상. 기존 registry 연동 줄(`content-registry.md` 2회)·게이트1 문구는 그대로 유지되었는지 육안 확인.

- [ ] **Step 4: Commit (git 저장소일 때만)**

```bash
git add .claude/agents/naver-brief-planner.md
git commit -m "feat: add SERP competitive analysis to brief-planner"
```

---

### Task 3: SEO 에디터 — 내부링크 검증 강화 + 세무사 기입란 첨부

**Files:**
- Modify: `.claude/agents/naver-seo-editor.md`

- [ ] **Step 1: 내부링크 체크 항목 강화**

`.claude/agents/naver-seo-editor.md`에서 아래 줄을 찾는다:

```markdown
- [ ] 내부링크 자리 존재
```

아래로 교체한다:

```markdown
- [ ] 내부링크가 `work/editorial-plan.md`의 클러스터 관계대로 채워짐 (editorial-plan 없으면 자리 존재만 확인)
```

- [ ] **Step 2: 작업 섹션에 세무사 기입란 첨부 지시 추가**

같은 파일에서 아래 줄을 찾는다:

```markdown
- 교정본 + 체크리스트 결과를 `work/<slug>-review.md`로 저장.
```

아래로 교체한다:

```markdown
- 교정본 + 체크리스트 결과를 `work/<slug>-review.md`로 저장.
- review.md 맨 아래에 **세무사 감수 기입란**을 그대로 첨부한다(게이트2에서 세무사가 칸을 채운다):

  ```
  ## 세무사 감수란 (발행 전 필수)
  ① 사실 정확성: 핵심 사실 항목별 확인
     - [ ] 항목1 OK / 수정:____
     - [ ] 항목2 OK / 수정:____
  ② 실제 사례: 본문 `[세무사 사례 삽입]` 자리에 실제 사례 기입
     - 사례:____
  ③ 과장표현: [ ] 절세 보장·과장광고·세무사법 오인 표현 없음 확인
  ④ 최종 발행 승인: 세무사명 ______  날짜 ______
  ```
```

- [ ] **Step 3: 검증**

Run: `grep -c -E 'editorial-plan.md|세무사 감수란|최종 발행 승인' .claude/agents/naver-seo-editor.md | tr -d ' '`
Expected: 출력 `3` 이상. 기존 게이트2 핸드오프 문구(마지막 문단)는 그대로인지 육안 확인.

- [ ] **Step 4: Commit (git 저장소일 때만)**

```bash
git add .claude/agents/naver-seo-editor.md
git commit -m "feat: strengthen internal-link check and add reviewer form to seo-editor"
```

---

### Task 4: README 갱신

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 구조도에 editorial-planner 추가**

`README.md`의 agents 트리에서 아래 줄을 찾는다:

```
│   │   ├── naver-brief-planner.md   # 1) 키워드 → 브리프
```

그 줄 바로 다음에 삽입한다:

```
│   │   ├── naver-editorial-planner.md # 1.5) 발행 캘린더 + 내부링크 그래프
```

- [ ] **Step 2: work/ 줄에 editorial-plan.md 추가**

아래 줄을 찾는다:

```
└── work/                            # content-registry.md(SSOT) + 핸드오프 <slug>-brief/research/draft/review.md + refresh-worklist.md
```

아래로 교체한다:

```
└── work/                            # content-registry.md(SSOT) + editorial-plan.md + 핸드오프 <slug>-brief/research/draft/review.md + refresh-worklist.md
```

- [ ] **Step 3: 셋업 체크리스트의 에이전트 개수 갱신**

아래 줄을 찾는다:

```markdown
- [ ] Claude Code에서 `/agents`로 6개 에이전트 로드 확인 (큐레이터·플래너·리서처·라이터·에디터·리프레시)
```

아래로 교체한다:

```markdown
- [ ] Claude Code에서 `/agents`로 7개 에이전트 로드 확인 (큐레이터·브리프플래너·에디토리얼플래너·리서처·라이터·에디터·리프레시)
```

- [ ] **Step 4: 검증**

Run: `grep -c 'naver-editorial-planner' README.md | tr -d ' '`
Expected: 출력 `1` 이상. `7개 에이전트`·`editorial-plan.md` 문구가 보이는지 육안 확인.

- [ ] **Step 5: Commit (git 저장소일 때만)**

```bash
git add README.md
git commit -m "docs: reflect editorial-planner in README"
```

---

## Self-Review

**1. Spec coverage**
- 에디토리얼 플래너(스펙 §1) → Task 1. 캘린더 + 내부링크 그래프 두 섹션, 초안 미수정 핸드오프 포함.
- brief-planner SERP 보강(스펙 §2) → Task 2. 할 일 단계 + 차별화 각도 출력. 기존 registry/게이트1 유지.
- seo-editor 보강(스펙 §3) → Task 3. 내부링크 검증 강화 + 세무사 기입란 4종(사실/사례/과장/서명). 기존 게이트2 유지.
- 통합 README(스펙 §4) → Task 4. 7개 에이전트 + editorial-plan.md.
- 성공 기준 5개 모두 태스크 검증 단계로 커버.

**2. Placeholder scan:** "TBD/TODO/적절히" 없음. 첨부 양식의 `____`·`항목1`은 세무사가 채울 입력 칸(의도된 빈칸)이지 계획의 미완성이 아님. 통과.

**3. Type consistency:** 파일 경로(`work/editorial-plan.md`)가 Task 1 출력·Task 3 체크·Task 4 README에서 동일. `cluster`·`status` 값이 1차 레지스트리 스펙과 일치. 에이전트 개수(7개) Task 4에서 일관. 통과.
