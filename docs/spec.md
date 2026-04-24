# TALKPIK AI Frontend Specification

## Status

This is the current implementation spec for the app in this repository.

For new UI work, treat this file and `docs/ant-design/` as the active source of
truth.

Older references to `shadcn/ui`, `Tailwind CSS`, `Supanova`, or static `.html`
routes are historical notes only. They may still appear in legacy observation
docs, but they are not the implementation standard for new work.

## 1. Product Goal

TALKPIK AI is a learning workspace for TOPIK preparation.

The product is not a marketing landing page. It is a repeat-use study tool that
must help the learner:

- understand what to do next,
- generate and solve problems quickly,
- practice writing with draft safety,
- review AI feedback and weak points,
- revisit saved materials and vocabulary,
- and move between tasks without losing context.

## 2. Current Frontend Stack

The active frontend stack is:

- `React` for page and component rendering.
- `TypeScript` for typed component props, state, and domain models.
- `Zustand` for shared client state such as user info, learning progress,
  writing drafts, and current task state.
- `Ant Design` as the primary UI component system.
- `Ant Design theme tokens` and `ConfigProvider` for light/dark theme control.
- Minimal project CSS for layout glue only, not for replacing Ant Design's
  design system.

## 3. UI Implementation Rules

Use these rules for all new UI work:

- Use Ant Design components before building custom UI.
- Use Ant Design theme tokens before hardcoded colors, shadows, radii, or
  spacing.
- Keep theme decisions centralized under `src/theme/`.
- Prefer page composition with Ant Design layout primitives such as `Layout`,
  `Row`, `Col`, `Flex`, `Space`, `Card`, `Form`, `Table`, `Tabs`, `Drawer`,
  `Modal`, `Descriptions`, `Statistic`, `Alert`, `Result`, and `Progress`.
- Do not introduce deprecated Ant Design components in new UI work.
- Include loading, empty, error, success, and disabled states.
- Verify desktop and mobile layout before calling UI work complete.

Detailed policy lives in:

- `docs/ant-design/README.md`
- `docs/ant-design/03-patterns-and-components.md`
- `docs/ant-design/06-ai-development-workflow.md`
- `docs/ant-design/07-review-checklist.md`
- `docs/ant-design/08-theme-architecture.md`

## 4. Current Source Structure

Current source-of-truth structure for app UI:

```text
src/
  components/
    ai-tutor/
    app/
    shared/
  pages/
  stores/
  styles/
  theme/
  types/
```

Meaning of the main folders:

- `src/components/app/`: app shell pieces such as sidebar, header, and settings.
- `src/components/ai-tutor/`: AI tutor panel and related helper UI.
- `src/components/shared/`: reusable UI blocks shared by multiple pages.
- `src/pages/`: route-level screens that users navigate to directly.
- `src/stores/`: Zustand stores, which are shared state containers.
- `src/styles/`: minimal global CSS used only where component-level layout glue
  is necessary.
- `src/theme/`: Ant Design theme setup, token composition, and theme presets.
- `src/types/`: shared TypeScript types.

## 5. Current Shared State Model

Current Zustand stores:

- `useUserStore`: learner profile, plan, language, and goal basics.
- `useLearningStore`: dashboard learning metrics and current progress.
- `usePracticeStore`: reading/listening problem generation and solving state.
- `useWritingStore`: writing setup, draft, autosave, and submission flow.
- `useFeedbackStore`: writing feedback list and detail state.
- `useAiTutorStore`: AI tutor panel state and conversation context.
- `useThemeStore`: light/dark theme preference.

Store design rules:

- Keep stores focused by product area.
- Do not duplicate server-derived data unless the UI needs temporary local
  interaction state.
- Keep draft-like user input recoverable.
- Keep route-level pages thin; state transitions belong in stores or focused
  feature helpers.

## 6. Current Route Inventory

Current React routes are defined in `src/App.tsx`.

### Main workspace routes

- `/` - home dashboard
- `/home-v2` - alternate writing-focused dashboard variant
- `/practice/create` - AI problem generation
- `/practice/solve` - generated problem solving
- `/writing/setup` - writing practice setup
- `/writing/51` - writing practice for type 51
- `/writing/52` - writing practice for type 52
- `/writing/53` - writing practice for type 53
- `/writing/54` - writing practice for type 54

### Feedback and review routes

- `/writing/feedback` - writing feedback list
- `/writing/feedback/:id` - writing feedback detail
- `/library` - saved problem library
- `/vocabulary` - vocabulary review

### Exam and support routes

- `/mock/results` - mock exam result dashboard
- `/mock/exam` - live mock exam mode
- `/board` - notices and board content
- `/profile` - profile and settings

If another document shows static routes such as `/home.html`, treat those as
legacy observed-site references. Use `src/App.tsx` and `docs/sitemap.md` for
the current route map.

## 7. Current Page Inventory

Current route screens live in `src/pages/`:

- `HomePage.tsx`
- `PracticeCreatePage.tsx`
- `PracticeSolvePage.tsx`
- `WritingSetupPage.tsx`
- `WritingPracticePage.tsx`
- `WritingFeedbackListPage.tsx`
- `WritingFeedbackDetailPage.tsx`
- `MockExamPage.tsx`
- `LibraryPage.tsx`
- `VocabularyPage.tsx`
- `BoardPage.tsx`
- `ProfileSettingsPage.tsx`

## 8. Core UX Expectations

Every major page should answer a clear user question:

- dashboard: "What should I do now?"
- generation/setup pages: "What should I choose before I start?"
- solving/writing pages: "What do I do right now?"
- feedback/detail pages: "What happened, and what should I improve next?"
- library/vocabulary pages: "What should I review or revisit?"

Implementation expectations:

- Keep primary task actions more visible than secondary actions.
- Keep navigation stable across the workspace.
- Do not let helper UI block critical actions.
- Use predictable labels for TOPIK level, question type, writing type, score,
  status, and review state.
- Keep long-form writing input safe with draft preservation or autosave cues.

## 9. Theme And Styling Boundaries

Theme and styling rules for this repository:

- Ant Design is the first styling system.
- `src/theme/` is the theme control point.
- `global.css` must not become a second design system.
- Visual styling should not be rebuilt with large custom wrappers when Ant
  Design already provides the pattern.
- Visual inline styles are still custom styling and should be minimized.

Read `docs/ant-design/08-theme-architecture.md` before changing theme structure
or token usage.

## 10. Validation Before Completion

Before calling frontend work complete:

- run the relevant build or validation command,
- check desktop layout,
- check mobile layout,
- apply `docs/ant-design/07-review-checklist.md`,
- and report:
  - what works,
  - what does not work yet,
  - what risk remains.

## 11. Relationship To Legacy Docs

These docs still matter, but they are not equal in role:

- `docs/prd.md`
- `docs/ia.md`
- `docs/user-flow.md`
- `docs/sitemap.md`
- `docs/ia-pages/`

Use them as product observation and route/reference context.

For implementation choices such as component selection, theme usage, layout
strategy, and UI review, follow this file plus `docs/ant-design/`.
