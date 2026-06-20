# Make Bold Solutions — LinkedIn Company Page Brand Guide

This guide applies the official Make Bold Solutions brand (see `../BrandGuide/MakeBoldSolutions.pdf`) to a LinkedIn Company Page for **Make Bold Solutions, LLC**. It covers every field on the page, the exact image assets to upload, and the voice/content standards to keep the page consistent with [makeboldsolutions.com](https://makeboldsolutions.com).

All image assets referenced below are in [`Assets/`](Assets/), pre-built at LinkedIn's exact required dimensions.

---

## 1. Required Assets

| Asset | File | Dimensions | Use |
|---|---|---|---|
| Company logo | `Assets/company-logo-400x400.png` | 400 × 400 px | Upload as the page's **Logo** |
| Company logo (high-res) | `Assets/company-logo-800x800@2x.png` | 800 × 800 px | Keep on file for anywhere LinkedIn or a partner asks for a larger source file |
| Cover (banner) image | `Assets/cover-banner-1128x191.png` | 1128 × 191 px | Upload as the page's **Cover image** |
| Cover image (high-res) | `Assets/cover-banner-2256x382@2x.png` | 2256 × 382 px | 2× source file, same 6:1 aspect ratio — use if LinkedIn ever raises its accepted resolution |

**Design rationale:**

- The **logo** uses the mountain mark only (no wordmark), on the brand red (`#982407`) background — one of the four approved logo/background pairings from the brand guide (white mark + black mark on red). A bare wordmark is illegible at the small avatar sizes LinkedIn renders in feeds and notifications, so the mark alone is the correct choice here, matching the "Logo Mark Only" file already provided in `../CMYK files for printing/`.
- The **cover image** uses the off-white (`#F8F6F2`) brand surface, the "Strong Foundations. Bold Decisions." headline from the website hero (for cross-channel consistency), and a faint mountain watermark bottom-right — the same motif used on makeboldsolutions.com.
- All text and the logo lockup are pushed into the **right ~52%** of the banner, vertically centered. This was corrected after testing on a live page: LinkedIn's square company logo doesn't just clip a small bottom-left corner — it overlaps roughly the **left 40–45% and bottom 60%** of the banner (much bigger than the standard "avatar corner" assumption from generic social-size guides). The entire left half of this layout is intentionally left as plain background for that reason. If you redesign this banner, keep all text/logo content right of center and in the upper half.
- LinkedIn also crops the cover image to its **center ~900px** on mobile (out of 1128px) — combined with the avatar-overlap constraint above, the safe content area in practice is roughly the **upper-right quadrant** of the banner.

> Dimension specs confirmed against Hootsuite's 2026 social image size guide; the avatar-overlap zone was confirmed empirically against the live `linkedin.com/company/makeboldsolutions` page, since published guides only describe a small corner clip and undersell how much of the banner the logo actually covers. If your upload dialog suggests different dimensions than below, trust LinkedIn's live crop preview over this document and re-export from the same source HTML (ask for the `li-logo.html` / `li-cover.html` source layouts if you need to regenerate at a new size).

---

## 2. Page Setup — Field by Field

Go to **linkedin.com/company/setup/new/** (or **Edit page** if it already exists) and fill in:

### Page identity

| Field | Value |
|---|---|
| **Page name** | `Make Bold Solutions` (no "LLC" — keep the page name matching the wordmark and website exactly; the legal entity name belongs in the About section, not the page title) |
| **LinkedIn public URL** | `linkedin.com/company/makeboldsolutions` (match the domain) |
| **Website** | `https://makeboldsolutions.com` |
| **Industry** | Financial Services (primary) — add **Business Consulting and Services** as a secondary if LinkedIn allows more than one |
| **Company size** | Select honestly (likely 1–10 employees for a fractional leadership practice) |
| **Company type** | Privately Held / LLC |
| **Founded** | Year founded |
| **Tagline** | `Fractional & Interim CFO Leadership` (this is the ~120-character line shown directly under the page name — keep it short and CFO-led per the brand guide's "About Us" positioning) |

### About / Overview (long description)

Use this copy, adapted directly from the brand guide's "About Us" page with the CTO offering kept as a secondary mention (matching the website's positioning):

> Make Bold Solutions provides fractional and interim CFO leadership to organizations navigating growth, change, and complexity. We partner with founders and leadership teams to build strong financial foundations, drive operational clarity, and support confident decision-making at critical moments.
>
> Fractional CTO support is also available for teams aligning technology strategy with financial goals.
>
> **Clarity over complexity.** We simplify the financial picture so leaders can act with confidence and focus on what matters most — backed by disciplined analysis, experience, and accountability.

### Visuals

| Field | Action |
|---|---|
| **Logo** | Upload `Assets/company-logo-400x400.png` |
| **Cover image** | Upload `Assets/cover-banner-1128x191.png` |

### Call-to-action button

Set the page's primary button to **Visit website** → `https://makeboldsolutions.com`. (Use **Contact us** only once a dedicated contact/lead form exists; until then, "Visit website" avoids sending prospects to a dead end.)

### Specialties (keyword field, comma-separated)

```text
Fractional CFO, Interim CFO, Financial Leadership, Financial Strategy, Operational Clarity, Fractional CTO, Executive Consulting, Business Scaling
```

---

## 3. Brand Recap (for anyone building further LinkedIn graphics)

| Token | Hex | Use |
|---|---|---|
| Brand Red (primary) | `#982407` | Headlines, accents, "Bold," primary mark peak |
| Brand Black | `#1E1E1E` | Body text on light backgrounds, secondary mark peak |
| Accent Orange | `#C6620C` | Sparingly — secondary highlights only, never logo or headlines |
| Off-White | `#F8F6F2` | Default light background |

**Typography:** Be Vietnam Pro (headlines, bold/extrabold) + Inter Tight (body copy, regular/medium). Both are free on Google Fonts if you're building additional graphics in Canva or Figma.

**Logo rule:** Only use the four approved background/mark color pairings from the brand guide (white, off-white, red, black backgrounds — see `../BrandGuide/MakeBoldSolutions.pdf`, "Logo Color Variations"). Never recolor the mark outside those four pairings, and never stretch or skew it.

**Voice:** Direct, confident, clarity-first. Core value: *"We encourage decisive leadership backed by disciplined analysis, experience, and accountability."* Avoid hedging language ("might," "could potentially") in page copy and posts — the brand voice is declarative.

---

## 4. Content Strategy for a "World Class" Page

A logo and banner alone don't make a page world-class — consistent, valuable posting does. LinkedIn's own data consistently shows Company Pages that post weekly grow followers significantly faster than pages that post rarely.

### Content pillars (rotate across these)

1. **CFO insight** — a short, opinionated take on a financial leadership topic (cash runway, fundraising readiness, scaling finance ops). This is the pillar that should dominate, since it's the core service.
2. **Proof of work** — anonymized case-study style posts: a problem a client faced, the decision made, the result. Ties directly to the "Bold Decisions" positioning.
3. **Point of view / commentary** — reacting to a relevant news item (a funding round, an economic indicator) through the "clarity over complexity" lens.
4. **Behind the practice** — who Make Bold Solutions is, how engagements work, what "fractional" actually means for a founder evaluating the option.

### Cadence

Aim for **1–2 posts per week** to start — consistency matters more than volume. A reliably-posting page with 1 post/week outperforms a page that bursts then goes quiet for months.

### Hashtags

Use 3–5 per post, mixing broad and specific:

```text
#FractionalCFO #InterimCFO #FinancialLeadership #MakeBoldSolutions #StartupFinance #CFOInsights
```

### Employee advocacy

Encourage any team members listed with Make Bold Solutions as their employer on LinkedIn to:

- Add the company page as their current employer (this is what populates the "Employees" module on the page — a near-empty employees list undercuts credibility for a "world class" page).
- Reshare company posts with a short personal comment rather than a bare reshare — LinkedIn's algorithm favors original commentary.

---

## 5. Launch Checklist

- [ ] Page name set to `Make Bold Solutions`, URL claimed
- [ ] Logo uploaded (`company-logo-400x400.png`)
- [ ] Cover image uploaded (`cover-banner-1128x191.png`)
- [ ] Tagline set
- [ ] About/Overview description filled in (CFO-led, CTO secondary)
- [ ] Website link set to `https://makeboldsolutions.com`
- [ ] Industry, company size, type, founded year set
- [ ] Specialties keywords added
- [ ] CTA button set to "Visit website"
- [ ] At least 3–5 founding posts published before inviting first followers (an empty feed undercuts a first impression)
- [ ] Team members' personal profiles linked as employees of the page
- [ ] Page linked from the website footer / contact section (and vice versa — add the website link prominently on LinkedIn)

---

## Sources

Image dimension specs cross-checked against:

- [Hootsuite — Social media image sizes for all networks (June 2026)](https://blog.hootsuite.com/social-media-image-sizes-guide/)
- [ConnectSafely — LinkedIn Cover Photo Size 2026: Every Dimension](https://connectsafely.ai/articles/linkedin-cover-photo-images-guide-2026)
