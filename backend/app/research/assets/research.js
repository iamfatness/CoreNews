const byId = id => document.getElementById(id);
const form = byId("search-form");
const queryInput = byId("domain");
const mode = byId("source-mode");
const main = document.querySelector("main");
const narrow = matchMedia("(max-width: 780px)");
const records = byId("records");
const detail = byId("detail");
const casePicker = byId("active-case");
let pending;
let lastSearch;
let workspaceKey;
let selected;
let selectedButton;

function setText(id, value) {
  byId(id).textContent = value;
}

function showTime(value) {
  if (!value) return "Not provided";
  if (!value.includes("T")) return value;
  const display = value.replace("T", " ");
  if (/(Z|\+00:00)$/.test(value)) return display.replace(/(?:Z|\+00:00)$/, " UTC");
  return /[+-]\d{2}:\d{2}$/.test(value) ? display : display + " (time zone not provided)";
}

function isFiling(record) {
  return record.record_type === "sec_filing";
}

function recordFields(record) {
  const sourceFields = isFiling(record)
    ? [["Filed", showTime(record.filed_on)], ["SEC CIK", record.cik], ["Accession", record.accession], ["Form", record.form]]
    : [["Logged by source", showTime(record.logged_at)], ["Valid from", showTime(record.valid_from)],
       ["Valid until", showTime(record.valid_until)], ["Issuer", record.issuer || "Not provided"]];
  return [["Collected by CoreNews", showTime(record.collected_at)], ...sourceFields];
}

async function api(path, {method = "GET", body, signal, key = workspaceKey} = {}) {
  const headers = {};
  if (key) headers.Authorization = "Bearer " + key;
  if (body) headers["Content-Type"] = "application/json";
  const response = await fetch("../api/research" + path, {
    method, headers, body: body ? JSON.stringify(body) : undefined, signal, cache: "no-store",
  });
  const payload = await response.json();
  if (!response.ok) {
    const failure = new Error(typeof payload.detail === "string" ? payload.detail : "The request could not be completed.");
    failure.status = response.status;
    throw failure;
  }
  return payload;
}

function openRecord(entry, button) {
  selectedButton?.setAttribute("aria-pressed", "false");
  selected = entry;
  selectedButton = button;
  button.setAttribute("aria-pressed", "true");
  const {record} = entry;
  const filing = isFiling(record);
  setText("detail-title", record.title);
  setText("record-kind", filing ? "Company filing" : "Certificate record");
  setText("attribution", record.source + " · " + record.id.split(":").at(-1));
  byId("original").href = record.source_url;
  setText("original", "View original record on " + record.source);
  byId("provenance").replaceChildren(...recordFields(record).map(([label, value]) => {
    const group = document.createElement("div");
    const dt = document.createElement("dt");
    const dd = document.createElement("dd");
    dt.textContent = label;
    dd.textContent = value;
    group.append(dt, dd);
    return group;
  }));
  setText("record-shows", filing
    ? "EDGAR lists a submission under the identified filer and form."
    : "The certificate log lists names on the certificate and the issuer when available.");
  setText("record-limits", filing
    ? "A filing records the filer’s disclosure. Check the document for the claim you want to cite."
    : "The log entry alone cannot establish who operates a domain or whether the certificate is currently in use.");
  const names = record.names || [];
  byId("names").hidden = !names.length;
  byId("names").replaceChildren(...names.map(name => {
    const item = document.createElement("li");
    item.textContent = name;
    return item;
  }));
  byId("save-record").hidden = !entry.proof;
  byId("save-record").disabled = !casePicker.value;
  byId("verify-record").hidden = !entry.snapshot_sha256;
  setText("record-status", entry.id
    ? (entry.snapshot_sha256 ? "Saved record with a verifiable metadata snapshot." : "Saved record metadata.")
    : (entry.proof && !casePicker.value ? "Create or select a case to save this record." : ""));
  byId("citation-text").hidden = true;
  detail.hidden = false;
  detail.scrollTop = 0;
  main.classList.add("inspecting");
  byId("detail-title").focus({preventScroll: !narrow.matches});
}

