const form = document.getElementById("search-form");
const domainInput = document.getElementById("domain");
const main = document.querySelector("main");
const narrowLayout = matchMedia("(max-width: 780px)");
const results = document.getElementById("results");
const records = document.getElementById("records");
const status = document.getElementById("status");
const empty = document.getElementById("empty");
const error = document.getElementById("error");
const errorMessage = document.getElementById("error-message");
const retry = document.getElementById("retry");
const detail = document.getElementById("detail");
const title = document.getElementById("detail-title");
const original = document.getElementById("original");
let pending;
let lastQuery;
let selectedButton;

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function showTime(value) {
  if (!value) return "Not provided";
  if (value.endsWith("Z") || value.endsWith("+00:00")) {
    return value.replace("T", " ").replace(/(?:Z|\+00:00)$/, " UTC");
  }
  const display = value.replace("T", " ");
  return /[+-]\d{2}:\d{2}$/.test(value) ? display : display + " (time zone not provided)";
}

function openRecord(record, button) {
  selectedButton?.setAttribute("aria-pressed", "false");
  selectedButton = button;
  button.setAttribute("aria-pressed", "true");
  title.textContent = record.title;
  setText("attribution", record.source + " · Certificate Transparency");
  setText("logged", showTime(record.logged_at));
  setText("collected", showTime(record.collected_at));
  setText("valid-from", showTime(record.valid_from));
  setText("valid-until", showTime(record.valid_until));
  setText("issuer", record.issuer || "Not provided");
  const names = document.getElementById("names");
  names.hidden = !record.names.length;
  names.replaceChildren(...record.names.map(name => {
    const item = document.createElement("li");
    item.textContent = name;
    return item;
  }));
  original.href = record.source_url;
  detail.hidden = false;
  detail.scrollTop = 0;
  main.classList.add("inspecting");
  title.focus({preventScroll: !narrowLayout.matches});
}

function resultRow(record) {
  const item = document.createElement("li");
  const button = document.createElement("button");
  button.type = "button";
  button.className = "record";
  button.setAttribute("aria-pressed", "false");
  const meta = document.createElement("span");
  meta.className = "meta";
  meta.textContent = record.source + " · Certificate " + record.id.split(":").at(-1);
  const label = document.createElement("strong");
  label.textContent = record.title;
  const issuer = document.createElement("span");
  issuer.textContent = record.issuer || "Issuer not provided";
  button.append(meta, label, issuer);
  button.addEventListener("click", () => openRecord(record, button));
  item.append(button);
  return item;
}

function rememberQuery(value) {
  const url = new URL(location.href);
  url.searchParams.set("q", value);
  history.replaceState(null, "", url);
}

async function search(value) {
  const domain = value.trim();
  if (!domain) {
    domainInput.focus();
    return;
  }
  pending?.abort();
  const request = new AbortController();
  pending = request;
  lastQuery = domain;
  rememberQuery(domain);
  main.classList.remove("inspecting");
  detail.hidden = true;
  selectedButton = undefined;
  empty.hidden = true;
  error.hidden = true;
  retry.hidden = true;
  records.replaceChildren();
  results.setAttribute("aria-busy", "true");
  status.textContent = "Searching crt.sh…";

  const endpoint = new URL("../search/records", location.href);
  endpoint.searchParams.set("q", domain);
  try {
    const response = await fetch(endpoint, {signal: request.signal});
    const payload = await response.json();
    if (request.signal.aborted) return;
    if (!response.ok) {
      errorMessage.textContent = typeof payload.detail === "string" && response.status >= 422
        ? payload.detail : "The search could not be completed.";
      retry.hidden = response.status < 500;
      error.hidden = false;
      status.textContent = "";
      if (response.status === 422) domainInput.focus();
      return;
    }

    const count = payload.records.length;
    records.replaceChildren(...payload.records.map(resultRow));
    if (count === 0) {
      empty.textContent = "crt.sh returned no certificate records for " + payload.query + ".";
      empty.hidden = false;
    }
    status.textContent = count < payload.total
      ? count + " records shown · " + payload.total + " source rows"
      : count + (count === 1 ? " record" : " records");
  } catch {
    if (request.signal.aborted) return;
    status.textContent = "";
    errorMessage.textContent = "Could not complete the search. Check your connection and try again.";
    retry.hidden = false;
    error.hidden = false;
  } finally {
    if (pending === request) {
      results.setAttribute("aria-busy", "false");
      pending = undefined;
    }
  }
}

form.addEventListener("submit", event => {
  event.preventDefault();
  search(domainInput.value);
});
retry.addEventListener("click", () => {
  domainInput.focus();
  search(lastQuery);
});
document.getElementById("back").addEventListener("click", () => {
  main.classList.remove("inspecting");
  selectedButton?.focus();
});
const initial = new URLSearchParams(location.search).get("q");
if (initial) {
  domainInput.value = initial;
  search(initial);
}
