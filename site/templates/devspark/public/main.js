/*
 * DevSpark docs — surface the live version from the distribution manifest.
 *
 * Elements with `data-devspark-version` and `data-devspark-build-date` attributes are
 * filled from `/dist/manifest.json` (served from the same Static Web App). This
 * keeps release information on the site current without hardcoding it.
 *
 * docfx "modern" template loads this file from the template's `public/` folder
 * and invokes the exported hooks; we also self-run on DOM ready as a fallback.
 */

let _devsparkVersionApplied = false;
let _devsparkUserApplied = false;

async function applyDevSparkManifestVersion() {
  if (_devsparkVersionApplied) return;
  const versionTargets = document.querySelectorAll("[data-devspark-version]");
  const buildDateTargets = document.querySelectorAll("[data-devspark-build-date]");
  if (!versionTargets.length && !buildDateTargets.length) return;
  _devsparkVersionApplied = true;
  try {
    const res = await fetch("/dist/manifest.json?cb=" + Date.now(), { cache: "no-store" });
    if (!res.ok) throw new Error("manifest " + res.status);
    const manifest = await res.json();
    const latest = manifest && manifest.latest ? String(manifest.latest) : "";
    if (!latest) throw new Error("no latest");
    const label = "v" + latest;
    versionTargets.forEach((el) => {
      el.textContent = label;
      if (manifest.released) {
        el.setAttribute("title", "Released " + manifest.released);
      }
    });
    if (buildDateTargets.length) {
      const released = manifest && manifest.released ? String(manifest.released) : "";
      const releasedDate = new Date(released);
      if (!released || Number.isNaN(releasedDate.getTime())) throw new Error("no build date");
      const formattedDate = new Intl.DateTimeFormat("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        timeZone: "UTC",
        timeZoneName: "short",
      }).format(releasedDate);
      buildDateTargets.forEach((el) => {
        el.textContent = formattedDate;
        el.setAttribute("datetime", released);
      });
    }
  } catch (err) {
    // Leave a graceful fallback rather than a broken placeholder.
    [...versionTargets, ...buildDateTargets].forEach((el) => {
      el.textContent = "Unavailable";
    });
  }
}

