# Dogfooding DevSpark

How we set up the DevSpark source repository to use its own spec-driven workflow — and what happens when your development process tool becomes both the product and the workbench.

## Eating Your Own Dog Food

The term "dogfooding" has been floating around the software industry since at least 1988, when Microsoft manager Paul Maritz sent an email titled "Eating our own Dogfood" urging the company to increase internal use of its own products. The origin story people love to tell is that it came from a Kal Kan pet food executive who supposedly ate his own company's dog food at shareholder meetings to prove its quality. Whether that's true or apocryphal, the metaphor stuck.

Over the decades, the practice has gone by many names:

- **Eating your own dog food** — The original, still the most common. Blunt. Effective.
- **Drinking your own champagne** — The optimistic European rebrand. Same idea, better taste.
- **Icecreaming** — Google's preferred term for a while, because who wants to think about dog food?
- **Eating your own cooking** — The polite version you use in executive presentations.
- **Self-hosting** — The compiler community's term, where building a compiler with itself is a rite of passage.
- **Bootstrapping** — Related but distinct. When a system can build itself from scratch, like a compiler that compiles its own source code.

The core idea is always the same: if you won't use your own product, why should anyone else?

## Building the Plane While Flying It

Remember those old EDS commercials? A team of engineers rebuilding a fighter jet's engine mid-flight, swapping out parts while the plane screams through the sky. The tagline was something like "We solve complex problems." It was absurd. It was memorable. And it's a surprisingly good metaphor for what happens when you try to use a development tool to develop that same tool.

Here's the fundamental tension: DevSpark is a spec-driven development workflow.
The current source set has 30 active commands that guide you from feature
specification
through implementation, review, and release. When we decided to use DevSpark to
build DevSpark, we immediately hit a question that doesn't come up in normal
projects:

**Which version of the tool are you using — the one you shipped, or the one you're changing right now?**

In most dogfooding scenarios, this isn't complicated. Microsoft uses Windows to build Windows, but the Windows build system is a separate thing from the product. Slack uses Slack for internal communication, but the act of sending messages doesn't modify Slack's source code. The tool and the product occupy different layers.

DevSpark doesn't have that luxury. The prompts ARE the product. When you type `@devspark.specify` to write a spec for a new DevSpark feature, the prompt that runs is the exact same file you might be editing. Change a word in the prompt template, and the next time you invoke the command, you get the new behavior. There's no build step, no compilation, no deployment pipeline between "edit" and "experience."

It's like being the pilot AND the mechanic AND the engine designer, all at 30,000 feet.

## The Meta Challenges

### The Stale Copy Trap

DevSpark's normal install process copies stock prompts into `.devspark/defaults/commands/`. For consumer repos, this is perfect — you get a stable snapshot of the framework. But in the source repo, those copies become a trap. Edit `templates/commands/specify.md` to improve the spec workflow, forget to re-copy it to `.devspark/defaults/commands/devspark.specify.md`, and suddenly you're testing yesterday's prompt while thinking you're testing today's. You fix a bug, it still fails, and you spend twenty minutes debugging code that was already correct because the old prompt was still running.

We've all been there with other tools. "Did you rebuild?" "Did you restart the server?" "Are you sure you're hitting the right endpoint?" Stale copies are a universal developer experience, and in a prompt-driven system they're invisible — there's no compiler error, no 404, just subtly different behavior.

### The Override Paradox

DevSpark has a clever 3-tier override system. Personal overrides shadow team overrides, which shadow stock defaults. Great for customization. Terrible for dogfooding. If someone creates a personal override to test a prompt variation, they're no longer testing the source. Worse, they might not realize it. The override system is doing exactly what it's designed to do — it's just doing it at the worst possible time.

### The Source Maintenance Boundary

DevSpark install, upgrade, and repair behavior belongs to quickstart prompts for
consumer repositories. In the source repo, those maintenance flows are
philosophically incoherent: you cannot refresh to the latest framework when you
are editing the framework source itself. Source maintenance happens by editing
templates, scripts, quickstarts, tests, `.knowledge`, and `.devspark/VERSION`
directly.

