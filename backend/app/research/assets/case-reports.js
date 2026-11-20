const byId = id => document.getElementById(id);

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}

function sourceLink(value) {
  try {
    const parsed = new URL(value);
    if (["https:", "http:"].includes(parsed.protocol) && !parsed.username && !parsed.password) {
      const link = node("a", parsed.href, "report-url");
      link.href = parsed.href;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      return link;
    }
  } catch {
    // Unreadable or unrecognized links stay out of the report.
  }
  return null;
}

function downloadFile(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function buildReport(report, onEdit) {
  const fragment = document.createDocumentFragment();
  const sources = new Map(report.evidence.map(item => [item.id, item]));
  fragment.append(
    node("p", "CoreNews · Case report", "report-eyebrow"),
    node("h2", report.case.title),
    node("p", "Generated " + report.exported_at, "report-meta"),
  );
  if (report.uncited_findings) {
    const count = report.uncited_findings;
    fragment.append(node("p", count + (count === 1 ? " finding needs a citation." : " findings need citations."), "notice"));
  }

  for (const [kind, heading, empty] of [
    ["finding", "Findings", "No findings recorded."],
    ["question", "Open questions", "No open questions recorded."],
  ]) {
    fragment.append(node("h3", heading));
    const entries = report.findings.filter(finding => finding.kind === kind);
    if (!entries.length) fragment.append(node("p", empty, "report-meta"));
    for (const finding of entries) {
      const card = node("section", undefined, "finding-entry");
      card.append(node("p", finding.body, "finding-text"));
      if (finding.uncited) card.append(node("p", "Citation needed", "report-warning"));
      const refs = node("ul", undefined, "report-cites");
      for (const id of finding.evidence_ids) {
        const item = sources.get(id);
        const reference = node("li");
        if (!item) {
          reference.textContent = "Evidence unavailable";
        } else {
          const link = node("a", "[" + item.label + "]");
          link.href = "#report-source-" + item.label;
          link.setAttribute("aria-label", "Evidence " + item.label + ": " + item.title);
          reference.append(link);
          if (!item.metadata_available || item.verification === "mismatch") {
            reference.append(" · needs review");
          }
        }
        refs.append(reference);
      }
      if (refs.children.length) card.append(refs);
      const edit = node("button", "Edit entry", "secondary report-edit");
      edit.type = "button";
      edit.addEventListener("click", () => onEdit(finding));
      card.append(edit);
      fragment.append(card);
    }
  }

  fragment.append(node("h3", "Evidence and integrity"));
  if (!report.evidence.length) fragment.append(node("p", "No evidence saved in this case.", "report-meta"));
  for (const item of report.evidence) {
    const entry = node("section", undefined, "report-source");
    entry.id = "report-source-" + item.label;
    entry.append(
      node("h4", "[" + item.label + "] " + item.title),
      node("p", [item.source, item.source_date && item.date_label + " " + item.source_date,
        item.collected_at && item.date_label !== "Collected by CoreNews" && "Collected " + item.collected_at,
        "Saved " + item.saved_at]
        .filter(Boolean).join(" · "), "report-meta"),
    );
    const original = sourceLink(item.source_url);
    if (original) entry.append(original);
    if (item.source_snapshot_sha256) {
      entry.append(node("p", "OFAC list entry " + item.source_entry_id + " · Snapshot SHA-256 " + item.source_snapshot_sha256, "report-meta"));
    }
    if (item.source_version) entry.append(node("p", "Catalog version " + item.source_version, "report-meta"));
    const states = {
      verified: "Saved metadata hash verified",
      mismatch: "Saved metadata hash mismatch",
      not_captured: "No snapshot hash captured",
    };
    entry.append(node("p", states[item.verification], item.verification === "mismatch" ? "report-warning" : "report-meta"));
    if (item.snapshot_sha256) entry.append(node("code", "SHA-256 " + item.snapshot_sha256));
    fragment.append(entry);
  }
  return fragment;
}

export function wireCaseReports(api, selectedCase) {
  const dialog = byId("case-report-dialog");
  const form = byId("finding-form");
  const editor = byId("finding-body");
  const choices = byId("finding-citations");
  const preview = byId("report-document");
  const download = byId("report-json");
  const evidenceCsv = byId("report-csv");
  const print = byId("report-print");
  const refresh = byId("report-refresh");
  const submit = byId("finding-save");
  let report;
  let editing;
  let caseId;
  let dialogGeneration = 0;

  function status(message) {
    byId("report-status").textContent = message;
  }

  function editingState(finding) {
    editing = finding;
    byId("finding-kind").value = finding?.kind || "finding";
    editor.value = finding?.body || "";
    byId("finding-form-title").textContent = finding ? "Edit an entry" : "Add a finding or question";
    byId("finding-cancel").hidden = !finding;
    for (const input of choices.querySelectorAll("input")) {
      input.checked = !!finding?.evidence_ids.includes(input.value);
    }
    if (finding) editor.focus();
  }

  function display(current) {
    const checked = new Set([...choices.querySelectorAll("input:checked")].map(input => input.value));
    report = current;
    choices.replaceChildren(...report.evidence.map(item => {
      const label = node("label", undefined, "citation-choice");
      const input = document.createElement("input");
      input.type = "checkbox";
      input.value = item.id;
      input.checked = checked.has(item.id);
      label.append(input, "[" + item.label + "] " + item.title);
      return label;
    }));
    byId("finding-no-evidence").hidden = report.evidence.length > 0;
    preview.replaceChildren(buildReport(report, editingState));
    form.hidden = false;
    download.disabled = false;
    evidenceCsv.disabled = false;
    print.disabled = false;
  }

  async function load(message = "") {
    const generation = dialogGeneration;
    refresh.disabled = true;
    try {
      const current = await api("/cases/" + caseId + "/report");
      if (generation !== dialogGeneration) return;
      display(current);
      status(message);
    } catch (failure) {
      if (generation === dialogGeneration) status(failure.message);
    } finally {
      if (generation === dialogGeneration) refresh.disabled = false;
    }
  }

  byId("open-case-report").addEventListener("click", () => {
    const target = selectedCase();
    if (!target || dialog.open) return;
    dialogGeneration += 1;
    caseId = target;
    report = undefined;
    choices.replaceChildren();
    preview.replaceChildren();
    editingState(undefined);
    form.hidden = true;
    download.disabled = true;
    evidenceCsv.disabled = true;
    print.disabled = true;
    submit.disabled = false;
    status("Loading case report.");
    dialog.showModal();
    load();
  });
  dialog.addEventListener("close", () => {
    dialogGeneration += 1;
  });
  refresh.addEventListener("click", () => {
    if (editing) {
      editingState(undefined);
      load("Report refreshed. Reopen the entry to edit the latest version.");
    } else load("Report refreshed.");
  });
  byId("finding-cancel").addEventListener("click", () => editingState(undefined));
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const evidenceIds = [...choices.querySelectorAll("input:checked")].map(input => input.value);
    if (evidenceIds.length > 25) {
      status("Select up to 25 evidence records for an entry.");
      return;
    }
    const generation = dialogGeneration;
    const body = {kind:byId("finding-kind").value, body:editor.value, evidence_ids:evidenceIds};
    let path = "/cases/" + caseId + "/findings";
    if (editing) {
      body.version = editing.version;
      path += "/" + editing.id;
    }
    submit.disabled = true;
    refresh.disabled = true;
    try {
      await api(path, {method:editing ? "PUT" : "POST", body});
      if (generation !== dialogGeneration) return;
      editingState(undefined);
      await load("Entry saved.");
    } catch (failure) {
      if (generation === dialogGeneration) status(failure.message);
    } finally {
      if (generation === dialogGeneration) {
        submit.disabled = false;
        refresh.disabled = false;
      }
    }
  });
  download.addEventListener("click", () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2) + "\n"], {type:"application/json"});
    downloadFile(blob, "corenews-case-" + report.case.id + ".json");
  });
  evidenceCsv.addEventListener("click", async () => {
    if (!report) return;
    const generation = dialogGeneration;
    const target = caseId;
    evidenceCsv.disabled = true;
    try {
      const csv = await api("/cases/" + target + "/evidence.csv", {download:true});
      if (generation === dialogGeneration) downloadFile(csv, "corenews-case-" + target + "-evidence.csv");
    } catch (failure) {
      if (generation === dialogGeneration) status(failure.message);
    } finally {
      if (generation === dialogGeneration) evidenceCsv.disabled = false;
    }
  });
  print.addEventListener("click", () => window.print());
}
