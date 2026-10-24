# Feature Modules

Each business feature (auth, jobs, candidates, employees, knowledge...)
gets its own directory here, self-contained:

```
features/
  jobs/
    components/
    hooks/
    services/
    types/
```

No `pages/candidate.tsx`-style monoliths — everything a feature needs
lives together. See Product Book §07 (Feature Specification) and
CLAUDE.md Engineering Principles for the reasoning.

Empty in Slice 0 — populated starting Slice 1 (Authentication & Identity).