### The Chicken-and-Egg Spec Problem

Want to use `/devspark.specify` to write a spec for improving `/devspark.specify`? That's perfectly valid — and perfectly recursive. The spec you write will be guided by the current version of the specify prompt. If the specify prompt has a flaw you're trying to fix, the spec it generates might inherit that flaw. You're using a broken tool to write the repair manual for the broken tool.

This isn't theoretical. It happens. The solution is awareness: know that the output is shaped by the current prompt, review it with fresh eyes, and don't trust the tool more than your own judgment.

## Our Solution: Cut the Indirection

The answer turned out to be simple: stop pretending this is a consumer repo.

Instead of copying prompts into `.devspark/defaults/commands/` and running them through the override chain, every agent shim in the DevSpark source repo points directly at the source file:

**GitHub Copilot** (`.github/agents/devspark.specify.agent.md`):

```markdown
Read and follow the instructions in `templates/commands/specify.md` exactly.
```

**Claude Code** (`.claude/commands/devspark.specify.md`):

```markdown
Read and follow the instructions in `templates/commands/specify.md` exactly.

User input: $ARGUMENTS
```

No override chain. No copied files. No indirection. Edit `templates/commands/specify.md`, invoke `@devspark.specify`, and you're running the code you just wrote. The feedback loop is as tight as it can possibly be.

### What We Didn't Create

| Directory | Why it doesn't exist here |
|-----------|--------------------------|
| `.devspark/defaults/commands/` | Shims point at `templates/commands/` directly |
| `.devspark/scripts/` | Scripts live at `scripts/` (the source) |
| `.devspark/templates/` | Templates live at `templates/` (the source) |

Only `.devspark/VERSION` and `.devspark/schemas/` exist — metadata that doesn't duplicate source content.

### Commands That Got a Bouncer

Some commands don't make sense in the source repo. Rather than let them run and cause confusion, we gave them guard clauses — a **STOP** message that explains why and points you to the right alternative:

| Command | Why it's blocked | What to do instead |
|---------|-----------------|-------------------|
| `personalize` | Overrides would shadow source | Edit `templates/commands/{name}.md` directly |
| `add-application` | Not a multi-app monorepo | Test with `tests/fixtures/` or `examples/todo-app/` |
| `list-applications` | Same | Same |
| `discover-constitution` | Constitution already exists as the source | Use `evolve-constitution` or edit directly |

The remaining active commands work normally, resolving straight to source.

## Living With the Recursion

Dogfooding DevSpark hasn't been a one-time setup. It's an ongoing practice that surfaces issues you'd never find from the outside:

- **Prompt wording matters more than you think.** When you're the one following your own instructions, you notice every ambiguous phrase, every missing context hint, every assumption that made sense when you wrote it but confuses the agent in practice.
- **The constitution is real.** DevSpark's constitution defines non-negotiable principles. When you're using the tool to build the tool, constitutional violations are immediately obvious — you feel them in your workflow, not just in a review checklist.
- **Guard clauses teach by blocking.** Every time someone hits a STOP message, they learn something about the difference between the source repo and a consumer repo. That distinction matters for contributors.

The EDS tagline was right, if a bit dramatic. We are building the plane while flying it. The trick is making sure every bolt you replace is the one that's actually installed, not a copy you made last week.

## Consumer Repos vs. Source Repo

For reference, here's how resolution differs:

| Aspect | Consumer repo | DevSpark source repo |
|--------|--------------|---------------------|
| Stock commands | `.devspark/defaults/commands/` (copied) | `templates/commands/` (source) |
| Scripts | `.devspark/scripts/` (copied) | `scripts/` (source) |
| Templates | `.devspark/templates/` (copied) | `templates/` (source) |
| Override chain | 3-tier (personal → team → stock) | None — always source |
| Quickstart maintenance | Refreshes `.devspark/` from latest release | Edit source files directly |
| Personalize command | Creates user override files | Blocked — edit source directly |
