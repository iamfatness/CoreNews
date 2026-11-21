const labels = {
  results: "Records returned", no_match: "No matching records",
  setup_required: "Setup required", unavailable: "Unavailable", not_applicable: "Outside this query",
};

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function action(text, handler, className = "secondary") {
  const button = element("button", text, className);
  button.type = "button";
  button.addEventListener("click", () => handler(button));
  return button;
}

function dateTime(value) {
  return new Date(value * 1000).toLocaleString(undefined, {dateStyle:"medium", timeStyle:"short"});
}

function sourceDate(record) {
  const dates = [
    ["Filed", record.filed_on], ["Indexed", record.seen_at], ["Occurred", record.occurred_at],
    ["SDN snapshot published", record.published_on], ["Added to catalog", record.added_on],
    ["Registry updated", record.updated_at || record.registry_changed_at],
    ["Registered", record.registered_at], ["Certificate logged", record.logged_at],
  ];
  return dates.find(([, date]) => date);
}

function provenance(record) {
  const date = sourceDate(record);
  const identifier = record.cik || record.lei || record.cve || record.domain || record.list_uid;
  return [record.source, identifier, date && date.join(" ")].filter(Boolean).join(" · ");
}

function original(record, text = "Open source record") {
  let url;
  try {
    url = new URL(record.source_url);
  } catch {
    return element("p", "Source link unavailable.");
  }
  if (!["https:", "http:"].includes(url.protocol)) return element("p", "Source link unavailable.");
  const link = element("a", text);
  link.href = url.href;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  return link;
}

function display(value) {
  if (Array.isArray(value)) return value.join(", ") || "None listed";
  return value === null || value === undefined ? "Unavailable" : String(value);
}

