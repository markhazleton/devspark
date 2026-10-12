"""Reference fixture: python-token-v1 canonicalizes past comments and whitespace."""


def add(a, b):
    # This comment carries no behavioral meaning under python-token-v1.
    return a + b
