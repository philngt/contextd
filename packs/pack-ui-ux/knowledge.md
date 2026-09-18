# pack-ui-ux — Canonical Knowledge

Manifest v3, decision-first profile: Global Principles and each routed
component's decision core are loaded. Optional foundations and procedures are
requested by exact ID; they are not mandatory prerequisites for execution. Legacy `agents/` files remain compatibility adapters.

## Global Principles

A capable agent may execute directly from strategy and judgment using its
available tools. A packaged skill is not required unless a controlling contract
requires its procedure. Tool permissions and actual outcome verification still
apply; this profile does not infer model competence from self-confidence.

Start with the user task, observed state, and controlling workspace design
contract. Separate inspected evidence, a mechanism hypothesis, a recommendation,
and an accepted decision. Existing strict-only constraints remain authoritative;
new strategy heuristics do not grant exceptions to them. Do not fabricate user
research, claim usability from appearance alone, or promote local feedback into
shared standards without review.

If required design knowledge is missing, report the gap and request the smallest
needed artifact. Do not invent an existing token catalog or production contract.
Hypothetical alternatives may be explored as such, not reported as approved facts.

### Inherited baseline

The following rule groups retain the existing pack requirements. They are the
pack's design baseline, not a complete WCAG audit or an exhaustive statement of
all criterion-specific conditions. The external baseline remains the review
recorded in the manifest, not a newly claimed standards review.

### Design Token (`pack-ui-ux-design-token`)

- **KHÔNG hardcode color/spacing/font literal** trong component spec, flow doc, hoặc UX writing doc — mọi giá trị phải tham chiếu token name (vd `color-primary-default`, không `#3B5AFE`). Ngoại lệ duy nhất: file `tokens.md` nơi token được định nghĩa.
- **Token name PHẢI thuộc token catalog** trong `{ws}/platform/design/tokens.md` — KHÔNG tự sáng tạo token name ngoài catalog.
- **Xóa/đổi tên token hiện có** PHẢI có migration note trong `tokens.md` + thông báo consumer bị ảnh hưởng.

### Accessibility (WCAG 2.2 AA) (`pack-ui-ux-accessibility`)

- **Contrast ratio PHẢI ≥ 4.5:1** cho text thông thường, **≥ 3:1** cho large text (≥ 18pt hoặc 14pt bold) và UI component (border, icon).
- **Mọi interactive element** (button, link, input, custom control) PHẢI có spec keyboard navigation (Tab/Enter/Space/Escape/Arrow) và visible focus indicator.
- **Mọi image/icon có nghĩa** PHẢI có alt text spec; icon decorative PHẢI có `aria-hidden` note.
- **Form element** PHẢI có label association spec — KHÔNG chỉ placeholder làm label.
- **ARIA role/label** khi dùng PHẢI match ARIA Authoring Practices Guide — KHÔNG dùng ARIA để patch non-semantic HTML.

### User Flows (`pack-ui-ux-user-flows`)

- **Mỗi user flow PHẢI cover relevant states** từ requirement/state matrix: success, loading/empty, validation, permission, timeout/recovery theo rủi ro thực tế; không dùng quota edge-case cố định.
- **Flow PHẢI identify persona/role** thực hiện — KHÔNG generic "user".
- **Decision point PHẢI có tất cả branch** được label — KHÔNG để branch ngầm.
- **Screen flow KHÔNG thay thế wireframe/prototype** — nếu interaction phức tạp, link tới Figma/prototype trong flow doc.

### UX Writing (`pack-ui-ux-writing`)

- **Copy dành cho end-user KHÔNG dùng jargon kỹ thuật** (stack trace, error code, field name backend) — translate sang ngôn ngữ người dùng.
- **Error message PHẢI actionable và an toàn** — nói điều xảy ra và next step phù hợp; chỉ nêu nguyên nhân khi biết chắc và không leak sensitive detail.
- **CTA PHẢI mô tả action/outcome trong context**; generic label chỉ hợp lệ khi surrounding semantics làm accessible name rõ ràng.

### Design Decisions (`pack-ui-ux-decisions`)