function resultRow(entry) {
  const {record} = entry;
  const item = document.createElement("li");
  const button = document.createElement("button");
  button.type = "button";
  button.className = "record";
  button.setAttribute("aria-pressed", "false");
  const meta = document.createElement("span");
  meta.className = "meta";
  meta.textContent = record.source + " · " + record.id.split(":").at(-1);
  const title = document.createElement("strong");
  title.textContent = record.title;
  const summary = document.createElement("span");
  summary.textContent = isFiling(record)
    ? "Filed " + (record.filed_on || "date unavailable")
    : record.issuer || "Issuer not provided";
  button.append(meta, title, summary);
  button.addEventListener("click", () => openRecord(entry, button));
  item.append(button);
  return item;
}

function clearResults(heading) {
  pending?.abort();
  pending = undefined;
  byId("results").setAttribute("aria-busy", "false");
  main.classList.remove("inspecting");
  detail.hidden = true;
  selected = undefined;
  selectedButton = undefined;
  byId("empty").hidden = true;
  byId("error").hidden = true;
  records.replaceChildren();
  setText("results-title", heading);
  setText("status", "");
}

function showEntries(entries, emptyMessage) {
  records.replaceChildren(...entries.map(resultRow));
  byId("empty").hidden = !!entries.length;
  setText("empty", emptyMessage);
  setText("status", entries.length + (entries.length === 1 ? " record" : " records"));
}

async function search(value, source) {
  const query = value.trim();
  if (!query) return;
  clearResults("Search results");
  lastSearch = {query, source};
  if (!workspaceKey && source === "edgar") {
    setText("workspace-status", "Open a case workspace to search company filings.");
    byId("workspace-key").focus();
    return;
  }

  const request = new AbortController();
  pending = request;
  const params = new URLSearchParams({q: query, source});
  byId("results").setAttribute("aria-busy", "true");
  setText("status", source === "edgar" ? "Searching SEC EDGAR." : "Searching crt.sh.");
  try {
    let payload;
    if (workspaceKey) {
      payload = await api("/search?" + params, {signal: request.signal});
    } else {
      const response = await fetch("../search/records?" + new URLSearchParams({q:query}), {signal:request.signal});
      payload = await response.json();
      if (!response.ok) {
        const failure = new Error(typeof payload.detail === "string" ? payload.detail : "The search could not be completed.");
        failure.status = response.status;
        throw failure;
      }
      payload.records = payload.records.map(record => ({record}));
    }
    if (request.signal.aborted) return;
    showEntries(payload.records, "The source returned no matching records.");
    if (payload.records.length < payload.total) {
      setText("status", payload.records.length + " records shown · " + payload.total + " source rows");
    }
  } catch (failure) {
    if (request.signal.aborted) return;
    setText("status", "");
    setText("error-message", failure.message);
    byId("error").hidden = false;
    byId("retry").hidden = !!failure.status && failure.status < 500;
  } finally {
    if (pending === request) {
      pending = undefined;
      byId("results").setAttribute("aria-busy", "false");
    }
  }
}

function updateCases(cases, activeId) {
  casePicker.replaceChildren(new Option("Select a case", ""));
  for (const item of cases) casePicker.add(new Option(item.title, item.id));
  casePicker.value = activeId || "";
  byId("view-case").disabled = !casePicker.value;
  byId("save-record").disabled = !casePicker.value;
}

byId("workspace-form").addEventListener("submit", async event => {
  event.preventDefault();
  const input = byId("workspace-key");
  const key = input.value;
  const button = event.submitter;
  button.disabled = true;
  try {
    const cases = await api("/cases", {key});
    workspaceKey = key;
    byId("workspace-form").hidden = true;
    byId("case-controls").hidden = false;
    input.value = "";
    updateCases(cases);
    setText("workspace-status", "Workspace open. Searches can now be saved.");
    if (lastSearch) search(lastSearch.query, lastSearch.source);
  } catch (failure) {
    setText("workspace-status", failure.message);
  } finally {
    button.disabled = false;
  }
});

