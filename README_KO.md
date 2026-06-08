# Repo Harness Tuner

Repo Harness Tuner는 Codex가 프로젝트별로 필요한 최소 작업 하네스를 만들고, 프로젝트가 진행되면서 계속 알맞게 조정하도록 돕는 로컬 Codex 플러그인입니다.

목표는 원커맨드 assistant 경험입니다. 사용자는 한 번 요청하고, 플러그인은 repo를 분석하고, 다음 하네스 작업과 필요한 최소 skill/agent 후보를 추천하며, 파일 쓰기와 설치는 명시 승인 뒤에만 진행합니다.

## 시작하기

Codex에서는 이렇게 한 번 요청하세요.

```text
repo-harness-tuner로 이 repo를 봐줘. 프로젝트를 분석하고, Codex 하네스를 진단하고, 다음 작업과 필요한 최소 skill/agent를 추천하되, 파일 쓰기와 설치는 승인 후에만 진행해줘.
```

CLI에서는 read-only planning pass부터 시작합니다.

```powershell
python scripts\console.py run-loop --repo C:\path\to\repo --phase active-development --domain "your project"
```

진단만 보고 싶다면:

```powershell
python scripts\console.py doctor --repo C:\path\to\repo --phase active-development --domain "your project"
```

## 다음에 일어나는 일

루프는 다음 순서로 판단합니다.

```text
Analyze -> Diagnose -> Design -> Factory -> Recommend Skills -> Tune -> Evaluate
```

결과에 따라 다음 중 하나를 추천합니다.

- 현재 하네스가 충분하면 변경 없음
- 첫 하네스가 필요하면 `bootstrap`
- 오래되거나 어긋난 하네스 문서는 `tune`
- 프로젝트별 팀/skill 설계가 필요하면 `factory`
- 최소 skill/agent 후보가 필요하면 `recommend-skills`
- 다음 실행이 더 좋아지도록 eval/history 기록

처음부터 모든 명령을 고를 필요는 없습니다. `run-loop` 또는 `doctor`로 시작하고, 출력된 next action을 검토한 뒤 진행하면 됩니다.

## 안전 모델

기본은 read-first입니다.

- `doctor`와 기본 `run-loop`는 파일을 수정하지 않습니다.
- 파일 쓰기는 `--write`, `--write-plan`, `--write-recommended`, `--write-artifacts` 같은 명시 플래그가 필요합니다.
- skill 설치는 `--install --confirm-install`이 필요합니다.
- human involvement 4 또는 5에서는 `--confirm-write`도 필요합니다.
- dependency, release, CI, secret, credential, marketplace, install/uninstall, migration, privacy-sensitive, destructive 변경은 명시 승인 없이는 진행하지 않습니다.
- 외부 ECC 후보는 대량 설치하지 않고, 승인된 경우 작은 Codex adapter skill로만 설치합니다.

## Skill 추천

`run-loop`에는 최소 skill 추천이 포함됩니다. 별도로 보고 싶으면:

```powershell
python scripts\console.py recommend-skills --repo C:\path\to\repo --phase active-development --domain "your project" --source builtin,ecc
```

추천 대상은 code review, TDD, security, docs, build-fix, frontend-ui, release-check 같은 역량입니다. 내장 factory로 충분한지, ECC seed catalog 후보가 필요한지 판단하지만, 추천은 1-3개로 제한됩니다.

설치하려면 반드시 검토 후 실행합니다.

```powershell
python scripts\console.py recommend-skills --repo C:\path\to\repo --install --confirm-install
```

이 설치는 Codex adapter skill만 생성합니다. ECC hooks, MCP 서버, slash command, agent 파일, marketplace 설정은 자동으로 설치하지 않습니다.

## Adaptive Harness Loop

프로젝트가 진행되면 하네스도 바뀌어야 합니다.

플러그인은 다음 신호를 봅니다.

- phase별 review cadence
- 다음 review trigger
- readiness score 변화
- 반복되는 validation drift
- 반복되는 process overhead
- 반복되는 human-involvement gap
- eval regression 또는 unchanged failure

이 신호들은 `adaptive.cadence`, `adaptive.human_involvement`, `skill_recommendations.curator`에 구조화되어 출력됩니다. 튜닝 주기나 인간개입 정책은 자동 변경하지 않고, 추천만 하며 적용은 승인 기반입니다.

## Human Involvement

human involvement는 Codex가 행동 전 얼마나 자주 물어봐야 하는지를 정합니다.

| Phase | 기본값 |
| --- | ---: |
| `prototype` | 2 |
| `new-project` | 3 |
| `active-development` | 3 |
| `maintenance` | 3 |
| `pre-release` | 4 |
| `high-risk` | 5 |

직접 조정할 수 있습니다.

```powershell
python scripts\console.py run-loop --repo C:\path\to\repo --human-involvement 4
python scripts\console.py run-loop --repo C:\path\to\repo --module "Release flow: 5"
```

## 핵심 명령

```powershell
python scripts\console.py doctor --repo C:\path\to\repo --phase active-development --domain "your project"
python scripts\console.py run-loop --repo C:\path\to\repo --phase active-development --domain "your project"
python scripts\console.py recommend-skills --repo C:\path\to\repo --phase active-development --domain "your project"
python scripts\console.py tune --repo C:\path\to\repo --phase active-development --dry-run --diff
python scripts\console.py bootstrap --repo C:\path\to\repo --phase new-project
python scripts\console.py fixture-test
```

전체 명령과 JSON 예시는 [Docs/commands.md](Docs/commands.md)에 있습니다.

## 설치

처음 설치할 때는 `$HOME\plugins\repo-harness-tuner`에 clone하고 personal marketplace entry를 추가한 뒤 실행합니다.

```powershell
codex plugin add repo-harness-tuner@personal
```

fresh clone, 갱신, 문제 해결, Windows `codex.exe` shim, PyYAML validator, 검증 절차는 [Docs/install.md](Docs/install.md)를 보세요.

## 관련 문서

- English README: [README.md](README.md)
- 설치와 문제 해결: [Docs/install.md](Docs/install.md)
- 전체 명령: [Docs/commands.md](Docs/commands.md)
- CLI 계약: [Docs/cli-contracts.md](Docs/cli-contracts.md)
- 버전/변경 정책: [Docs/versioning.md](Docs/versioning.md)
- Fixture tests: [Docs/fixture-tests.md](Docs/fixture-tests.md)
- 로드맵: [ROADMAP.md](ROADMAP.md)
- 다른 PC/thread에서 이어가기: [HANDOFF.md](HANDOFF.md)
