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
│   └── VERSION
├── .knowledge/                         ← Durable current truth
│   └── governance/
│       └── constitution.md             ← Customized for this project
├── .devspark.work/                     ← Temporary lifecycle work (ignored)
│   └── specs/                          ← In-flight feature packages
├── .knowledge/                     ← Durable current truth
│   └── commands/                       ← Team prompt overrides
├── .github/
│   └── agents/
│       └── devspark.specify.agent.md   ← Copilot shim example
└── README.md
```

## Key Concepts Demonstrated

1. **`.devspark/` vs `.knowledge/` vs `.devspark.work/`** — framework files, durable current truth, and temporary work state stay separate
2. **Constitution** — `.knowledge/governance/constitution.md` is customized with project-specific principles
3. **Agent shim** — `.github/agents/devspark.specify.agent.md` shows the personal/team/stock resolution pattern
4. **VERSION stamp** — `.devspark/VERSION` records how and when DevSpark was installed

## Try It

Copy this directory into a fresh repo and start using DevSpark commands with your AI agent.
