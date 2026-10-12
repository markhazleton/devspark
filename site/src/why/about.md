# About, Architecture and Controls

DevSpark is a Make Bold Solutions toolkit for AI-assisted software delivery. Its versioned markdown prompts, templates, and helper scripts provide a repeatable workflow from requirements through release. Adoption is voluntary per repository.

## Current status

- **Maintainer:** [Mark Hazleton](https://markhazleton.com), through the [DevSpark GitHub repository](https://github.com/MarkHazleton/DevSpark). The toolkit began from Spec Kit and has been substantially rebuilt.
- **Lifecycle stage:** maintained as an open-source, prompt-first engineering toolkit.
- **Feedback:** open an issue or pull request against the repository (see [Contributing](https://github.com/MarkHazleton/DevSpark/blob/main/CONTRIBUTING.md)). Git, release notes, and work-item systems retain history.
- **Audiences:** developers should start with [Evaluate One Task](../get-started/evaluate-one-task.md); managers with [How to Evaluate](evidence.md); architecture and security reviewers with the sections below.

## Ownership and hosting

- **Build:** a CI pipeline in the repository builds the documentation site, per-agent template packages, and the prompt-first `/raw` distribution tree as one artifact.
- **Hosting:** the public documentation and distribution site is [dev.makeboldspark.com](https://dev.makeboldspark.com), built for GitHub Pages.
- **Versioning:** releases are tagged `vX.Y.Z` ([Semantic Versioning](https://semver.org/)). `dist/manifest.json` exposes the current `latest`, and each consuming repository records its installed version in `.devspark/VERSION`.
- **Change approval:** normal GitHub pull requests, subject to the repository's branch policies.
- **Access:** public documentation and framework distribution; consumer repositories retain their own access controls.

## What it adds to a repository

The core workflow is versioned markdown and scripts that a developer uses through an AI coding assistant they already have (GitHub Copilot, Claude Code, Cursor, and others). It adds no runtime dependency, service, binary, or package reference, and makes no network call of its own.

Four folders define ownership, all plain files under normal repository controls:

| Folder | Holds |
|---|---|
| `.devspark/` | Static snapshot of prompt defaults, templates, and scripts. Replaceable framework files |
| `.devspark.work/` | Temporary plans, gates, configuration, registries, and skill prompt or script overrides |
| `.knowledge/` | Current authoritative technical and governance truth, plus published guidance under `.knowledge/guides/` |
| `.archive/` | Old work products, grouped by release |

Once copied, there is no runtime link back to the canonical repository. Updating is a deliberate, developer-initiated action, and uninstalling removes only `.devspark/`. Skill prompt instructions resolve through a three-tier chain: personal overrides in `.devspark.work/{git-user}/commands/`, then team overrides in `.devspark.work/commands/`, then stock defaults. The agent performs the work; a `/devspark-*` slash command invokes the skill. See [Terminology](../guides/prompt-lifecycle-mapping.md#terminology).

## Data handling

- The site hosts methodology documentation and distribution artifacts only: quickstart guides, prompt text, templates, scripts, and release packages. It does not host consumer application source or business data.
- DevSpark does not transmit repository content. The AI assistant a developer uses processes repository context under its own approved enterprise configuration, exactly as it would without DevSpark present.
- Follow your organization's guidance on what may be shared with an AI assistant. Write specs and plans like any other repository documentation: no secrets, credentials, or protected data.

## Existing controls

DevSpark operates within existing engineering controls and does not replace or bypass them: identity and access management, repository permissions and branch protections, pull-request review, secure coding requirements, dependency scanning, test requirements and CI gates, release pipelines, and production access controls.

Durable changes are reviewed and merged through the same pull-request process as any other change. Temporary plans stay under `.devspark.work/` until `/devspark-release` archives them under `.archive/{YYYY-MM-DD}/`. Nothing auto-commits, auto-approves, or auto-deploys.

## Review status

The design minimizes added runtime and supply-chain risk, but that intent is not a completed formal review. No security or architecture approval is currently documented or linked here, and none should be inferred. Teams that require one before adopting should treat it as an open item and route it through their normal review process.

## Common questions

<details>
<summary>Is there a cost or vendor relationship?</summary>

No. It is free to use under the MIT license, with no license fee, subscription, contract, or external vendor.
</details>

<details>
<summary>What if the maintainer stops maintaining DevSpark?</summary>

The canonical repository is available on GitHub. Files already in a consuming repository are static text with no external dependency, so they keep working even if the source were no longer maintained.
</details>

<details>
<summary>Does adopting it create a dependency my team does not control?</summary>

No. The files are copied into the repository, and there is no connection back to the distribution site afterward.
</details>

<details>
<summary>Can the constitution enforce standards more broadly?</summary>

A repository's constitution (`.knowledge/governance/constitution.md`) is read by the agent when running skills for specification, implementation, and PR review in that repository. Enforcement beyond a single repository is a question for Dev Infrastructure, not a capability operated at that scale today.
</details>

## Related pages

- [How It Works](../get-started/how-it-works.md)
- [Philosophy](philosophy.md) and [FAQ](faq.md)
- [Repository](https://github.com/MarkHazleton/DevSpark)
