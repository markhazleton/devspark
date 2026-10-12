// Reference fixture: python-token-v1 cannot tokenize a non-Python file.
// canonicalize_source falls back conservatively to exact-text-v1 for this extension.
fn add(a: i32, b: i32) -> i32 {
    a + b
}