export function wireInvestigations(api, activeCase) {
  const byId = id => document.getElementById(id);
  const dialog = byId("investigation-dialog");
  const status = byId("investigation-status");
  const selector = byId("investigation-select");
  const frequency = byId("investigation-frequency");
  const schedule = byId("investigation-schedule");
  const runList = byId("investigation-runs");
  const detail = byId("investigation-run-detail");
  const older = byId("investigation-older");
  const pending = byId("investigation-pending");
  const save = byId("save-investigation");
  const saveStatus = byId("save-investigation-status");
  let search;
  let current;

  function endpoint(state, id = selector.value) {
    const collection = "/cases/" + encodeURIComponent(state.caseId) + "/investigations";
    return id ? collection + "/" + encodeURIComponent(id) : collection;
  }

  async function perform(button, outcome, task) {
    button.disabled = true;
    try {
      await task();
    } catch (error) {
      outcome.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  }

  function changeCard(state, run, change) {
    const item = element("li", "", "investigation-change");
    item.append(
      element("p", (change.kind === "new" ? "New record" : "Updated record") + (change.reviewed ? " · Reviewed" : ""), "report-meta"),
      element("h4", change.record.title),
      element("p", provenance(change.record), "report-meta"), original(change.record),
    );
    if (change.previous && change.changed_fields.length) {
      const diff = element("details");
      diff.append(element("summary", "Compare earlier and current values"));
      const list = element("dl");
      for (const key of change.changed_fields) {
        if (["id", "record_type", "source"].includes(key)) continue;
        const field = element("div");
        field.append(element("dt", key.replaceAll("_", " ")),
          element("dd", "Earlier · " + display(change.previous[key])),
          element("dd", "Current · " + display(change.record[key])));
        list.append(field);
      }
      diff.append(list);
      item.append(diff);
    }
    if (change.finding_id) {
      item.append(element("p", "Cited in case findings.", "report-meta"));
      return item;
    }
    const path = endpoint(state) + "/changes/" + change.id;
    const feedback = element("p");
    feedback.setAttribute("role", "status");
    if (!change.reviewed) {
      item.append(action("Mark reviewed", button => perform(button, feedback, async () => {
        await api(path + "/review", {method:"PUT"});
        await loadHistory(state, false, run.id);
      })));
    }
    const editor = element("details");
    const form = element("form");
    const label = element("label", "What does the evidence support?");
    const body = element("textarea");
    body.rows = 3;
    body.required = true;
    body.maxLength = 5000;
    label.append(body);
    const submit = element("button", "Save cited finding", "primary");
    submit.type = "submit";
    form.append(label, submit);
    form.addEventListener("submit", event => {
      event.preventDefault();
      perform(submit, feedback, async () => {
        await api(path + "/finding", {method:"PUT", body:{body:body.value}});
        await loadHistory(state, false, run.id);
      });
    });
    editor.append(element("summary", "Create cited finding"), form);
    item.append(editor, feedback);
    return item;
  }

  function changeList(state, run) {
    const groups = new Map();
    for (const change of run.changes) {
      const key = change.group_key || change.id;
      const group = groups.get(key) || [];
      group.push(change);
      groups.set(key, group);
    }
    const list = element("ul", "", "investigation-list");
    for (const records of groups.values()) {
      if (records.length === 1) {
        list.append(changeCard(state, run, records[0]));
      } else {
        const group = element("li", "", "investigation-group");
        const collapse = element("details");
        const nested = element("ul", "", "investigation-list");
        const domains = new Set(records.map(item => item.record.publisher_domain)).size;
        collapse.append(element("summary", records.length + " records share this headline across " + domains
          + (domains === 1 ? " domain" : " domains")),
        element("p", records[0].record.title),
        element("p", "Check the bylines before treating coverage as independent.", "report-meta"));
        nested.append(...records.map(change => changeCard(state, run, change)));
        collapse.append(nested);
        group.append(collapse);
        list.append(group);
      }
    }
    return list;
  }

  function renderRun(state, run) {
    detail.replaceChildren(element("h3", "Run " + run.sequence), element("p", dateTime(run.finished_at), "report-meta"));
    if (run.error) {
      detail.append(element("p", run.error, "notice"));
      return;
    }
    const coverage = element("details");
    const sources = element("ul", "", "investigation-list");
    coverage.append(element("summary", "Source coverage"));
    for (const source of run.sources.filter(item => item.query)) {
      const retained = source.retained ? (source.baseline ? " · Baseline recorded" : "") : " · Run history off";
      const row = element("li");
      row.append(element("strong", source.name), element("p", labels[source.status] + retained, "report-meta"));
      if (source.reason) row.append(element("p", source.reason));
      sources.append(row);
    }
    coverage.append(sources);
    detail.append(coverage, element("h3", "Changes to review"));
    if (run.changes.length) detail.append(changeList(state, run));
    else detail.append(element("p", "No new or updated records in this run.", "report-meta"));
    if (run.insights.length) {
      const snapshotInsights = element("details");
      snapshotInsights.append(element("summary", "Insights from this run"));
      const byRecord = new Map(run.records.map(record => [record.id, record]));
      for (const insight of run.insights) {
        const cite = element("ul");
        for (const id of insight.record_ids) {
          const record = byRecord.get(id);
          if (!record) continue;
          const row = element("li");
          row.append(original(record, record.source + " · " + record.title));
          cite.append(row);
        }
        snapshotInsights.append(element("h4", insight.title), element("p", insight.explanation, "report-meta"), cite);
      }
      detail.append(snapshotInsights);
    }
    if (run.records.length) {
      const snapshot = element("details");
      snapshot.append(element("summary", "Records retained in this run (" + run.records.length + ")"));
      const list = element("ul", "", "investigation-list");
      for (const record of run.records) {
        const row = element("li", "", "investigation-change");
        row.append(element("strong", record.title), element("p", provenance(record), "report-meta"), original(record));
        list.append(row);
      }
      snapshot.append(list);
      detail.append(snapshot);
    }
  }

  async function selectRun(state, id) {
    const selected = endpoint(state) + "/runs/" + id;
    const request = {};
    state.detailRequest = request;
    try {
      const run = await api(selected);
      if (current === state && state.detailRequest === request) {
        for (const button of runList.querySelectorAll("button")) {
          button.setAttribute("aria-pressed", String(button.dataset.runId === run.id));
        }
        renderRun(state, run);
      }
    } catch (error) {
      if (current === state && state.detailRequest === request) status.textContent = error.message;
    }
  }

  async function loadHistory(state, append = false, requested = null) {
    const id = selector.value;
    const request = {};
    state.historyRequest = request;
    if (!append) {
      state.detailRequest = null;
      state.next = null;
      runList.replaceChildren();
      detail.replaceChildren();
      pending.textContent = "";
      older.hidden = true;
    }
    const query = append && state.next ? "?before=" + encodeURIComponent(state.next) : "";
    const page = await api(endpoint(state) + "/runs" + query);
    if (current !== state || state.historyRequest !== request || selector.value !== id) return;
    state.next = page.next_before;
    older.hidden = !state.next;
    pending.textContent = page.pending_count ? page.pending_count + " to review across runs" : "Review queue clear";
    for (const run of page.runs) {
      const row = element("li");
      const note = run.error ? " · Run failed" : run.pending_count ? " · " + run.pending_count + " to review" : "";
      const button = action("Run " + run.sequence + note, () => selectRun(state, run.id));
      button.dataset.runId = run.id;
      button.setAttribute("aria-pressed", "false");
      row.append(button, element("p", dateTime(run.finished_at), "report-meta"));
      runList.append(row);
    }
    if (append) return;
    const first = requested || page.runs.find(run => run.pending_count)?.id || page.runs[0]?.id;
    if (first) await selectRun(state, first);
    else detail.append(element("p", "Run this investigation to establish its baseline.", "report-meta"));
  }

  function showSchedule(state) {
    const row = state.items.find(item => item.id === selector.value);
    const interval = row?.interval_minutes ? String(row.interval_minutes) : "";
    frequency.querySelector("[data-custom-interval]")?.remove();
    if (interval && ![...frequency.options].some(item => item.value === interval)) {
      const custom = new Option("Every " + interval + " minutes", interval);
      custom.dataset.customInterval = "true";
      frequency.add(custom);
    }
    frequency.value = interval;
    byId("investigation-next").textContent = row?.next_run ? "Next run " + dateTime(row.next_run) : "";
  }

  async function refreshSchedule(state) {
    const result = await api(endpoint(state, ""));
    if (current !== state) return;
    state.items = result.investigations;
    schedule.hidden = !result.scheduling_enabled;
    showSchedule(state);
  }

  async function open(caseId, selectedId = null) {
    if (!caseId || dialog.open) return;
    const state = {caseId, items:[]};
    current = state;
    byId("investigation-controls").hidden = true;
    status.textContent = "Loading saved investigations.";
    dialog.showModal();
    try {
      const result = await api(endpoint(state, ""));
      if (current !== state) return;
      state.items = result.investigations;
      if (!state.items.length) {
        status.textContent = "Save a workbench search to this case to track its changes.";
        return;
      }
      selector.replaceChildren(...state.items.map(item => new Option(item.query, item.id)));
      if (selectedId) selector.value = selectedId;
      schedule.hidden = !result.scheduling_enabled;
      status.textContent = result.retained_sources.length
        ? "Run history retains record metadata for " + result.retained_sources.join(", ") + "."
        : "Run history is configured to retain source coverage only.";
      showSchedule(state);
      byId("investigation-controls").hidden = false;
      await loadHistory(state);
    } catch (error) {
      if (current === state) status.textContent = error.message;
    }
  }

  dialog.addEventListener("close", () => {current = null;});
  byId("open-investigations").addEventListener("click", () => open(activeCase()));
  selector.addEventListener("change", () => {
    const state = current;
    if (!state) return;
    showSchedule(state);
    loadHistory(state).catch(error => {if (current === state) status.textContent = error.message;});
  });
  byId("investigation-run-now").addEventListener("click", event => {
    const state = current;
    if (!state) return;
    const id = selector.value;
    status.textContent = "Running saved investigation.";
    perform(event.currentTarget, status, async () => {
      const run = await api(endpoint(state) + "/runs", {method:"POST"});
      if (current === state && selector.value === id) {
        status.textContent = run.error || "Run completed.";
        await Promise.all([loadHistory(state, false, run.id), refreshSchedule(state)]);
      }
    });
  });
  byId("investigation-refresh").addEventListener("click", event => {
    const state = current;
    if (state) perform(event.currentTarget, status, () => Promise.all([loadHistory(state), refreshSchedule(state)]));
  });
  older.addEventListener("click", () => {
    if (current) perform(older, status, () => loadHistory(current, true));
  });
  schedule.addEventListener("submit", event => {
    event.preventDefault();
    const state = current;
    if (!state) return;
    perform(event.submitter, status, async () => {
      const item = await api(endpoint(state) + "/schedule", {
        method:"PUT", body:{interval_minutes:frequency.value ? Number(frequency.value) : null},
      });
      if (current !== state) return;
      state.items = state.items.map(previous => previous.id === item.id ? item : previous);
      showSchedule(state);
      status.textContent = "Schedule saved.";
    });
  });
  save.addEventListener("click", () => {
    const caseId = activeCase();
    if (!caseId) {
      saveStatus.textContent = "Create or select a case before saving the search.";
      return;
    }
    if (!search) return;
    const captured = search;
    perform(save, saveStatus, async () => {
      const item = await api(endpoint({caseId}, ""), {method:"POST", body:captured});
      if (captured === search && activeCase() === caseId) {
        saveStatus.textContent = "Search saved to case.";
        await open(caseId, item.id);
      }
    });
  });

  return {
    clearSearch() {search = null; saveStatus.textContent = "";},
    setSearch(query) {search = query; saveStatus.textContent = "";},
  };
}
