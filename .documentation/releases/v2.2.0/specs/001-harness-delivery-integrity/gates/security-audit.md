# Security Audit: Subprocess Injection Risk in validation.py

**Date**: 2026-04-29  
**Scope**: src/devspark_cli/harness/validation.py  
**Classification**: Medium Risk / Mitigated by Design

## Findings

### F-1: shell=True with Arbitrary Commands

**Location**: Lines 87-99 (command.pass rule type)  
**Severity**: Medium  
**Description**: The validation engine executes arbitrary commands from harness specs using `shell=True`.

```python
completed = subprocess.run(
    rule.command,
    cwd=repo_root,
    shell=True,
    text=True,
    errors="replace",
    capture_output=True,
    check=False,
    timeout=timeout_seconds,
)
```

**Injection Vector**: If rule.command contains shell metacharacters (e.g., `; rm -rf /`), they execute.
**Mitigation**:

- Rules are defined in committed YAML specs, not user-provided at runtime
- Injection vector is limited to developers with repository write access
- Harness runs are typically executed in isolated environments or by trusted automation

**Recommendation**:

- Document that rule commands are trusted (from spec definitions)
- Add lint check in spec-validation-contract.md to warn on suspicious commands
- Consider using shlex.quote() for any dynamic path interpolation in future

### F-2: shell=True with Grader Commands

**Location**: Lines 203-217 (grader rule type)  
**Severity**: Medium  
**Description**: The validation engine executes grader commands from harness specs using `shell=True` with piped input.

```python
completed = subprocess.run(
    rule.grader_command,
    shell=True,
    input=grading_prompt,
    text=True,
    errors="replace",
    capture_output=True,
    check=False,
    cwd=repo_root,
    timeout=rule.timeout_seconds or 300,
)
```

**Injection Vector**: Similar to F-1; grader_command comes from spec definition.  
**Mitigation**: Same as F-1.

**Recommendation**:

- Document that grader commands are trusted
- Ensure grader_command validation is in spec-validation-contract.md

## Current Mitigations in Place

1. **No shell=True with user input**: User-provided values (e.g., paths, branch names) are passed as arguments, not shell commands
2. **Git commands use array form**: Git diff commands (lines 138, etc.) use `["git", ...]` array syntax instead of shell
3. **Path arguments use shlex semantics**: Path arguments to git are passed safely
4. **Timeout protection**: All subprocess calls include timeout_seconds to prevent hang attacks

## Assessed Risk

**Overall Risk Level**: LOW

**Reasoning**:

- Attack surface limited to developers with repo write access (who can already inject code)
- Harness execution environment is typically controlled (CI/CD, local dev)
- No end-user input flows into shell commands
- Existing test harnesses have established safe patterns

## Recommended Actions

1. ✅ **DONE**: Document shell=True usage in code comments
2. ✅ **DONE**: Verify all user-controlled paths use non-shell subprocess calls
3. ✅ **DONE**: Add timeout protection (already present)
4. 📋 **TODO**: Add spec-level validation to warn on suspicious command patterns (out of scope for PR1)
5. 📋 **TODO**: Future: Replace shell=True with shlex.quote() pattern if dynamic interpolation added (Phase 4+)

## Verification Checklist

- [x] No shell=True with pathlib.Path objects
- [x] No shell=True with external environment variables
- [x] All timeout parameters present
- [x] All commands use capture_output=True for safety
- [x] errors="replace" prevents decode crashes
- [x] Git operations use array syntax (not shell)
- [x] Cwd parameter properly set for all operations

## Conclusion

Current subprocess usage in validation.py follows security best practices for developer-trusted rule definitions. The existing mitigations are sufficient for PR1. Future enhancements (dynamic command interpolation, user-defined rule injection) would require additional hardening.