// Surface the Entra-authenticated user (Azure Static Web Apps exposes the signed-in
// principal at /.auth/me) as a "logged in" chip in the navbar. Fails silently when
// auth is not configured or the visitor is anonymous, so it is safe pre-Entra.
async function applyDevSparkUser() {
  if (_devsparkUserApplied) return;
  _devsparkUserApplied = true;
  try {
    const res = await fetch("/.auth/me", { cache: "no-store", credentials: "same-origin" });
    if (!res.ok) return;
    const data = await res.json();
    const principal = data && data.clientPrincipal;
    if (!principal) return; // anonymous — show nothing

    // Prefer a friendly display-name claim; fall back to userDetails (UPN/email).
    const claims = Array.isArray(principal.claims) ? principal.claims : [];
    const findClaim = (suffixes) =>
      (claims.find((c) => c && typeof c.typ === "string" &&
        suffixes.some((s) => c.typ === s || c.typ.endsWith(s))) || {}).val;
    const name =
      findClaim(["name", "/name", "/displayname", "given_name"]) ||
      principal.userDetails ||
      "Signed in";

    const initials = String(name)
      .split(/[\s.@]+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((p) => p[0].toUpperCase())
      .join("") || "•";

    const chip = document.createElement("div");
    chip.className = "devspark-user";
    chip.setAttribute("title", "Signed in as " + name);
    chip.innerHTML =
      '<span class="devspark-user-avatar" aria-hidden="true"></span>' +
      '<span class="devspark-user-name"></span>';
    chip.querySelector(".devspark-user-avatar").textContent = initials;
    chip.querySelector(".devspark-user-name").textContent = name;

    // Drop it into the navbar (right side) when present; otherwise pin top-right.
    const navbar =
      document.querySelector(".navbar .navbar-nav") ||
      document.querySelector(".navbar > .container-xxl") ||
      document.querySelector(".navbar");
    if (navbar) {
      chip.classList.add("devspark-user--nav");
      navbar.appendChild(chip);
    } else {
      chip.classList.add("devspark-user--float");
      document.body.appendChild(chip);
    }
  } catch (err) {
    // No auth endpoint / not signed in — leave the header unchanged.
  }
}

// Interactive route explorer for the home page: renders into [data-devspark-flow].
const DEVSPARK_FLOW_TAGS = { req: "Required", rec: "Recommended", opt: "Optional", dec: "Decision", end: "Human" };

const DEVSPARK_FLOW_ROUTES = [
  {
    id: "quickfix",
    title: "Bug, config, docs, hotfix",
    sub: "Quickfix \u00b7 about 4 hours or less, one area",
    skips: "/devspark-specify, /devspark-plan, /devspark-tasks, /devspark-planning-review",
    gates: "Advisory only; you decide on any concern",
    escalate: "Switch to a full spec if the fix needs a new contract, public API or schema change, or a security or governance change.",
    steps: [
      { cmd: "/devspark-quickfix", tag: "req", why: "Creates a lightweight record and runs targeted checks.",
        detail: "Classifies the work (bug-fix, hotfix, config-change, docs-update, minor-feature) and checks only the constitution principles that apply." },
      { cmd: "/devspark-implement", tag: "req", why: "Makes the fix and finalizes the record.",
        detail: "Owns code, tests and current knowledge together. The record stays live until release archives it." },
    ],
  },
  {
    id: "quickspec",
    title: "Small feature, clear criteria",
    sub: "Quick-spec \u00b7 needs acceptance criteria, no design",
    skips: "/devspark-plan, /devspark-tasks, /devspark-planning-review",
    gates: "/devspark-verify, scaled to the change",
    escalate: "Re-run /devspark-specify as a full spec if scope grows past what the quick-spec describes.",
    steps: [
      { cmd: "/devspark-specify", tag: "req", why: "Confirms the quick-spec route and writes a compact spec.",
        detail: "Recommends a route, asks you to confirm it, then drafts the intent and acceptance criteria." },
      { cmd: "/devspark-implement", tag: "req", why: "Goes straight from spec to code.",
        detail: "No plan, tasks or planning review. Code, tests and current knowledge change together." },
    ],
  },
  {
    id: "fullspec",
    title: "New feature, API or schema, refactor",
    sub: "Full spec \u00b7 cross-cutting or high-risk",
    skips: "nothing",
    gates: "/devspark-planning-review, then /devspark-verify",
    escalate: "Already the heaviest route.",
    steps: [
      { cmd: "/devspark-specify", tag: "req", why: "Defines what and why, with acceptance criteria.",
        detail: "Creates the branch and the spec, and asks you to confirm the route before anything is written." },
      { cmd: "/devspark-clarify", tag: "rec", why: "Up to five targeted questions on vague points.",
        detail: "Cheaper than rework after planning. Skip it when the spec is already unambiguous." },
      { cmd: "/devspark-plan", tag: "req", why: "Produces the design and the context the work depends on.",
        detail: "Includes the Context Resolution section that planning review checks later." },
      { cmd: "/devspark-checklist", tag: "opt", why: "Quality-checks the written requirements.",
        detail: "Worth it for risky or ambiguous specs; safe to skip otherwise." },
      { cmd: "/devspark-tasks", tag: "req", why: "Breaks the plan into dependency-ordered tasks.",
        detail: "Each task carries code and knowledge linkage so nothing is lost at release." },
      { cmd: "/devspark-planning-review", tag: "rec", why: "/devspark-analyze, /devspark-critic and Judge run as one step with one decision.",
        detail: "Edits alone never clear a STOP. The review ends on a clean verdict or a human decision.",
        extras: [
          { cls: "bad", text: "STOP: fix the plan or tasks, then re-review" },
          { cls: "warn", text: "CONDITIONAL: a human decides, then re-review" },
          { cls: "ok", text: "PROCEED: continue to /devspark-implement" },
        ] },
      { cmd: "/devspark-implement", tag: "req", why: "Executes the tasks.",
        detail: "Code, tests and current knowledge change together." },
    ],
  },
];

const DEVSPARK_FLOW_TAIL = [
  { cmd: "/devspark-verify", tag: "req", why: "Gathers executable proof and records the closeout decision.",
    detail: "Closeout is part of this skill, so there is no separate closeout step to run." },
  { cmd: "Closeout complete?", tag: "dec", why: "Complete, or back to /devspark-implement for open defects only.",
    detail: "A not-complete decision never means redoing everything.",
    extras: [
      { cls: "ok", text: "complete: go on to the pull request" },
      { cls: "bad", text: "not-complete: /devspark-implement for open defects only, then /devspark-verify again" },
    ] },
  { cmd: "/devspark-create-pr", tag: "req", why: "Opens a spec-aware pull request.",
    detail: "A not-complete closeout blocks this step." },
  { cmd: "/devspark-pr-review", tag: "rec", why: "Constitution-aware review of the pull request.",
    detail: "Findings are saved with the commit they were reviewed against." },
  { cmd: "Open findings?", tag: "dec", why: "Fix them, then review again.",
    detail: "Code fixes and review-file updates go in separate commits.",
    extras: [
      { cls: "ok", text: "none: ready to merge" },
      { cls: "warn", text: "yes: /devspark-address-pr-review, then /devspark-pr-review again" },
    ] },
  { cmd: "Human merges", tag: "end", why: "You approve and merge in GitHub or Azure DevOps.",
    detail: "DevSpark never merges for you." },
];

function _devsparkMake(tag, cls, text) {
  const el = document.createElement(tag);
  if (cls) el.className = cls;
  if (text !== undefined) el.textContent = text;
  return el;
}

function applyDevSparkFlow() {
  const root = document.querySelector("[data-devspark-flow]");
  if (!root || root.dataset.devsparkFlowReady) return;
  root.dataset.devsparkFlowReady = "1";

  const state = { route: DEVSPARK_FLOW_ROUTES[2], showOptional: true, active: null, timer: null };
  const buttons = [];

  root.textContent = "";
  root.classList.add("devspark-flow");

  const ask = _devsparkMake("div", "devspark-flow__ask");
  ask.appendChild(_devsparkMake("p", "devspark-flow__q", "What are you changing?"));
  const choices = _devsparkMake("div", "devspark-flow__choices");
  ask.appendChild(choices);

  const toolbar = _devsparkMake("div", "devspark-flow__toolbar");
  const optLabel = _devsparkMake("label", "devspark-flow__opt");
  const optBox = _devsparkMake("input");
  optBox.type = "checkbox";
  optBox.checked = true;
  optLabel.appendChild(optBox);
  optLabel.appendChild(document.createTextNode(" Show optional steps"));
  const play = _devsparkMake("button", "devspark-flow__play", "\u25b6 Walk me through it");
  play.type = "button";
  toolbar.appendChild(optLabel);
  toolbar.appendChild(play);

  const stepsRow = _devsparkMake("ol", "devspark-flow__row");
  const meta = _devsparkMake("div", "devspark-flow__meta");
  const tailHead = _devsparkMake("p", "devspark-flow__tailhead", "Then, on every route");
  const tailRow = _devsparkMake("ol", "devspark-flow__row devspark-flow__row--tail");
  const detail = _devsparkMake("div", "devspark-flow__detail");
  detail.setAttribute("aria-live", "polite");
  const hint = _devsparkMake("p", "devspark-flow__hint");
  hint.appendChild(document.createTextNode("Not sure where you are? Run "));
  hint.appendChild(_devsparkMake("code", "", "/devspark-next"));
  hint.appendChild(document.createTextNode(" and it names the single next step."));

  [ask, toolbar, stepsRow, meta, tailHead, tailRow, detail, hint].forEach((n) => root.appendChild(n));

  function visibleSteps() {
    const own = state.route.steps.filter((s) => state.showOptional || s.tag !== "opt");
    return own.concat(DEVSPARK_FLOW_TAIL);
  }

  function showDetail(step) {
    state.active = step;
    buttons.forEach((b) => b.el.classList.toggle("is-active", b.step === step));
    detail.textContent = "";
    if (!step) {
      detail.appendChild(_devsparkMake("p", "devspark-flow__empty", "Select a step to see what it does and why it is there."));
      return;
    }
    const head = _devsparkMake("div", "devspark-flow__dhead");
    head.appendChild(_devsparkMake("code", "devspark-flow__dcmd", step.cmd));
    head.appendChild(_devsparkMake("span", "devspark-tag devspark-tag--" + step.tag, DEVSPARK_FLOW_TAGS[step.tag]));
    detail.appendChild(head);
    detail.appendChild(_devsparkMake("p", "devspark-flow__dwhy", step.why));
    if (step.detail) detail.appendChild(_devsparkMake("p", "devspark-flow__ddetail", step.detail));
    if (step.extras) {
      const list = _devsparkMake("ul", "devspark-flow__extras");
      step.extras.forEach((x) => list.appendChild(_devsparkMake("li", "devspark-x devspark-x--" + x.cls, x.text)));
      detail.appendChild(list);
    }
  }

  function stepButton(step, kind) {
    const li = _devsparkMake("li", "devspark-step devspark-step--" + kind);
    const b = _devsparkMake("button", "devspark-step__btn devspark-step__btn--" + step.tag);
    b.type = "button";
    b.appendChild(_devsparkMake("span", "devspark-step__cmd", step.cmd));
    b.appendChild(_devsparkMake("span", "devspark-tag devspark-tag--" + step.tag, DEVSPARK_FLOW_TAGS[step.tag]));
    b.addEventListener("click", () => { stopPlay(); showDetail(step); });
    li.appendChild(b);
    buttons.push({ el: b, step });
    return li;
  }

  function render() {
    buttons.length = 0;
    root.style.setProperty("--route-c", "var(--devspark-route-" + state.route.id + ")");
    [...choices.children].forEach((c) => {
      const on = c.dataset.route === state.route.id;
      c.classList.toggle("is-on", on);
      c.setAttribute("aria-pressed", String(on));
    });
    stepsRow.textContent = "";
    tailRow.textContent = "";
    state.route.steps
      .filter((s) => state.showOptional || s.tag !== "opt")
      .forEach((s) => stepsRow.appendChild(stepButton(s, "route")));
    DEVSPARK_FLOW_TAIL.forEach((s) => tailRow.appendChild(stepButton(s, "tail")));
    tailRow.style.counterReset = "devspark-s " + stepsRow.children.length;
    meta.textContent = "";
    [["Skips", state.route.skips], ["Gates", state.route.gates], ["Escalate", state.route.escalate]].forEach(([k, v]) => {
      const d = _devsparkMake("div", "devspark-flow__metaitem");
      d.appendChild(_devsparkMake("strong", "", k + ": "));
      d.appendChild(document.createTextNode(v));
      meta.appendChild(d);
    });
    root.classList.remove("is-fresh");
    void root.offsetWidth;
    root.classList.add("is-fresh");
    showDetail(state.route.steps[0]);
  }

  function stopPlay() {
    if (state.timer) window.clearInterval(state.timer);
    state.timer = null;
    play.textContent = "\u25b6 Walk me through it";
  }

  function startPlay() {
    const list = visibleSteps();
    let i = 0;
    showDetail(list[0]);
    play.textContent = "\u275a\u275a Pause";
    state.timer = window.setInterval(() => {
      i += 1;
      if (i >= list.length) { stopPlay(); return; }
      showDetail(list[i]);
    }, 2200);
  }

  DEVSPARK_FLOW_ROUTES.forEach((r) => {
    const c = _devsparkMake("button", "devspark-flow__choice devspark-flow__choice--" + r.id);
    c.type = "button";
    c.dataset.route = r.id;
    c.appendChild(_devsparkMake("span", "devspark-flow__ctitle", r.title));
    c.appendChild(_devsparkMake("span", "devspark-flow__csub", r.sub));
    c.addEventListener("click", () => { stopPlay(); state.route = r; render(); });
    choices.appendChild(c);
  });

  optBox.addEventListener("change", () => { stopPlay(); state.showOptional = optBox.checked; render(); });
  play.addEventListener("click", () => (state.timer ? stopPlay() : startPlay()));

  render();
}

function _devsparkInit() {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", applyDevSparkManifestVersion);
    document.addEventListener("DOMContentLoaded", applyDevSparkUser);
    document.addEventListener("DOMContentLoaded", applyDevSparkFlow);
  } else {
    applyDevSparkManifestVersion();
    applyDevSparkUser();
    applyDevSparkFlow();
  }
}

// Self-run on import (covers templates that don't call the hooks).
if (typeof document !== "undefined") {
  _devsparkInit();
}

// docfx "modern" template hooks.
export default {
  start: () => _devsparkInit(),
  ready: () => {
    applyDevSparkManifestVersion();
    applyDevSparkUser();
    applyDevSparkFlow();
  },
};