- **Quyết định chọn component library, design system, hoặc thay đổi token scale PHẢI có ADR** trong `{ws}/design/decisions/`.
- **Design ADR PHẢI nêu** options considered + rationale + consequences.

### Executable checks and their limits

| Rule ID | Severity | Actual check; not a semantic guarantee |
|---|---|---|
| `pack-ui-ux-hardcoded-color` | error | Detects matched color literals in design Markdown outside `tokens.md`; fenced code is skipped. Does not validate all token categories or catalog membership. |
| `pack-ui-ux-missing-a11y-note` | warn | `platform/design/design-system.md` must contain a blockquote with literal `A11y:`. Does not test keyboard or assistive behavior. |
| `pack-ui-ux-flow-no-error-path` | warn | Domain flow Markdown must contain an Error or Edge heading. Does not prove reachable-state coverage or recovery. |
| `pack-ui-ux-contrast-unchecked` | warn | Design Markdown mentioning a color token must mention contrast or a ratio. Does not measure or validate that ratio. |

Use the literal format `> A11y: ...` in component specs so the example matches
the executable checker. Layer-1 success is not a Layer-2 design acceptance.
Baseline reference: [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/).

## Component: design-system

### Mental Model

- **Observe:** Inspect the current component anatomy, supported states, token catalog, content lengths, viewport/text-size requirements, and the user task. Identify competing visual emphasis before changing styling.
- **Mechanism:** Contrast, grouping, spacing, and position can influence perceived priority; treat the predicted attention order as a hypothesis to inspect, not a universal scan-path law. Shared tokens propagate both improvements and mistakes to consumers.

### Standards

Apply `pack-ui-ux-design-token` and all applicable Global Principles; optional support never relaxes them.

### Strategy

- **Choose:** For competing actions, compare changing emphasis, regrouping information, or revealing secondary controls later. Prefer an existing component/token when it fits; document a new variant or token-scale decision rather than inventing catalog entries.
### Judgment

- **Exception:** Comparison and expert tools may need several peer actions and higher density. Do not impose one primary action, generous whitespace, or a new component library independently of the task and constraints.

Hypothetical contrast: a first-time single-task flow may benefit from stronger emphasis on one action; an expert comparison canvas may need peer actions kept visible. The deciding evidence is the actual task, not a universal density or button-count rule.

### Procedure: document-design-system

#### Design Token Format (tokens.md)

- Naming pattern: `{category}-{variant}-{state}` — vd `color-primary-default`, `color-primary-hover`, `spacing-md`, `font-size-body`.
- Categories chuẩn: `color`, `spacing`, `font-size`, `font-weight`, `line-height`, `border-radius`, `shadow`, `motion-duration`, `motion-easing`.
- Mỗi token entry: name + value + usage note (1 dòng) + alias nếu có.
- Group token theo category với heading `## {Category}`.
- Deprecated token: gạch tên + note `(deprecated — dùng {replacement})`, giữ ít nhất 1 version trước khi xóa.

#### Component Spec Format (design-system.md)

- Mỗi component: Anatomy (tên các part) → Variants → States → Do/Don't → A11y note → Token usage.
- **A11y note** dùng blockquote: `> A11y: ...` — đặt cuối component spec, trước Token usage.
- Variant table: columns `Variant | When to use | Token override (nếu có)`.
- State coverage: default, hover, focus, active, disabled, error, loading (chỉ những state component hỗ trợ).

#### Design Decision (ADR) Format

- File naming: `{YYYY-MM-DD}-{slug}.md` — vd `2026-05-22-choose-component-library.md`.
- Structure: Status → Context → Decision → Options considered → Rationale → Consequences.
- Status: `Proposed | Accepted | Deprecated | Superseded by {file}`.

### Foundation: hierarchy-basics

A design token names a reusable value; a variant adapts a component to a supported context; a state describes its current interaction or data condition. Visual hierarchy is an intended ordering of emphasis, not evidence that a user found the correct action. Compare the actual task and content before using the familiar “one primary action” heuristic.

### Failure Signals

