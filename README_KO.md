# Repo Harness Tuner

Repo Harness Tuner는 프로젝트에 맞는 Codex 작업 하네스를 만들고, 프로젝트가 진행되면서 계속 적정 크기로 튜닝해 주는 로컬 Codex 플러그인입니다.

목표는 원커맨드 assistant 경험입니다. 사용자는 한 번 요청하고, 플러그인은 저장소를 분석하고, 다음 하네스 작업을 판단하고, 파일 쓰기는 명시 승인 뒤에만 진행합니다.

## 여기서 시작

Codex에서는 이렇게 한 번 요청합니다.

```text
repo-harness-tuner로 이 repo를 점검해줘. 프로젝트를 분석하고, Codex 하네스를 진단하고, 다음 작업을 추천하되 파일 쓰기는 승인 뒤에만 해줘.
```

CLI에서는 읽기 전용 planning pass 하나로 시작합니다.

```powershell
python scripts\console.py run-loop --repo C:\path\to\repo --phase active-development --domain "your project"
```

진단만 보고 싶으면:

```powershell
python scripts\console.py doctor --repo C:\path\to\repo --phase active-development --domain "your project"
```

## 다음에 일어나는 일

루프는 하네스 작업을 이 순서로 판단합니다.

```text
Analyze -> Diagnose -> Design -> Factory -> Tune -> Evaluate
```

결과에 따라 다음 중 하나를 추천합니다.

- 현재 하네스가 충분해서 변경하지 않음
- 새 프로젝트에 최소 하네스를 만드는 `bootstrap`
- 낡은 하네스 문서를 부분 수정하는 `tune`
- 프로젝트별 team/skill 계획을 만드는 `factory`
- 다음 실행이 학습할 수 있도록 eval/history 기록

처음부터 모든 명령을 고를 필요는 없습니다. `run-loop` 또는 `doctor`로 시작하고, 출력된 next action을 검토한 뒤 진행하면 됩니다.

## 안전 모델

기본은 read-first입니다.

- `doctor`와 기본 `run-loop`는 파일을 수정하지 않습니다.
- 파일 쓰기는 `--write`, `--write-plan`, `--write-recommended`, `--write-artifacts` 같은 명시 플래그가 있어야 합니다.
- 사람 개입 레벨이 4 또는 5이면 `--confirm-write`도 필요합니다.
- dependency, release, CI, secret, credential, marketplace, install/uninstall, migration, privacy-sensitive, destructive 변경은 명시 승인 없이는 진행하지 않습니다.
- `tune`은 전체 파일을 갈아엎지 않고 관리되는 markdown 섹션만 갱신합니다.
- `bootstrap`과 factory artifact 쓰기는 명시적인 force 경로 없이는 기존 파일을 보존합니다.

## 언제 사용하나요?

다음 상황에서 사용합니다.

- `AGENTS.md` 또는 `Docs/AI/*`가 필요할 때
- Codex가 너무 많은 절차를 만들거나, 반대로 필요한 검증/질문을 놓칠 때
- 검증 지침, ask-before-edit 규칙, worker visibility를 저장소별로 정리하고 싶을 때
- 프로젝트별 Codex team/skill 계획이 필요할 때
- history/eval 증거로 하네스를 계속 튜닝하고 싶을 때

일반 코딩, 디버깅, 리뷰처럼 하네스 자체가 이미 적절한 작업에는 보통 필요하지 않습니다.

## Adaptive Harness Loop

이 플러그인은 프로젝트가 계속 바뀐다는 전제를 둡니다.

추적하는 신호:

- phase별 review cadence
- 다음 review trigger
- readiness score 변화
- 반복되는 validation drift
- 반복되는 process overhead
- 반복되는 human-involvement gap
- eval regression 또는 unchanged failure

이 신호들이 review pressure를 올리고, 다음 `run-loop`가 `tune`, `eval-review`, 더 짧은 review interval을 추천하게 만들 수 있습니다.

`doctor`와 `run-loop`는 cadence와 사람 개입 레벨에 대한 구조화된 `adaptive` 추천도 출력합니다. 아직 백그라운드 스케줄러처럼 자동 실행되지는 않습니다. 추천된 시점, 의미 있는 프로젝트 변경 뒤, Codex가 같은 실수를 반복한 뒤, high-risk/release 작업 전에 `doctor` 또는 `run-loop`를 다시 실행하는 구조입니다.

## 사람 개입 레벨

사람 개입 레벨은 Codex가 행동 전에 얼마나 자주 물어야 하는지 정합니다.

기본값은 phase로 자동 선택됩니다.

| Phase | 기본값 |
| --- | ---: |
| `prototype` | 2 |
| `new-project` | 3 |
| `active-development` | 3 |
| `maintenance` | 3 |
| `pre-release` | 4 |
| `high-risk` | 5 |

직접 조절할 수도 있습니다.

```powershell
python scripts\console.py run-loop --repo C:\path\to\repo --human-involvement 4
python scripts\console.py run-loop --repo C:\path\to\repo --module "Release flow: 5"
```

레벨 의미:

- `1`: 보호 영역이 없으면 Codex가 자율적으로 진행
- `2`: 기존 repo 패턴을 따르고 마무리에 가정 보고
- `3`: repo 문맥으로 추론하되 되돌리기 어렵거나 사용자에게 보이는 방향 변경은 질문
- `4`: repo가 이미 답하지 않는 한 편집 전에 집중 질문
- `5`: 편집 전 명시 승인 필요

현재는 human-involvement gap과 history/eval 증거를 바탕으로 기본 레벨을 유지, 상향, 하향할지 추천할 수 있습니다. 단, 정책 변경은 자동 적용되지 않으며 repo-local policy를 바꾸려면 검토와 명시 승인이 필요합니다.

## 핵심 명령

이 플러그인 디렉터리에서 실행합니다.

```powershell
python scripts\console.py doctor --repo C:\path\to\repo --phase active-development --domain "your project"
python scripts\console.py run-loop --repo C:\path\to\repo --phase active-development --domain "your project"
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

fresh clone, 갱신, 문제 해결, Windows `codex.exe` shim, PyYAML validator, 검증 절차는 [Docs/install.md](Docs/install.md)를 봅니다.

## 관련 문서

- English README: [README.md](README.md)
- 설치와 문제 해결: [Docs/install.md](Docs/install.md)
- 전체 명령어: [Docs/commands.md](Docs/commands.md)
- CLI 계약: [Docs/cli-contracts.md](Docs/cli-contracts.md)
- 버전과 파괴적 변경 정책: [Docs/versioning.md](Docs/versioning.md)
- Fixture 테스트: [Docs/fixture-tests.md](Docs/fixture-tests.md)
- 로드맵: [ROADMAP.md](ROADMAP.md)
- 다른 PC/thread에서 이어가기: [HANDOFF.md](HANDOFF.md)
