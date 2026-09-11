const state = { mode: "fused", data: null };
const $ = (selector) => document.querySelector(selector);

const decodeEntitiesEl = document.createElement("textarea");
function decodeEntities(text = "") { decodeEntitiesEl.innerHTML = text; return decodeEntitiesEl.value; }
const esc = (text = "") => decodeEntities(String(text)).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

const svg = (paths) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${paths}</svg>`;
const categoryIcon = {
  bill_payment: svg('<rect x="2" y="5" width="20" height="14" rx="3"/><circle cx="12" cy="12" r="3"/><path d="M6 12h.01M18 12h.01"/>'),
  approval: svg('<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>'),
  travel: svg('<path d="m21 3-7 18-4-7-7-4 18-7ZM10 14 21 3"/>'),
  personal: svg('<circle cx="12" cy="12" r="4"/><path d="M16 8v5a3 3 0 0 0 6 0v-1a10 10 0 1 0-4 8"/>'),
  receipt: svg('<path d="M5 3 8 5l4-2 4 2 3-2v18l-3-2-4 2-4-2-3 2V3ZM9 9h6M9 13h6"/>'),
  unknown: svg('<rect x="3" y="5" width="18" height="14" rx="3"/><path d="m3 7 9 6 9-6"/>')
};
const infoIcon = svg('<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>');
const caretIcon = svg('<path d="m6 9 6 6 6-6"/>');
const emptyState = (text) => `<div class="empty"><span class="icon">${categoryIcon.unknown}</span><p>${esc(text)}</p></div>`;
let drawerTrigger = null;
let threadRequest = 0;

// Categories the backend already treats as digest-only noise.
const QUIET_CATEGORIES = new Set(["newsletter", "notification"]);
// Categories that are informational by nature — worth seeing, never a task.
const FYI_CATEGORIES = new Set(["travel", "receipt"]);
const AUTOMATED_SENDER_RE = /no.?reply|do.?not.?reply|notification|alert|security|mailer-daemon/i;
const SECURITY_SUBJECT_RE = /log ?on|log ?in|sign.?in|otp|verification code|password (changed|reset)/i;
const GENERIC_ASK_RE = /^(reply|respond)\b/i;

// Client-side only: decide how loud a card should be. No backend/API contract change —
// this is a presentation judgment on top of the same `cards` array.
function tierOf(card) {
  if (QUIET_CATEGORIES.has(card.category)) return "quiet";
  if (card.category === "unknown" && (
    AUTOMATED_SENDER_RE.test(card.sender) ||
    SECURITY_SUBJECT_RE.test(card.subject) ||
    (GENERIC_ASK_RE.test(card.ask || "") && !card.deadline_ts)
  )) return "quiet";
  if (FYI_CATEGORIES.has(card.category)) return "fyi";
  return "action";
}

const FYI_HEADLINE = { travel: "Booking confirmed", receipt: "Receipt received" };
function headlineFor(card, tier) { return tier === "fyi" ? (FYI_HEADLINE[card.category] || card.ask) : card.ask; }

function relativeTime(iso) {
  if (!iso) return "";
  const diffMs = Date.now() - new Date(iso).getTime();
  const days = Math.floor(diffMs / 86400000);
  if (days <= 0) return "today";
  if (days === 1) return "1d ago";
  if (days < 30) return `${days}d ago`;
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

async function json(url) { const response = await fetch(url); if (!response.ok) throw new Error("Could not load mail"); return response.json(); }
function renderAccounts(accounts) { $("#accounts").innerHTML = accounts.map(a => `<span class="chip"><i class="dot" style="background:${esc(a.color)}"></i>${esc(a.label)}</span>`).join(""); }

function deadlineBadge(card) {
  if (!card.deadline_ts) return "";
  const deadline = new Date(card.deadline_ts).getTime();
  const hoursLeft = (deadline - Date.now()) / 3600000;
  const cls = hoursLeft < 0 ? " overdue" : hoursLeft <= 48 ? " due-soon" : "";
  const label = new Date(card.deadline_ts).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  return `<span class="deadline${cls}">${hoursLeft < 0 ? "Overdue · " : "Due · "}${esc(label)}</span>`;
}

function metaLine(card) {
  return `<span class="meta"><span class="meta-sender">${esc(card.sender)}</span><span class="meta-subject">${esc(card.subject)}</span></span>`;
}

function actionCard(card) {
  return `<button class="card" data-thread="${esc(card.threadId)}">
    <span class="icon">${categoryIcon[card.category] || categoryIcon.unknown}</span>
    <span class="card-content"><span class="headline">${esc(card.ask)}</span>${metaLine(card)}<span class="snippet">${esc(card.snippet)}</span></span>
    ${deadlineBadge(card)}
  </button>`;
}

function fyiCard(card) {
  return `<button class="card fyi" data-thread="${esc(card.threadId)}">
    <span class="icon">${categoryIcon[card.category] || categoryIcon.unknown}</span>
    <span class="card-content"><span class="fyi-eyebrow">${infoIcon} FYI</span><span class="headline">${esc(headlineFor(card, "fyi"))}</span>${metaLine(card)}<span class="snippet">${esc(card.snippet)}</span></span>
    ${deadlineBadge(card)}
  </button>`;
}

function quietRow(card) {
  return `<button class="quiet-row" data-thread="${esc(card.threadId)}">
    <span class="q-subject">${esc(card.subject)}</span><span class="q-sender">${esc(card.sender)}</span><span class="q-time">${esc(relativeTime(card.date))}</span>
  </button>`;
}

function bucketize(cards) {
  const buckets = { action: [], fyi: [], quiet: [] };
  cards.forEach(card => buckets[tierOf(card)].push(card));
  return buckets;
}

function renderTiers(cards) {
  const { action, fyi, quiet } = bucketize(cards);
  let html = "";
  if (action.length) html += `<div class="tier tier-action">${action.map(actionCard).join("")}</div>`;
  if (fyi.length) html += `<div class="tier tier-fyi"><p class="tier-heading">For your information</p>${fyi.map(fyiCard).join("")}</div>`;
  if (quiet.length) html += `<div class="tier tier-quiet"><p class="tier-heading">Also arrived</p><div class="quiet-strip">${quiet.map(quietRow).join("")}</div></div>`;
  if (!html) html = emptyState("Clear for now. Nothing needs you.");
  return html;
}

function renderPile(pile) {
  const entries = Object.entries(pile.categories || {});
  const total = entries.reduce((sum, [, item]) => sum + item.count, 0);
  $("#pile-headline").textContent = total ? `${total} messages filed, nothing needs you` : "Nothing here needs you";
  $("#pile").dataset.hasItems = String(total > 0);
  $("#pile-body").innerHTML = entries.length
    ? entries.map(([kind, item]) => `<div class="pile-row"><span>${esc(item.count)} ${esc(kind.replace("_", " "))}</span><span class="p-latest">${esc(relativeTime(item.latest))}</span></div>`).join("")
    : `<p class="empty">Nothing else came in.</p>`;
}

function renderToday(data) {
  state.data = data;
  const lanes = $("#lanes");
  if (!data.cards.length) {
    lanes.innerHTML = emptyState("Clear for now. Nothing needs you.");
  } else if (state.mode === "split") {
    const groups = Object.groupBy(data.cards, c => c.accountId);
    lanes.innerHTML = Object.entries(groups).map(([accountId, cards]) => {
      const account = (data.accounts || []).find(a => a.id === accountId);
      const label = account ? account.label : accountId;
      const dot = account ? `<i class="dot" style="background:${esc(account.color)}"></i>` : "";
      return `<section class="lane"><p class="lane-title">${dot}${esc(label)}</p>${renderTiers(cards)}</section>`;
    }).join("");
  } else {
    lanes.innerHTML = `<section class="lane">${renderTiers(data.cards)}</section>`;
  }
  document.querySelectorAll("[data-thread]").forEach(el => el.onclick = () => showThread(el.dataset.thread));
  renderPile(data.pile);

  const { action, fyi } = bucketize(data.cards);
  const parts = [];
  parts.push(action.length ? `${action.length} need you` : "Clear for now");
  if (fyi.length) parts.push(`${fyi.length} for your info`);
  $("#status").textContent = parts.join(" · ");
}

async function load() {
  try {
    const [accounts, today] = await Promise.all([json("/api/accounts"), json(`/api/today?mode=${state.mode}&days=7`)]);
    renderAccounts(accounts);
    renderToday({ ...today, accounts });
  } catch (error) {
    $("#status").textContent = error.message;
    $("#lanes").innerHTML = emptyState(`${error.message}. Try again shortly.`);
  }
}

async function showThread(id) {
  const request = ++threadRequest;
  drawerTrigger = document.activeElement;
  const drawer = $("#drawer");
  drawer.inert = false;
  $("main").inert = true;
  document.body.classList.add("drawer-open");
  drawer.classList.add("open"); drawer.setAttribute("aria-hidden", "false");
  $("#scrim").classList.add("open");
  $("#close-drawer").focus();
  $("#thread-title").textContent = "Loading thread…";
  $("#thread-summary").textContent = ""; $("#thread-change").textContent = ""; $("#thread-change-block").hidden = true; $("#thread-messages").innerHTML = "";
  try {
    const thread = await json(`/api/thread/${encodeURIComponent(id)}`);
    if (request !== threadRequest) return;
    $("#thread-title").textContent = thread.messages[0]?.subject || "Thread";
    $("#thread-summary").textContent = decodeEntities(thread.summary);
    if (thread.changed_since_last_seen) {
      $("#thread-change").textContent = thread.changed_since_last_seen;
      $("#thread-change-block").hidden = false;
    }
    $("#thread-messages").innerHTML = thread.messages.map(m => `<article class="message"><div class="message-head"><strong>${esc(m.from)}</strong><time>${esc(new Date(m.date).toLocaleString())}</time></div><p>${esc(m.snippet)}</p></article>`).join("");
  } catch (e) {
    if (request !== threadRequest) return;
    $("#thread-title").textContent = e.message;
  }
}

function closeDrawer() {
  threadRequest++;
  $("#drawer").inert = true;
  $("main").inert = false;
  document.body.classList.remove("drawer-open");
  drawerTrigger?.focus();
  $("#drawer").classList.remove("open"); $("#drawer").setAttribute("aria-hidden", "true");
  $("#scrim").classList.remove("open");
}

document.querySelectorAll("[data-mode]").forEach(button => button.onclick = () => {
  state.mode = button.dataset.mode;
  document.querySelectorAll("[data-mode]").forEach(b => {
    b.classList.toggle("active", b === button);
    b.setAttribute("aria-pressed", String(b === button));
  });
  load();
});
$("#density").onchange = e => document.body.dataset.density = e.target.value;
$("#close-drawer").onclick = closeDrawer;
$("#scrim").onclick = closeDrawer;
$("#pile-toggle").onclick = () => {
  const pile = $("#pile");
  const open = pile.dataset.open !== "true";
  pile.dataset.open = String(open);
  $("#pile-toggle").setAttribute("aria-expanded", String(open));
  $("#pile-caret").innerHTML = `${open ? "Hide breakdown" : "Show breakdown"}${caretIcon}`;
};

$("#pile-caret").innerHTML = `Show breakdown${caretIcon}`;
document.addEventListener("keydown", event => {
  if (!$("#drawer").classList.contains("open")) return;
  if (event.key === "Escape") closeDrawer();
  if (event.key === "Tab") {
    event.preventDefault();
    $("#close-drawer").focus();
  }
});
load();
