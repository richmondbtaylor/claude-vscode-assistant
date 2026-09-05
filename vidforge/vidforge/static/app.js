/* vidforge UI - vanilla, no build step. */
const $ = (sel) => document.querySelector(sel);
const state = { models: [], filter: "", search: "", initImage: null, poll: null };

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: options.body ? { "Content-Type": "application/json" } : {},
    ...options,
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    throw new Error(data?.error || data?.detail || `${response.status} ${response.statusText}`);
  }
  return data;
}

function message(text, kind = "error") {
  const box = $("#message");
  box.textContent = text;
  box.className = `message ${kind}`;
  box.hidden = !text;
}

/* --- models ------------------------------------------------------------- */
function currentModel() {
  return state.models.find((m) => m.id === $("#model").value);
}

function applyModelDefaults() {
  const model = currentModel();
  if (!model) return;
  const d = model.defaults || {};
  const set = (id, value) => { if (value !== undefined && value !== null) $(id).value = value; };
  set("#width", d.width); set("#height", d.height); set("#frames", d.num_frames);
  set("#fps", d.fps); set("#steps", d.steps); set("#cfg", d.guidance_scale);
  if (d.negative_prompt && !$("#negative").value) $("#negative").value = d.negative_prompt;
  $("#model-note").textContent = `${model.backend} · ${model.kind === "i2v" ? "image-to-video" : "text-to-video"}${model.repo ? ` · ${model.repo}` : ""}`;
  document.querySelector(".i2v-only").hidden = model.kind !== "i2v";
}

async function loadModels() {
  state.models = await api("/api/models");
  const select = $("#model");
  select.innerHTML = state.models
    .map((m) => `<option value="${m.id}">${m.label}</option>`)
    .join("");
  // Land on something that can actually render rather than whatever sorts
  // first: the first model whose backend passed preflight.
  try {
    const { backends } = await api("/api/status");
    const usable = state.models.find((m) => backends?.[m.backend]?.ready);
    if (usable) select.value = usable.id;
  } catch { /* keep the first option */ }
  applyModelDefaults();
}

async function loadConsent() {
  const records = await api("/api/consent");
  const select = $("#consent");
  select.innerHTML = records.length
    ? records.map((r) => `<option value="${r.id}">${r.subject} — ${r.attested_by}</option>`).join("")
    : `<option value="">no consent records on file</option>`;
}

/* --- status ------------------------------------------------------------- */
async function refreshStatus() {
  try {
    const status = await api("/api/status");
    const counts = status.counts || {};
    const backends = Object.entries(status.backends || {})
      .map(([name, info]) => `<span class="${info.ready ? "ok" : "bad"}" title="${(info.detail || "ready").replace(/"/g, "'")}">${name}</span>`)
      .join(" · ");
    $("#status-strip").innerHTML =
      `<span class="pill">queued ${counts.queued || 0}</span> · ` +
      `<span class="pill">running ${counts.running || 0}</span> · ` +
      `<span class="pill">done ${counts.done || 0}</span> &nbsp;|&nbsp; ${backends}`;
  } catch (err) {
    $("#status-strip").innerHTML = `<span class="bad">API unreachable</span>`;
  }
}

/* --- gallery ------------------------------------------------------------ */
function card(job) {
  const el = document.createElement("article");
  el.className = "card";
  el.dataset.id = job.id;
  const poster = job.status === "done"
    ? `<img loading="lazy" src="/media/${job.id}/thumb" alt="">`
    : `<div class="bar" style="width:80%"><i style="width:${Math.round(job.progress * 100)}%"></i></div>`;
  el.innerHTML = `
    <div class="media">${poster}</div>
    <div class="meta">
      <div class="row"><span class="badge ${job.status}">${job.status}</span><span>${job.model_id}</span></div>
      <div class="prompt">${escapeHtml(job.prompt)}</div>
      <div class="row"><span>seed ${job.seed}</span><span>${(job.created_at || "").slice(11, 19)}</span></div>
      ${job.error ? `<div class="error-text">${escapeHtml(job.error)}</div>` : ""}
    </div>`;
  el.addEventListener("click", () => openDetail(job));
  return el;
}