- P01: literals or invented token names bypass the catalog.
- P06: a system/library/token-scale change has no recorded alternatives or consequences.
- P09: layout depends on space but no responsive behavior is specified.
- P10: a reachable empty/loading/error state has no defined feedback.
- A cleaner-looking screen is reported as a proven usability improvement without task evidence.

### Evidence And Stop Conditions

- **Verify:** Inspect rendered states, actual content, layout under required space/zoom/text sizes, token existence, contrast pairs, and affected consumers. A screenshot establishes visual evidence, not task success or complete accessibility.
- **Stop:** Pause a material system/library/token-scale change without its required decision and migration evidence. Stop polishing when the agreed task and quality criteria are satisfied; record remaining hypotheses.

## Component: accessibility

### Mental Model

- **Observe:** Identify semantic roles, accessible names, focus order, keyboard interactions, text/non-text contrast pairs, meaningful imagery, and the assistive workflows in scope.
- **Mechanism:** Missing names, focus movement, or keyboard behavior can prevent an intended action even when the screen looks correct. Adding ARIA does not repair an unsuitable interaction model or establish usable navigation.

### Standards

Apply `pack-ui-ux-accessibility` and all applicable Global Principles; optional support never relaxes them.

### Strategy

- **Choose:** Prefer native semantics; use the applicable, pinned APG pattern for custom behavior. Pair automated checks with manual keyboard and assistive-technology inspection, selecting checks from the actual component states.
### Judgment

- **Exception:** Only keys and states relevant to the chosen pattern need specification. A non-interactive decorative asset is not an actionable control; exclude it from the accessibility tree with the platform-appropriate mechanism. These distinctions do not relax the inherited baseline.

Hypothetical contrast: a native control with tested semantics and a custom composite control may need different verification work. A static A11y marker in either case does not establish keyboard behavior or conformance.

### Procedure: document-accessibility

#### Accessibility Doc Format (a11y.md)

- Structure: WCAG principles (Perceivable, Operable, Understandable, Robust) → Checklist per principle → Component-specific notes.
- Checklist item: `- [ ] {criterion}` với link WCAG Success Criterion số (vd `1.4.3`).
- Testing method ghi ngay sau criterion: `(test: axe-core / manual keyboard / screen reader VoiceOver)`.

### Foundation: semantics-basics

A semantic role describes what a control is; an accessible name identifies it; focus identifies the current keyboard target. A documentation note about these properties differs from inspecting behavior in the rendered interface. Consult the applicable platform pattern and current workspace baseline when a control or assistive workflow is unfamiliar.

### Failure Signals

- P02: keyboard behavior or visible focus is missing.
- P04: a required contrast pair is unmeasured or below the pack baseline.
- P07: generic or conflicting accessible names obscure the action.
- Placeholder-only labels or an automated pass are treated as complete accessibility evidence.

### Evidence And Stop Conditions

- **Verify:** Record the applicable criterion, tested state, method, environment, and actual result. Include focus entry/return, visible focus, labels, meaningful alternatives, and contrast measurements. Static note/ratio checks cannot prove WCAG conformance.
- **Stop:** Pause an accessibility acceptance claim when a required interaction or applicable criterion has not been tested. Keep untested platform/assistive combinations explicit instead of reporting universal compliance.

## Component: user-flows

### Mental Model

- **Observe:** Identify the persona/role, entry conditions, state transitions, permissions, pending operations, recovery paths, and observable completion condition. Read the requirement/state matrix rather than inventing it.
- **Mechanism:** A missing state or unlabeled branch makes implementation choose behavior implicitly. Pending, failed, and completed effects are different states; hiding that distinction can encourage duplicate actions or strand the user.

### Standards

Apply `pack-ui-ux-user-flows` and all applicable Global Principles; optional support never relaxes them.

### Strategy

- **Choose:** Use a numbered path for simple behavior and a state/flow diagram for meaningful branches, interruption, or resumption. Compare inline recovery, a separate step, or deferred work against the user task and permission model.
### Judgment

- **Exception:** Do not add arbitrary error-state quotas or an extra confirmation for every action. Reversible local actions and consequential external effects need different recovery/confirmation treatment, subject to the existing contract.

