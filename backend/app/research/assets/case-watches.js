const get = id => document.getElementById(id);
const names = {edgar:"SEC EDGAR", gdelt:"GDELT"};

function element(tag, text) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  return node;
}

function sourceLink(record) {
  try {
    const url = new URL(record.source_url);
    if (["https:", "http:"].includes(url.protocol) && !url.username && !url.password) {
      const link = element("a", record.title);
      link.href = url.href;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      return link;
    }
  } catch {}
  return element("strong", record.title);
}

export function wireCaseWatches(api, selectedCase) {
  const dialog = get("case-watch-dialog");
  const form = get("new-watch");
  const source = get("watch-source");
  let generation = 0;
  let caseId;

  function status(message) {
    get("watch-status").textContent = message;
  }

  function action(label, handler) {
    const button = element("button", label);
    button.type = "button";
    button.className = "secondary";
    button.addEventListener("click", () => handler(button));
    return button;
  }

  function render(data) {
    const previous = source.value;
    source.replaceChildren(...data.sources.map(id => new Option(names[id], id)));
    if (data.sources.includes(previous)) source.value = previous;
    source.dispatchEvent(new Event("change"));
    form.hidden = !data.enabled || !data.sources.length;
    get("watch-list").replaceChildren(...data.watches.map(watch => {
      const item = element("li");
      const state = watch.paused ? "Paused" : watch.last_error ? "Check failed" : watch.last_success ? "Active" : "Waiting for first check";
      item.append(element("strong", names[watch.source] + " · " + watch.query),
        element("p", state + " · every " + watch.interval_minutes + " minutes"));
      if (watch.last_error) item.append(element("p", watch.last_error));
      if (!watch.paused && data.enabled) {
        item.append(element("p", "Next check " + new Date(watch.next_run * 1000).toLocaleString()));
      }
      if (!watch.paused || data.enabled) {
        item.append(action(watch.paused ? "Resume watch" : "Pause watch", button =>
          mutate(button, "/watches/" + watch.id, "PATCH", {paused:!watch.paused}, watch.paused ? "Watch resumed." : "Watch paused.")
        ));
      }
      return item;
    }));
    get("watch-alerts").replaceChildren(...data.alerts.map(alert => {
      const item = element("li");
      item.append(sourceLink(alert.record), element("p", names[alert.source] + " · " +
        (alert.reviewed ? "Reviewed" : "New") + " · detected " + new Date(alert.observed_at * 1000).toLocaleString()));
      const buttons = element("div");
      buttons.className = "case-actions";
      buttons.append(action("Save alert evidence", button =>
        mutate(button, "/alerts/" + alert.id + "/evidence", "PUT", undefined, "Record saved to the case.")
      ));
      if (!alert.reviewed) buttons.append(action("Mark reviewed", button =>
        mutate(button, "/alerts/" + alert.id + "/review", "PUT", undefined, "Alert marked reviewed.")
      ));
      item.append(buttons);
      return item;
    }));
    if (!data.watches.length) get("watch-list").append(element("li", "No watches in this case."));
    if (!data.alerts.length) get("watch-alerts").append(element("li", "No alerts in this case."));
  }

  async function load(message = "") {
    const current = generation;
    const result = await api("/cases/" + caseId + "/monitoring");
    if (current !== generation) return;
    render(result);
    status(message || (result.enabled && result.sources.length
      ? "" : "Scheduled checks are disabled or sources need setup."));
  }

  async function mutate(button, path, method, body, message) {
    const current = generation;
    button.disabled = true;
    try {
      await api("/cases/" + caseId + path, {method, body});
      if (current !== generation) return;
      status(message);
      await load(message);
    } catch (error) {
      if (current === generation) status(error.message);
    } finally {
      button.disabled = false;
    }
  }

  function reload() {
    const current = generation;
    load().catch(error => { if (current === generation) status(error.message); });
  }

  get("open-case-watches").addEventListener("click", () => {
    caseId = selectedCase();
    if (!caseId || dialog.open) return;
    generation += 1;
    form.hidden = true;
    get("watch-list").replaceChildren();
    get("watch-alerts").replaceChildren();
    status("Loading case watches.");
    dialog.showModal();
    reload();
  });
  dialog.addEventListener("close", () => { generation += 1; });
  get("watch-refresh").addEventListener("click", reload);
  source.addEventListener("change", () => {
    get("watch-query-label").textContent = source.value === "gdelt" ? "News topic" : "SEC CIK";
  });
  form.addEventListener("submit", event => {
    event.preventDefault();
    mutate(event.submitter, "/watches", "POST", {
      source:source.value, query:get("watch-query").value, interval_minutes:Number(get("watch-interval").value),
    }, "Watch saved.");
  });
}
