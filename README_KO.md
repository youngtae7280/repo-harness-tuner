# Repo Harness Tuner

Repo Harness Tuner는 Codex가 프로젝트별 작업 지침을 더 잘 설계하고, 진단하고, 개선하고, 평가하도록 돕는 로컬 Codex 플러그인입니다.

핵심 루프는 다음과 같습니다.

```text
Analyze -> Diagnose -> Design -> Tune -> Restructure -> Evaluate
```

대상은 `AGENTS.md`, `Docs/AI/*`, 검증 지침, 사람 개입 수준, 워커 패턴, 평가 계획, 하네스 변경 이력입니다.

## 주요 기능

- 저장소 하네스 진단: `AGENTS.md`, `Docs/AI/*`, package scripts, 에이전트 지침 파일 확인.
- 프로젝트 타입 감지: Unity, Godot, Vite/Node, Node, Python, docs-only.
- 하네스 설계안 생성: 대상 파일, 워커 패턴, 검증 단계, 다음 리뷰 시점.
- Codex 워커 패턴 선택: `single-agent`, `background-review`, `visible-decision-thread`, `producer-reviewer`, `fanout-review`, `supervisor-cycle`, `phase-handoff`.
- 평가 계획 생성: 일반 Codex 사용과 repo-harness-tuner 사용 결과를 비교하는 golden task와 assertion 제공.
- 부트스트랩/적용: 새 프로젝트용 최소 하네스 파일 생성. 기본은 dry-run.
- 튜닝 diff 생성: 기존 하네스 파일을 통째로 덮지 않고 관리 섹션 기반 unified diff 제안.
- 하네스 히스토리: `Docs/AI/harness-history.jsonl`에 진단 스냅샷 기록.
- 내장 `codex-harness-setup` 스킬 포함.

## 자주 쓰는 명령

```powershell
python scripts\console.py overview --repo C:\path\to\repo
python scripts\console.py diagnose --repo C:\path\to\repo --phase active-development --human-involvement 3
python scripts\console.py design --repo C:\path\to\repo --phase active-development
python scripts\console.py patterns
python scripts\console.py eval --repo C:\path\to\repo --phase active-development
python scripts\console.py bootstrap --repo C:\path\to\repo --phase new-project
python scripts\console.py bootstrap --repo C:\path\to\repo --phase new-project --write
python scripts\console.py tune --repo C:\path\to\repo --phase active-development --dry-run --diff
python scripts\console.py tune --repo C:\path\to\repo --phase active-development --write
python scripts\console.py history --repo C:\path\to\repo
python scripts\console.py history --repo C:\path\to\repo --record --write --note "first snapshot"
```

## 사람 개입 수준

- 1: 보호 영역 외에는 대부분 자율 진행.
- 2: 기존 패턴을 따라 진행하고 마무리에 가정을 기록.
- 3: 기본 균형값. 되돌리기 어렵거나 사용자에게 보이는 방향 변경은 질문.
- 4: 편집 전 1-3개의 집중 질문.
- 5: 파일 편집 전 명시 승인 필요.

## 안전 기본값

- 파일 쓰기는 `--write`가 있어야 실행됩니다.
- 기존 하네스 파일은 기본적으로 건너뜁니다.
- 덮어쓰기는 `--write --force`가 모두 있어야 합니다.
- `tune`은 기존 파일 전체를 덮지 않고 `repo-harness-tuner` 관리 섹션을 추가/갱신합니다.
- 평가 명령은 plan-only이며 별도 에이전트를 자동 실행하지 않습니다.
- destructive operation, dependency, release, CI, secret, migration, privacy-sensitive 변경은 명시 승인이 필요합니다.
- 공개 배포 전에는 `NOTICE.md`를 읽고 내장 `codex-harness-setup` 스킬의 재배포 방식을 확인하세요.

## 추천 운영 방식

새 프로젝트에서는 먼저 dry-run을 봅니다.

```powershell
python scripts\console.py bootstrap --repo C:\path\to\repo --phase new-project --human-involvement 3
```

내용이 맞으면 실제로 씁니다.

```powershell
python scripts\console.py bootstrap --repo C:\path\to\repo --phase new-project --human-involvement 3 --write
```

프로젝트가 진행되면 3-5개의 의미 있는 작업 주기마다 진단하고 히스토리를 남깁니다.

```powershell
python scripts\console.py diagnose --repo C:\path\to\repo --phase active-development
python scripts\console.py tune --repo C:\path\to\repo --phase active-development --dry-run --diff
python scripts\console.py history --repo C:\path\to\repo --record --write --note "after feature slice"
```
