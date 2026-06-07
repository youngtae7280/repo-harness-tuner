# Repo Harness Tuner

Repo Harness Tuner는 프로젝트별 Codex 작업 하네스를 계속 설계하고 개선하기 위한 로컬 Codex 플러그인입니다.

핵심 루프는 다음과 같습니다.

```text
Analyze -> Diagnose -> Design -> Tune -> Restructure -> Evaluate
```

대상은 `AGENTS.md`, `Docs/AI/*`, 검증 지침, 사람 개입 정책, 워커 패턴, 평가 계획, 하네스 변경 이력입니다.

## 주요 기능

- 현재 저장소의 `AGENTS.md`, `Docs/AI/*`, `docs/ai/*`, `Docs/SKILLS.md`, `package.json` scripts, 일반 문서를 스캔합니다.
- Unity, Godot, Vite/Node, Node, Python, docs-only, unknown 프로젝트 프리셋을 적용합니다.
- `diagnose`로 하네스 준비도, 검증 drift, 과한 프로세스 규칙, 사람 개입 enforcement gap을 진단합니다.
- `design`으로 다음에 손댈 파일, 워커 구조, 평가 단계, 다음 리뷰 시점을 설계합니다.
- `bootstrap`/`apply`로 새 프로젝트의 최소 하네스를 dry-run 우선으로 생성합니다.
- `tune --dry-run --diff`로 기존 하네스에 review 가능한 unified diff를 만듭니다.
- `history`로 `Docs/AI/harness-history.jsonl`에 진단 스냅샷을 남기고, 이후 `diagnose`/`tune`이 그 반복 신호를 다시 반영합니다.
- `eval`로 baseline vs with-harness 평가 계획을 만들고, `eval --score`로 결과 JSON을 점수화합니다.
- `patterns`로 Codex 워커 패턴을 확인하고, `patterns --prompt`로 visible/background worker용 지시 프롬프트를 생성합니다.
- 내장된 `codex-harness-setup` 스킬을 사용해 실제 하네스 파일을 설계/수정합니다.

## 기본 사용법

플러그인 루트에서 실행합니다.

```powershell
python scripts\console.py overview --repo C:\path\to\repo
python scripts\console.py diagnose --repo C:\path\to\repo --phase active-development --human-involvement 3
python scripts\console.py design --repo C:\path\to\repo --phase active-development
python scripts\console.py tune --repo C:\path\to\repo --phase active-development --dry-run --diff
python scripts\console.py history --repo C:\path\to\repo --record --write --note "after feature slice"
```

새 프로젝트에서는 먼저 dry-run으로 봅니다.

```powershell
python scripts\console.py bootstrap --repo C:\path\to\repo --phase new-project --human-involvement 3
```

내용이 맞으면 명시적으로 씁니다.

```powershell
python scripts\console.py bootstrap --repo C:\path\to\repo --phase new-project --human-involvement 3 --write
```

사람 개입 레벨이 4 또는 5이면 파일 쓰기 명령에 `--confirm-write`가 추가로 필요합니다.

```powershell
python scripts\console.py tune --repo C:\path\to\repo --phase high-risk --write --confirm-write
```

## 사람 개입 레벨

사용자가 고르는 핵심 설정은 사람 개입 정도입니다.

- 1: 보호 영역이나 명시적 승인 조건이 없으면 Codex가 자율적으로 진행합니다.
- 2: 기존 패턴을 따라 진행하고 마무리에서 가정을 언급합니다.
- 3: 저장소 맥락으로 추론하되 되돌리기 어렵거나 사용자에게 보이는 방향 변경은 묻습니다.
- 4: 파일 수정 전에 1-3개의 집중 질문을 합니다. 단, 저장소의 명확한 source of truth가 답을 주면 진행할 수 있습니다.
- 5: 파일 수정 전에 명시적 승인을 받아야 합니다.

내부적으로는 이 레벨이 `Docs/AI/ambiguity-profile.md`의 ask-before 규칙으로 표현됩니다.

## 평가

평가 계획을 만들려면:

```powershell
python scripts\console.py eval --repo C:\path\to\repo --phase active-development
```

baseline과 with-harness 결과를 JSON으로 기록한 뒤 점수화하려면:

```powershell
python scripts\console.py eval --score C:\path\to\eval-results.json
```

점수화는 assertion 단위로 improved, regressed, unchanged pass, unchanged fail을 계산하고 keep/revise 권고를 냅니다.

## 워커 패턴

패턴 목록:

```powershell
python scripts\console.py patterns
```

특정 패턴으로 worker 지시문 생성:

```powershell
python scripts\console.py patterns --prompt background-review --repo C:\path\to\repo --phase active-development --scope "validation drift"
```

visible chat은 제품 방향, 승인, QA 증거처럼 사용자가 직접 봐야 하는 결정에 쓰고, background/read-only worker는 코드 리뷰, 테스트 리뷰, 정적 스캔, 하네스 감사처럼 최종 findings만 중요할 때 씁니다.

## 안전 기본값

- 파일 쓰기는 기본적으로 일어나지 않습니다. `--write`가 있어야 합니다.
- 사람 개입 4/5에서는 `--confirm-write`도 필요합니다.
- 기존 bootstrap 파일은 기본적으로 skip되며, 덮어쓰려면 `--write --force`가 필요합니다.
- `tune`은 전체 파일을 갈아엎지 않고 `repo-harness-tuner:start:*` / `repo-harness-tuner:end:*` 관리 섹션을 갱신합니다.
- dependency, release, CI, secret, migration, privacy-sensitive 변경은 명시적 승인 없이는 추가하지 않습니다.
