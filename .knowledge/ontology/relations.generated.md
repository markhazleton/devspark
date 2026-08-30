# Entity Relations

| Subject | Type | Object |
|---|---|---|
| `agent-shims` | derives_from | `command-templates` |
| `application-registry` | scopes | `work-packages` |
| `brand-system` | supports | `product-documentation` |
| `command-templates` | generated_for | `agent-shims` |
| `current-truth-ontology` | validates | `command-templates` |
| `current-truth-ontology` | validates | `work-packages` |
| `developer-workflow` | uses | `command-templates` |
| `extension-catalog` | extends | `command-templates` |
| `product-documentation` | describes | `command-templates` |
| `product-documentation` | describes | `work-packages` |
| `work-packages` | validated_by | `current-truth-ontology` |
