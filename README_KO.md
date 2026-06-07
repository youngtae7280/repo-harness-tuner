# Repo Harness Tuner

Repo Harness Tuner는 프로젝트별 Codex 작업 하네스를 계속 설계하고 개선하기 위한 로컬 Codex 플러그인입니다.

최종 목표는 두 축을 함께 가져가는 것입니다.

- **Factory**: 프로젝트별 agent team, role prompt, skill plan, orchestration 문서를 생성합니다.
- **Engine**: 그 하네스를 분석, 진단, 튜닝, 평가하면서 프로젝트가 진행될수록 계속 개선합니다.

핵심 루프는 다음과 같습니다.

```text
Analyze -> Diagnose -> Design -> Factory -> Tune -> Restructure -> Evaluate
```

대상은 `AGENTS.md`, `Docs/AI/*`, 검증 지침, 사람 개입 정책, 워커 패턴, 평가 계획, 하네스 변경 이력, agent team/skill 계획입니다.

## 주요 기능

- 현재 저장소의 `AGENTS.md`, `Docs/AI/*`, `docs/ai/*`, `Docs/SKILLS.md`, `package.json` scripts, 일반 문서를 스캔합니다.
- Unity, Godot, Vite/Node, Node, Python, docs-only, unknown 프로젝트 프리셋을 적용합니다.
- `diagnose`로 하네스 준비도, 검증 drift, 과한 프로세스 규칙, 사람 개입 enforcement gap을 진단합니다.
- `design`으로 다음에 손댈 파일, 워커 구조, 평가 단계, 다음 리뷰 시점을 설계합니다.
- `factory`로 도메인 설명과 저장소 진단을 합쳐 Codex agent team/skill 계획, repo-local 문서, Codex `SKILL.md` 초안, 확인된 skill 설치를 처리합니다.
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
python scripts\console.py factory --repo C:\path\to\repo --domain "Unity tycoon game UI" --phase active-development
python scripts\console.py tune --repo C:\path\to\repo --phase active-development --dry-run --diff
python scripts\console.py history --repo C:\path\to\repo --record --write --note "after feature slice"
```

factory plan을 파일로 남기려면:

```powershell
python scripts\console.py factory --repo C:\path\to\repo --domain "deep research" --team-size 3 --write-plan
```

이 명령은 다음 파일을 씁니다.

```text
Docs/AI/factory-plan.md
```

agent team/skill 문서까지 생성하려면:

```powershell
python scripts\console.py factory --repo C:\path\to\repo --domain "technical documentation" --write-artifacts
```

이 명령은 기존 파일을 덮어쓰지 않고, 없는 파일만 생성합니다.

```text
Docs/AI/agent-team.md
Docs/AI/team-orchestration.md
Docs/AI/skills/*.md
```

기존 factory artifact를 의도적으로 덮어쓰려면 `--force`를 함께 사용합니다.

설치/복사 가능한 Codex skill 초안까지 만들려면:

```powershell
python scripts\console.py factory --repo C:\path\to\repo --domain "technical documentation" --write-codex-skills
```

이 명령은 다음 구조를 만듭니다.

```text
Docs/AI/codex-skills/<skill-id>/SKILL.md
```

이 스킬 초안은 자동 설치되지 않습니다. 검토와 검증 후 필요한 위치로 복사하거나 설치하는 흐름을 사용합니다.

생성된 skill 초안을 실제 Codex skills 디렉터리에 설치하려면:

```powershell
python scripts\console.py factory --repo C:\path\to\repo --domain "technical documentation" --install-codex-skills --confirm-install
```

기본 설치 위치는 `$CODEX_HOME/skills`이고, `CODEX_HOME`이 없으면 `~/.codex/skills`입니다. 다른 위치에 설치하려면 `--skill-install-root`를 사용합니다. 설치는 저장소 밖에 쓰는 작업이므로 항상 `--confirm-install`이 필요합니다.

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

## Factory와 Engine의 관계

Factory는 “어떤 팀과 스킬이 필요한가”를 설계합니다.

- agent 역할
- role별 목적과 출력물
- skill plan
- visible/background worker 정책
- orchestration 문서

Engine은 “그 설계가 프로젝트에 맞게 계속 좋아지고 있는가”를 관리합니다.

- readiness 진단
- drift와 과한 프로세스 감지
- history feedback 반영
- evaluation score 반영
- tune diff 생성

둘 중 하나만으로는 부족합니다. 이 플러그인의 목표는 팀/스킬 생성 공장과 점진적 하네스 개선 엔진을 함께 제공하는 것입니다.

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

## 안전 기본값

- 파일 쓰기는 기본적으로 일어나지 않습니다. `--write` 또는 `--write-plan`이 있어야 합니다.
- 사람 개입 4/5에서는 `--confirm-write`도 필요합니다.
- 기존 bootstrap 파일은 기본적으로 skip되며, 덮어쓰려면 `--write --force`가 필요합니다.
- `tune`은 전체 파일을 갈아엎지 않고 `repo-harness-tuner:start:*` / `repo-harness-tuner:end:*` 관리 섹션을 갱신합니다.
- dependency, release, CI, secret, migration, privacy-sensitive 변경은 명시적 승인 없이는 추가하지 않습니다.
