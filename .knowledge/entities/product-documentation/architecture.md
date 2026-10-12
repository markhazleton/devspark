---
id: product-documentation-architecture
type: entity-layer
title: Product Documentation - Architecture
layer: architecture
source_of_truth:
  - site/docfx.json
  - .github/workflows/docs.yml
  - eng/site/build-distribution.py
last_verified: '2026-10-12'
---

# Product Documentation

The authored public documentation lives in `site/src/`. DocFX builds it using the
Make Bold Solutions theme in `site/templates/devspark/`. The Pages workflow assembles
the documentation, versioned release archives, raw framework assets, and install
manifest into one public distribution. Its `skill` entries install v9.0 consumer
skills under `.github/skills/`; framework stock data stays under `.devspark/`.
Retained brand source assets live alongside
the brand-system entity; the site's copied logos and fonts are its publishing assets.