Hypothetical contrast: undo may be enough for a reversible local edit; an uncertain external operation may require checking its durable outcome before retry. Escalate when the recovery contract is not known.

### Procedure: document-user-flows

#### User Flow Format

- File naming: `{feature}-{persona}-flow.md` — vd `checkout-guest-flow.md`, `onboarding-new-user-flow.md`.
- Mỗi flow file: Context (1 đoạn) → Persona + Role → Preconditions → Flow diagram → Edge/Error paths → Exit states.
- **Diagram**: Mermaid `stateDiagram-v2` hoặc `flowchart TD` — ưu tiên stateDiagram cho screen-to-screen. Fallback sang numbered list nếu tool không render Mermaid.
- Decision point dạng câu hỏi: `Is user authenticated?` — branch `Yes →` / `No →`.
- Edge path heading: `## Edge & Error Paths` — liệt kê từng case với state + user feedback.

### Foundation: state-basics

A flow relates an actor, preconditions, actions, branches and exit states. Pending work is not a confirmed result. Distinguish the user-visible state from the durable external effect when an operation can time out or resume. A diagram is a model to validate rather than evidence that every transition works.

### Failure Signals

- P03: only success is modeled; validation, permission, interruption, or recovery is omitted where reachable.
- P08: generic “user” hides role-dependent behavior.
- P10: loading, empty, or error states exist in the data contract but not the flow.
- An Error heading is present while the actual recovery path remains undefined.

### Evidence And Stop Conditions

- **Verify:** Walk each reachable branch with its actor, preconditions, feedback, next action, and exit state. Use a prototype when interaction complexity warrants it; record task observations, failures, and untested branches.
- **Stop:** Pause implementation of a consequential branch when its authorization, durable effect, or recovery semantics are unresolved. Label hypothetical paths; do not present a diagram as an executed user test.

## Component: ux-writing

### Mental Model

- **Observe:** Inspect the user goal, surrounding controls, known system state, terminology, locale, accessible name, and the safe action the user can actually take.
- **Mechanism:** Copy creates expectations about state and available action. A claimed cause that is unknown, a misleading completion message, or an ambiguous label can send the user down the wrong path.

### Standards

Apply `pack-ui-ux-writing` and all applicable Global Principles; optional support never relaxes them.

### Strategy

- **Choose:** Describe the action/outcome in context; use a concise instruction for recoverable errors and an honest status when the user cannot fix the condition. Compare wording with the approved terminology and real layout.
### Judgment

- **Exception:** Generic labels can work when surrounding semantics make the accessible name clear. Do not fabricate a cause, promise recovery, or force a CTA into a state where no useful action exists.

Hypothetical contrast: a known input error can name the corrective action; an unknown service failure should not assert a cause. Choose wording from verified state, not an invented explanation.

### Procedure: document-ux-writing

#### UX Writing Format (ux-writing.md)

- Structure per pattern: **Intent** (1 câu) → **Examples** (✅ OK / ❌ Avoid) → **Rationale** (1-2 câu).
- Sections: Tone of Voice → Error Messages → Empty States → Loading States → CTAs → Tooltips → Notifications.
- Error message template: `[What happened]. [Why — nếu useful]. [What to do next].`
- Empty state template: `[No {item} yet]. [Action to create first one].`

### Foundation: copy-basics

An accessible name, visible label, status and error explanation serve different purposes. Ground them in the known system state and the actions actually available. Vocabulary is product-specific: a familiar term can have a different approved meaning in this workspace. Unknown causes remain unknown even when a plausible explanation would sound reassuring.

### Failure Signals

- P05: a stack trace, backend field, or unexplained technical error reaches the user.
- P07: an ambiguous CTA or accessible label fails to communicate its contextual action.
- A loading/empty/error message promises success or recovery that the system cannot provide.

### Evidence And Stop Conditions

- **Verify:** Check terminology, actual state/action linkage, truncation/localization, accessible names, and absence of backend jargon or sensitive detail. Record comprehension/task evidence separately from editorial preference.
- **Stop:** Pause publication of copy that asserts an unverified cause, completed effect, or unavailable next action. Seek the controlling product/security decision for material ambiguity rather than inventing one.