byId("close-workspace").addEventListener("click", () => location.reload());
byId("new-case").addEventListener("submit", async event => {
  event.preventDefault();
  const input = byId("case-title");
  const button = event.submitter;
  button.disabled = true;
  try {
    const created = await api("/cases", {method:"POST", body:{title:input.value}});
    casePicker.add(new Option(created.title, created.id));
    casePicker.value = created.id;
    casePicker.dispatchEvent(new Event("change"));
    input.value = "";
    setText("workspace-status", "Case created.");
  } catch (failure) {
    setText("workspace-status", failure.message);
  } finally {
    button.disabled = false;
  }
});
casePicker.addEventListener("change", () => {
  byId("view-case").disabled = !casePicker.value;
  byId("save-record").disabled = !casePicker.value;
  if (byId("results-title").textContent === "Saved evidence") {
    clearResults("Saved evidence");
    showEntries([], "Open the selected case to see its evidence.");
  }
});
byId("view-case").addEventListener("click", async () => {
  const caseId = casePicker.value;
  clearResults("Saved evidence");
  const request = new AbortController();
  pending = request;
  try {
    const current = await api("/cases/" + caseId, {signal:request.signal});
    if (request.signal.aborted || caseId !== casePicker.value) return;
    showEntries(current.evidence.map(entry => ({...entry, caseId})), "No evidence has been saved in this case.");
  } catch (failure) {
    if (!request.signal.aborted) setText("workspace-status", failure.message);
  } finally {
    if (pending === request) pending = undefined;
  }
});
byId("save-record").addEventListener("click", async event => {
  const entry = selected;
  const button = event.currentTarget;
  button.disabled = true;
  try {
    await api("/cases/" + casePicker.value + "/evidence", {
      method:"PUT", body:{record:entry.record, proof:entry.proof},
    });
    if (entry === selected) setText("record-status", "Saved. Open the case to view the evidence.");
  } catch (failure) {
    if (entry === selected) setText("record-status", failure.message);
  } finally {
    button.disabled = !casePicker.value;
  }
});
byId("verify-record").addEventListener("click", async () => {
  const entry = selected;
  try {
    const result = await api("/cases/" + entry.caseId + "/evidence/" + entry.id + "/verify");
    if (entry === selected) setText("record-status", result.status === "verified"
      ? "Snapshot verified · SHA-256 " + result.sha256
      : "Snapshot verification status: " + result.status.replaceAll("_", " "));
  } catch (failure) {
    if (entry === selected) setText("record-status", failure.message);
  }
});
byId("copy-citation").addEventListener("click", async () => {
  const {record} = selected;
  const parts = [record.title, record.source, record.id];
  const date = record.filed_on || record.logged_at;
  if (date) parts.push((isFiling(record) ? "Filed " : "Logged ") + showTime(date));
  parts.push("Collected " + showTime(record.collected_at), record.source_url);
  const citation = parts.join(" · ");
  try {
    await navigator.clipboard.writeText(citation);
    setText("record-status", "Citation copied.");
  } catch {
    const field = byId("citation-text");
    field.value = citation;
    field.hidden = false;
    field.select();
    setText("record-status", "Copy the citation from the text field.");
  }
});

mode.addEventListener("change", () => {
  const filing = mode.value === "edgar";
  setText("query-label", filing ? "Ticker or SEC CIK" : "Domain");
  queryInput.placeholder = filing ? "AAPL or 0000320193" : "example.org";
});
form.addEventListener("submit", event => {
  event.preventDefault();
  search(queryInput.value, mode.value);
});
byId("retry").addEventListener("click", () => search(lastSearch.query, lastSearch.source));
byId("back").addEventListener("click", () => {
  main.classList.remove("inspecting");
  selectedButton?.focus();
});
const params = new URLSearchParams(location.search);
if (params.get("source") === "edgar") {
  mode.value = "edgar";
  mode.dispatchEvent(new Event("change"));
}
if (params.get("q")) {
  queryInput.value = params.get("q");
  search(queryInput.value, mode.value);
}
