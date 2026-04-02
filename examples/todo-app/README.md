# DevSpark Example: Todo App

This is a minimal example showing what a project looks like **after** DevSpark is installed. Use it as a reference for the expected directory structure, file contents, and 3-tier override system.

## What's Here

```text
examples/todo-app/
├── .devspark/                          ← Framework (removable)
│   ├── defaults/commands/              ← Stock prompts
│   │   ├── devspark.specify.md
│   │   ├── devspark.plan.md
│   │   └── devspark.implement.md
│   ├── memory/
│   │   └── constitution.md             ← Seed template
│   └── VERSION
├── .documentation/                     ← User work (never touched)
│   ├── memory/
│   │   └── constitution.md             ← Customized for this project
│   ├── commands/                       ← Team overrides (empty by default)
│   └── specs/                          ← Feature specs go here
├── .github/
│   └── agents/
│       └── devspark.specify.agent.md   ← Copilot shim example
└── README.md
```

## Key Concepts Demonstrated

1. **`.devspark/` vs `.documentation/`** — Framework files separate from user work
2. **Constitution** — `.documentation/memory/constitution.md` is customized with project-specific principles; the stock seed template lives in `.devspark/memory/constitution.md`
3. **Agent shim** — `.github/agents/devspark.specify.agent.md` shows the 3-tier resolution pattern
4. **VERSION stamp** — `.devspark/VERSION` records how and when DevSpark was installed

## Try It

Copy this directory into a fresh repo and start using DevSpark commands with your AI agent.
