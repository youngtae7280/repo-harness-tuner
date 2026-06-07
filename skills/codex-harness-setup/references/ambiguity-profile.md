# Ambiguity Profiles

Use this reference when a repository needs a repeatable policy for how much Codex should ask versus infer. Do not create an ambiguity profile by default; add one only when the user asks for it, repeated agent work is misaligned, or different modules clearly need different levels of confirmation.

## Contents

- Ambiguity Scale
- When to Use
- Module Discovery
- Interview Policy
- Overrides
- Template
- Examples
- Calibration

## Ambiguity Scale

Use 1-5:

| Level | Meaning | Interview behavior | Best for |
|---|---|---|---|
| 1 | Very low ambiguity | Confirm goals, constraints, success criteria, and risky decisions before edits. | destructive, data, release, payment, permissions |
| 2 | Low ambiguity | Ask 3-5 high-impact questions before implementation. | UI direction, balance, public API, migrations |
| 3 | Medium ambiguity | Ask only 1-3 questions that change direction or risk. | normal features, docs, harness setup |
| 4 | High ambiguity | Proceed from repo context; ask only when blocked or reversal is expensive. | isolated fixes, refactors, internal tools |
| 5 | Very high ambiguity | Explore and propose without upfront questions. | brainstorming, prototypes, throwaway experiments |

Default to 3 unless project risk, user preference, or module policy says otherwise.

## When to Use

Create or update `docs/ai/ambiguity-profile.md` when:

- the user asks to control how much Codex interviews them,
- agents ask too many questions for routine work,
- agents make too many assumptions in high-risk areas,
- project modules have different risk and preference needs,
- a harness review finds repeated misalignment between user intent and agent output.

Skip it when:

- the repository is small and one `AGENTS.md` rule is enough,
- the user only needs a one-off change,
- module boundaries are not stable enough to document yet.

## Module Discovery

Do not assume a fixed module taxonomy. Derive areas from the repository:

- paths and namespaces,
- build targets or packages,
- domain concepts in README/docs,
- task verbs such as publish, migrate, delete, balance, redesign, refactor,
- risk surfaces such as data, auth, payments, release, user-facing UI, public APIs,
- known failure notes or user feedback.

Modules can overlap. When a task touches multiple areas, use the lowest ambiguity level unless the profile states a more specific rule.

## Interview Policy

Use questions only when they reduce meaningful risk:

- Would the answer change the goal, scope, or user-visible behavior?
- Is the decision preference-heavy rather than codebase-inferable?
- Is the cost of a wrong assumption high or hard to reverse?
- Would one question eliminate several follow-up guesses?

Avoid asking about implementation details the agent can infer from local patterns.

## Overrides

Lower ambiguity to 1-2 when a task touches:

- persisted or user-owned data,
- destructive operations,
- payments, ads, monetization, or store submission,
- auth, permissions, secrets, or privacy,
- migrations, release, deployment, signing, or production config,
- public API contracts or compatibility boundaries.

Allow ambiguity 4-5 when the task is:

- exploratory,
- a disposable prototype,
- a small isolated refactor,
- an internal tool polish pass,
- a low-risk bug with clear reproduction and rollback.

User preference overrides module defaults. If the user says "move fast" or "handle it yourself", raise ambiguity unless a risk override applies. If the user says "confirm before changing", lower ambiguity.

## Template

```md
# Ambiguity Profile

## Default
- Default ambiguity: 3
- User interview style: ask only questions that change direction, risk, or irreversible decisions.

## Module ambiguity
| Area | Paths / signals | Ambiguity | Ask before | Agent may decide | Evidence |
|---|---|---:|---|---|---|
| [area] | [paths or task signals] | [1-5] | [decisions requiring user input] | [safe inferred decisions] | [validation/review evidence] |

## Risk overrides
- Lower to 1 when:
- Lower to 2 when:
- Allow 4 when:
- Allow 5 when:

## Interview budget
| Ambiguity | Typical questions before edits |
|---|---:|
| 1 | 5-10 |
| 2 | 3-5 |
| 3 | 1-3 |
| 4 | 0-1 |
| 5 | 0 |

## Calibration notes
| Date | Task | Expected ambiguity | Actual behavior | Adjustment |
|---|---|---:|---|---|
| YYYY-MM-DD | [task] | [1-5] | [too many questions / too few / right] | [change] |
```

## Examples

### Unity game

| Area | Signals | Ambiguity | Ask before | Agent may decide |
|---|---|---:|---|---|
| Save data | `Save`, persistence, player progress | 1 | schema changes, migration, destructive reset | naming, local cleanup |
| Economy balance | `Balance`, rewards, prices, tables | 2 | progression intent, target difficulty, monetization impact | data formatting, loader shape |
| UI screens | `UI`, `Views`, `Prefabs`, visual polish | 2-3 | visual direction, major flow changes | spacing, alignment, existing-style polish |
| Editor tools | `Editor`, internal utilities | 4 | workflow-breaking changes | helper refactors, focused fixes |
| Prototype | task says prototype or explore | 5 | none upfront | rough implementation and options |

### Web app

| Area | Signals | Ambiguity | Ask before | Agent may decide |
|---|---|---:|---|---|
| Auth and permissions | auth, roles, sessions | 1 | permission semantics, rollout, compatibility | local test shape |
| Billing | payment, plan, subscription | 1 | pricing behavior, provider-side changes | copy-safe refactors |
| Database migration | migration, schema, backfill | 1 | data transformation, rollback, approval | dry-run command structure |
| API contracts | public endpoints, SDKs | 2 | breaking changes, versioning | internal helper design |
| Admin UI | dashboard, internal workflow | 3 | workflow priority | layout polish in current design system |
| Style tweak | CSS-only, copy-only | 4 | only broad visual direction | implementation detail |

## Calibration

Review the profile after 3-5 meaningful cycles or immediately after:

- the agent asked too many low-value questions,
- the agent made a wrong assumption in a high-risk area,
- the user corrected tone, style, product direction, or risk tolerance,
- a module boundary changed.

Prefer changing one row or override at a time. Do not turn ambiguity profiling into a full project management system.
