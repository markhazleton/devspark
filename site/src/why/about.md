# About, Architecture and Controls

DevSpark is an internally developed, optional engineering toolkit maintained in the DevSpark
development environment. It combines reusable skills, versioned Markdown instructions, templates,
and helper scripts used with an AI coding assistant. Its purpose is to help developers create and
assess trustworthy software changes—not to require one prescribed specification-first sequence.

DevSpark is not a program, subscription, or mandated DevSpark-wide standard. Adoption is voluntary per
repository; repositories that do not adopt it are unaffected.

## Current status

- **Maintainer:** [DevSpark on GitHub](https://github.com/MarkHazleton/DevSpark) is maintained by Make Bold Solutions. It began from Spec Kit, an open-source specification-driven development starter, and has been substantially rebuilt.
- **Use:** adopted voluntarily by teams in Make Bold Solutions. Formal enterprise security or architecture approval is not documented here; see [Review status](#review-status).
- **Feedback:** use repository issues or pull requests; see
  [Contributing](https://github.com/MarkHazleton/DevSpark/blob/main/CONTRIBUTING.md).
  Git, releases, and existing work-management systems retain delivery history.
- **Start here:** developers can try [Evaluate One Task](../get-started/evaluate-one-task.md);
  managers can use [How to Evaluate](evidence.md); architecture and security reviewers can use
  the operating boundaries below.

## What DevSpark is trying to improve

A **Delta** is an intentional software change. Developers may discover it through formal
requirements, exploratory code, a production defect, or an experiment. DevSpark provides
engineering assistance appropriate to the journey, then seeks credible evidence about the Delta
and its **blast radius**—the behavior, contracts, dependencies, data, and failure paths it can
actually affect.

The enduring assets are **code, tests, and current durable Knowledge**. Specs, plans, task lists,
and review records may help create those assets, but completing paperwork is not proof of software
quality. The goal is to validate the change, preserve relevant understanding, and stop once the
required confidence and decisions exist.

This is the [Vision and Manifesto](philosophy.md). It is also a direction for the tool's evolution:
existing skills do not all implement modality-independent Delta assurance today. The exact
capabilities depend on the installed version and commands.

## Ownership and hosting

- **Build:** repository CI builds the documentation site, per-agent template packages, and
  prompt-first `/raw` distribution tree together.
- **Hosting:** the public site is published through GitHub Pages at
  [dev.makeboldspark.com](https://dev.makeboldspark.com) by Make Bold Solutions.
- **Versioning:** releases use `vX.Y.Z` tags ([Semantic Versioning](https://semver.org/)).
  `dist/manifest.json` exposes `latest`, and consuming repositories record their installed version
  in `.devspark/VERSION`.
- **Approval:** changes to the framework follow GitHub pull requests and repository branch
  protection rules.
- **Access today:** the published site is publicly reachable during the current validation period.
  Microsoft Entra ID and network restrictions are not currently implemented for the site; it must
  not be described as private or internal-network-only.

## What it adds to a repository

Developers invoke `/devspark-*` skills through an AI coding assistant they already use, such as
GitHub Copilot, Claude Code, or Cursor. The installed framework is prompt instructions, templates,
and scripts—not an application runtime, subscription service, or agent-hosting dependency.

| Folder | Ownership and purpose |
|---|---|
| `.devspark/` | Installed framework instructions, templates, and scripts; replaceable on upgrade |
| `.devspark.work/` | Repository-owned temporary plans, review records, configuration, and overrides |
| `.knowledge/` | Repository-owned authoritative current software and governance Knowledge, plus published guides |
| `.archive/` | Repository-owned inactive historical work products |

Once installed, the framework works from its local files; there is no runtime connection back to
the canonical DevSpark repository. Updates are developer-initiated. Skills resolve personal prompt
overrides under `.devspark.work/{git-user}/commands/`, then team overrides under
`.devspark.work/commands/`, then stock defaults in `.devspark/`. See
[Terminology](../guides/prompt-lifecycle-mapping.md#terminology).

Framework upgrades own `.devspark/`, not the repository's Knowledge, work products, or archives.

## Data handling

The website distributes methodology documentation and framework artifacts; it does not host DevSpark
application source or business data. DevSpark itself does not transmit repository content.
The AI assistant selected by the developer processes context according to its own enterprise
configuration and approved usage.

Existing DevSpark restrictions still govern what may be submitted to an AI assistant. Do not place
secrets, credentials, or protected data in specifications, Knowledge, or prompts.

## Assurance and existing controls

DevSpark does not replace identity management, repository permissions, branch protection,
independent human review where required, secure coding, dependency scanning, build and test
checks, release pipelines, or production access controls.

Accountable humans set the standing expectations for acceptable risk and evidence. Agents may
recommend scope and run checks but cannot waive mandatory obligations or claim unrecorded human
approval. A second AI model can offer independent reasoning, but it does not replace tests or
real-world observations when those are required.

Some controls are expressed as prompt instructions and are not automatically enforced by the
hosting platform. A contributor may bypass optional DevSpark commands; applicable repository CI
and branch policies are what technically prevent a merge. DevSpark does not auto-approve,
auto-merge, or auto-deploy.

Temporary work products are retained or archived under the repository's current lifecycle rules;
durable Knowledge is maintained as current truth, not as a record of every historical workflow.

## Review status

The design aims to minimize additional runtime and supply-chain dependencies, but that intent is
not a completed formal review. No enterprise-wide security or architecture approval is linked or
documented here; none should be inferred. Teams requiring such approval should route it through
their established process before adoption.

## Common questions

<details>
<summary>Is there a cost or external vendor relationship?</summary>

No fee, subscription, or external DevSpark vendor is required. The framework is maintained
internally; developers use AI coding assistants under their existing approved arrangements.
</details>

<details>
<summary>What if the maintainer leaves DevSpark?</summary>

The source repository is DevSpark-owned. Installed files remain local to their consuming repositories
and do not depend on the maintainer's continued availability.
</details>

<details>
<summary>Does adoption create a service dependency DevSpark does not control?</summary>

No DevSpark service must remain available for the installed instructions and scripts to run.
The chosen AI assistant and existing toolchain retain their own dependencies and controls.
</details>

<details>
<summary>Does the Constitution enforce enterprise-wide standards?</summary>

No. Repository governance applies through the installed skills and the repository's existing
technical controls. Enterprise-wide enforcement is not a capability DevSpark operates today.
</details>

## Related pages

- [Vision and Manifesto](philosophy.md) and [FAQ](faq.md)
- [How to Evaluate](evidence.md)
- [How It Works](../get-started/how-it-works.md)
- [Repository](https://github.com/MarkHazleton/DevSpark)