function escapeHtml(text) {
  return String(text ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

async function refreshJobs() {
  const params = new URLSearchParams({ limit: "60" });
  if (state.filter) params.set("status", state.filter);
  if (state.search) params.set("search", state.search);
  const { jobs } = await api(`/api/jobs?${params}`);
  const grid = $("#grid");
  grid.replaceChildren(...jobs.map(card));
  $("#empty").hidden = jobs.length > 0;
}

function openDetail(job) {
  const dialog = $("#detail");
  // The encoder falls back to animated WebP when no ffmpeg is present, and
  // <video> cannot play that - show it as an image instead.
  const isWebp = (job.output_path || "").toLowerCase().endsWith(".webp");
  const player = job.status !== "done" ? ""
    : isWebp
      ? `<img class="player" src="/media/${job.id}" alt="">`
      : `<video src="/media/${job.id}" controls autoplay loop muted playsinline></video>`;
  const cancellable = job.status === "queued" || job.status === "running";
  dialog.querySelector(".detail-body").innerHTML = `
    ${player}
    <dl>
      <dt>Prompt</dt><dd>${escapeHtml(job.prompt)}</dd>
      ${job.negative_prompt ? `<dt>Negative</dt><dd>${escapeHtml(job.negative_prompt)}</dd>` : ""}
      <dt>Model</dt><dd>${job.model_id} (${job.backend})</dd>
      <dt>Seed</dt><dd>${job.seed}</dd>
      <dt>Params</dt><dd>${escapeHtml(JSON.stringify(job.params))}</dd>
      <dt>Status</dt><dd>${job.status}${job.error ? ` — ${escapeHtml(job.error)}` : ""}</dd>
      ${job.output_path ? `<dt>File</dt><dd>${escapeHtml(job.output_path)}</dd>` : ""}
    </dl>
    <div class="actions">
      <button class="ghost small" data-act="reuse">Reuse settings</button>
      ${cancellable ? `<button class="ghost small" data-act="cancel">Cancel</button>` : ""}
      <button class="ghost small" data-act="delete">Delete</button>
    </div>`;

  dialog.querySelector('[data-act="reuse"]').onclick = () => {
    $("#prompt").value = job.prompt;
    $("#negative").value = job.negative_prompt || "";
    $("#seeds").value = job.seed;
    dialog.close();
  };
  const cancelBtn = dialog.querySelector('[data-act="cancel"]');
  if (cancelBtn) cancelBtn.onclick = async () => {
    await api(`/api/jobs/${job.id}/cancel`, { method: "POST" });
    dialog.close(); refreshJobs();
  };
  dialog.querySelector('[data-act="delete"]').onclick = async () => {
    await api(`/api/jobs/${job.id}`, { method: "DELETE" });
    dialog.close(); refreshJobs();
  };
  dialog.showModal();
}

/* --- submit ------------------------------------------------------------- */
function collectPrompts() {
  return $("#prompt").value.split("\n").map((line) => line.trim()).filter(Boolean);
}

function collectParams() {
  const num = (id) => ($(id).value === "" ? null : Number($(id).value));
  return {
    width: num("#width"), height: num("#height"), num_frames: num("#frames"),
    fps: num("#fps"), steps: num("#steps"), guidance_scale: num("#cfg"),
    negative_prompt: $("#negative").value,
    init_image: state.initImage,
  };
}

function collectSeeds() {
  return $("#seeds").value.split(",").map((s) => s.trim()).filter(Boolean)
    .map(Number).filter((n) => Number.isFinite(n));
}

async function uploadInitImage() {
  const file = $("#init").files[0];
  if (!file) return state.initImage;
  const body = new FormData();
  body.append("file", file);
  const response = await fetch("/api/uploads", { method: "POST", body });
  if (!response.ok) throw new Error("upload failed");
  state.initImage = (await response.json()).filename;
  return state.initImage;
}

async function previewExpansion() {
  message("");
  try {
    const data = await api("/api/prompts/preview", {
      method: "POST",
      body: JSON.stringify({
        prompts: collectPrompts(), variants: Number($("#variants").value) || 1,
        seeds: collectSeeds(), expand_wildcards: true, limit: 25,
      }),
    });
    const list = $("#preview-list");
    list.innerHTML = data.items
      .map((item) => `<li>${escapeHtml(item.prompt)} <em>· seed ${item.seed}</em></li>`).join("");
    list.hidden = false;
    message(`${data.total} job(s) would be queued${data.total > data.items.length ? ` (showing ${data.items.length})` : ""}.`, "ok");
  } catch (err) {
    message(err.message);
  }
}

async function generate() {
  const button = $("#generate-btn");
  button.disabled = true;
  message("");
  $("#preview-list").hidden = true;
  try {
    const model = currentModel();
    if (model?.kind === "i2v") await uploadInitImage();
    const payload = {
      model_id: $("#model").value,
      prompts: collectPrompts(),
      params: collectParams(),
      variants: Number($("#variants").value) || 1,
      seeds: collectSeeds(),
      identity_reference: $("#identity").checked,
      consent_id: $("#identity").checked ? $("#consent").value || null : null,
    };
    const data = await api("/api/generate", { method: "POST", body: JSON.stringify(payload) });
    message(`Queued ${data.jobs.length} job(s).`, "ok");
    await refreshJobs();
  } catch (err) {
    message(err.message);
  } finally {
    button.disabled = false;
  }
}

/* --- wiring ------------------------------------------------------------- */
function wire() {
  $("#model").addEventListener("change", applyModelDefaults);
  $("#generate-btn").addEventListener("click", generate);
  $("#preview-btn").addEventListener("click", previewExpansion);
  $("#identity").addEventListener("change", (e) => { $("#consent").hidden = !e.target.checked; });
  $("#clear-queue").addEventListener("click", async () => {
    await api("/api/queue/clear", { method: "POST" });
    refreshJobs();
  });
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("is-active"));
      tab.classList.add("is-active");
      state.filter = tab.dataset.filter;
      refreshJobs();
    });
  });
  let debounce;
  $("#search").addEventListener("input", (e) => {
    clearTimeout(debounce);
    debounce = setTimeout(() => { state.search = e.target.value.trim(); refreshJobs(); }, 250);
  });
}

async function boot() {
  wire();
  try {
    await loadModels();
    await loadConsent();
  } catch (err) {
    message(`Could not reach the API: ${err.message}`);
  }
  await Promise.all([refreshStatus(), refreshJobs().catch(() => {})]);
  // Cheap polling beats a websocket here: the payload is small and the queue
  // only changes on the order of seconds.
  state.poll = setInterval(() => {
    refreshStatus();
    if (!$("#detail").open) refreshJobs().catch(() => {});
  }, 2000);
}

boot();
