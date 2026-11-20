export function wireOfacScreening(api, selectedCase) {
  const byId = id => document.getElementById(id);
  const dialog = byId("ofac-dialog");
  const form = byId("ofac-form");
  const status = byId("ofac-status");
  const version = byId("ofac-version");
  const results = byId("ofac-results");
  let pending;

  function candidate(selection) {
    const {record} = selection;
    const item = document.createElement("li");
    const title = document.createElement("strong");
    title.textContent = record.title;
    const metadata = document.createElement("p");
    metadata.textContent = "List entry " + record.list_uid + " · " + (record.programs.join(", ") || "Program unavailable");
    const source = document.createElement("a");
    source.textContent = "Open OFAC Sanctions List Service";
    source.href = record.source_url;
    source.target = "_blank";
    source.rel = "noopener noreferrer";
    const actions = document.createElement("div");
    actions.className = "case-actions";
    const save = document.createElement("button");
    save.type = "button";
    save.className = "secondary";
    save.disabled = !selectedCase();
    save.textContent = "Save candidate to case";
    const feedback = document.createElement("p");
    feedback.setAttribute("role", "status");
    feedback.textContent = save.disabled ? "Select a case before screening to save candidates." : "";
    save.addEventListener("click", async () => {
      const caseId = selectedCase();
      if (!caseId) return;
      save.disabled = true;
      try {
        await api("/cases/" + encodeURIComponent(caseId) + "/evidence", {method:"PUT", body:selection});
        feedback.textContent = "Candidate saved to case evidence for review.";
      } catch (failure) {
        feedback.textContent = failure.message;
        save.disabled = false;
      }
    });
    actions.append(source, save);
    item.append(title, metadata, actions, feedback);
    return item;
  }

  byId("open-ofac-screening").addEventListener("click", () => {
    results.replaceChildren();
    status.textContent = "";
    version.textContent = "";
    dialog.showModal();
    byId("ofac-name").focus();
  });
  dialog.addEventListener("close", () => {
    pending?.abort();
    pending = undefined;
  });
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const name = byId("ofac-name").value.trim();
    const snapshotId = byId("ofac-snapshot").value.trim();
    pending?.abort();
    results.replaceChildren();
    version.textContent = "";
    if (!name) {
      status.textContent = "Enter an organization name.";
      byId("ofac-name").focus();
      return;
    }
    const request = new AbortController();
    pending = request;
    status.textContent = "Checking the snapshot…";
    try {
      const data = await api("/screening/ofac", {
        method:"POST", body:{name, snapshot_id:snapshotId || null}, signal:request.signal,
      });
      if (pending !== request) return;
      version.textContent = "Published " + data.snapshot.published_on + " · SHA-256 " + data.snapshot.id;
      results.replaceChildren(...data.records.map(candidate));
      status.textContent = data.records.length
        ? "Exact name candidates. Verify the organization's identity before drawing a conclusion."
        : "No exact organization-name candidates in this snapshot. This lookup cannot establish sanctions status.";
    } catch (failure) {
      if (pending === request) status.textContent = failure.message;
    }
  });
}
