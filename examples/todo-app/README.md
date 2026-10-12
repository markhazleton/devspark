# DevSpark Example: Todo App

This is a minimal example showing what a project looks like **after** DevSpark is installed. Use it as a reference for the expected directory structure, file contents, and personal/team/stock prompt resolution.

## What's Here

```text
examples/todo-app/
├── .devspark/                          ← Framework (removable)
│   ├── defaults/commands/              ← Stock prompts
│   │   ├── devspark.specify.md
│   │   ├── devspark.plan.md
│   │   └── devspark.implement.md
│   └── VERSION            ← Installed version stamp
├── .devspark.work/                     ← Temporary work and overrides
│   ├── commands/                       ← Team overrides (empty by default)
│   └── specs/                          ← Temporary plans go here
├── .knowledge/
│   └── governance/constitution.md      ← Current project principles
├── .knowledge/guides/                  ← Published user guidance
├── .github/
│   └── skills/
│       └── devspark-specify/SKILL.md   ← Copilot skill example
└── README.md
```

## Key Concepts Demonstrated

1. **Four roots** — Framework, temporary work, current truth, and published guidance stay separate
2. **Constitution** — `.knowledge/governance/constitution.md` contains current project principles
3. **Agent skill** — `.github/skills/devspark-specify/SKILL.md` shows the personal/team/stock resolution pattern
4. **VERSION stamp** — `.devspark/VERSION` records how and when DevSpark was installed

## Try It

Copy this directory into a fresh repo and start using DevSpark commands with your AI agent.
