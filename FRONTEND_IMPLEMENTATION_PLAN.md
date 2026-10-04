# Frontend Implementation Plan

Admin dashboard for staff. Users chat in WhatsApp itself; no end-user frontend.

Stack: React 18, Vite, TypeScript, React Router, TanStack Query, Tailwind, shadcn/ui, react-hook-form + zod, Vitest, Playwright.

Timeline: ~7 working days after backend admin API exists.

## Folder structure

```
web/
  src/
    api/
      client.ts            # fetch wrapper, cookie auth, error handling
      types.ts             # shared API types
      conversations.ts     # query + mutation hooks
      kb.ts
      settings.ts
      analytics.ts
    auth/
      AuthProvider.tsx
      RequireAuth.tsx
      useAuth.ts
    features/
      inbox/
        InboxPage.tsx
        ConversationList.tsx
        ConversationItem.tsx
        Thread.tsx
        MessageBubble.tsx
        Composer.tsx
        WindowBadge.tsx    # 24h window status
        TakeoverButton.tsx
      kb/
        KbPage.tsx
        KbEditor.tsx
      settings/
        SettingsPage.tsx
        PromptEditor.tsx
        PromptHistory.tsx
      contacts/
      tools/
      analytics/
    hooks/
      useSSE.ts
      useDebounce.ts
    components/            # shared UI (shadcn wrappers)
    lib/                   # utils, formatters (phone mask, dates)
    mocks/                 # MSW handlers
    routes.tsx
    main.tsx
  e2e/
  vite.config.ts
  .env.example
```
