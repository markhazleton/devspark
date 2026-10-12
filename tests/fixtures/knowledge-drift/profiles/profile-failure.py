"""Reference fixture: unterminated syntax makes python-token-v1 unable to tokenize this
file. canonicalize_source falls back conservatively to exact-text-v1 rather than silently
treating the difference as non-behavioral."""


def broken(
    return 1
