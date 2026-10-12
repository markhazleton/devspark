"""Reference fixture: a claim pinning a region name absent from this file (e.g. `missing`)
widens to the whole file and the run emits a `region-widened` advisory."""


def present():
    return 1
