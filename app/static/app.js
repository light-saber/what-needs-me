const state = { mode: "fused", data: null };
const $ = (selector) => document.querySelector(selector);
const esc = (text = "") => String(text).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const categoryIcon = { bill_payment: "₹", approval: "✓", travel: "✈", personal: "@", unknown: "·" };

async function json(url) { const response = await fetch(url); if (!response.ok) throw new Error("Could not load mail"); return response.json(); }
function renderAccounts(accounts) { $("#accounts").innerHTML = accounts.map(a => `<span class="chip"><i class="dot" style="background:${esc(a.color)}"></i>${esc(a.label)}</span>`).join(""); }
function card(card) { return `<button class="card" data-thread="${esc(card.threadId)}"><span class="icon">${categoryIcon[card.category] || "·"}</span><span><span class="ask">${esc(card.ask)}</span><span class="meta">${esc(card.sender)} · ${esc(card.subject)}</span><span class="snippet">${esc(card.snippet)}</span></span><span class="deadline">${card.deadline_ts ? esc(new Date(card.deadline_ts).toLocaleDateString(undefined,{month:"short",day:"numeric"})) : ""}</span></button>`; }
function renderToday(data) {
  state.data = data; const lanes = $("#lanes");
  if (!data.cards.length) { lanes.innerHTML = `<p class="empty">Clear for now. Nothing in the inbox needs your attention.</p>`; return; }
  const groups = state.mode === "split" ? Object.groupBy(data.cards, c => c.accountId) : { "Today": data.cards };
  lanes.innerHTML = Object.entries(groups).map(([name, cards]) => `<section><p class="lane-title">${esc(name === "Today" ? "PRIORITY STACK" : name)}</p>${cards.map(card).join("")}</section>`).join("");
  document.querySelectorAll(".card").forEach(el => el.onclick = () => showThread(el.dataset.thread));
  $("#pile-items").innerHTML = Object.entries(data.pile.categories).map(([kind, item]) => `<span class="pile-item">${item.count} ${esc(kind.replace("_", " "))}</span>`).join("") || "<span class=\"pile-item\">No pile yet</span>";
}
async function load() { try { const [accounts, today] = await Promise.all([json("/api/accounts"), json(`/api/today?mode=${state.mode}&days=7`)]); renderAccounts(accounts); renderToday(today); $("#status").textContent = `${today.cards.length} items worth opening`; } catch (error) { $("#status").textContent = error.message; $("#lanes").innerHTML = `<p class=empty>${esc(error.message)}. Try again shortly.</p>`; } }
async function showThread(id) { const drawer = $("#drawer"); drawer.classList.add("open"); drawer.setAttribute("aria-hidden", "false"); $("#thread-title").textContent = "Loading thread…"; try { const thread = await json(`/api/thread/${encodeURIComponent(id)}`); $("#thread-title").textContent = thread.messages[0]?.subject || "Thread"; $("#thread-summary").textContent = thread.summary; $("#thread-change").textContent = thread.changed_since_last_seen; $("#thread-messages").innerHTML = thread.messages.map(m => `<article class=message><strong>${esc(m.from)}</strong><time>${esc(new Date(m.date).toLocaleString())}</time><p>${esc(m.snippet)}</p></article>`).join(""); } catch (e) { $("#thread-title").textContent = e.message; } }
document.querySelectorAll("[data-mode]").forEach(button => button.onclick = () => { state.mode = button.dataset.mode; document.querySelectorAll("[data-mode]").forEach(b => b.classList.toggle("active", b === button)); load(); });
$("#density").onchange = e => document.body.dataset.density = e.target.value;
$("#close-drawer").onclick = () => { $("#drawer").classList.remove("open"); $("#drawer").setAttribute("aria-hidden", "true"); };
load();
