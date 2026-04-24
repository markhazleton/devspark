## Source-repo guard

Check whether the directory `templates/commands/` exists in the current working directory.

**If it does exist** (you are inside the DevSpark source repository):

> **STOP — This is the DevSpark source repository.**
>
> You are already on the latest version by definition. The `upgrade` command is designed for consumer repos that install DevSpark as a framework — it has no meaning here.
>
> If you want to bump the version number, edit `CHANGELOG.md` and `.devspark/VERSION` directly.

Stop here. Do not proceed further.

---

**If it does not exist** (you are in a consumer repo), read and follow the instructions from the **first file that exists**:

1. `.documentation/$GITUSER/commands/devspark.upgrade.md` (personalized override — determine `$GITUSER` by running `git config user.name`, then normalize: lowercase, spaces → hyphens, strip non-alphanumeric/hyphen characters)
2. `.documentation/commands/devspark.upgrade.md` (team customisation)
3. `.devspark/defaults/commands/devspark.upgrade.md` (stock default)

## User Input

$ARGUMENTS
