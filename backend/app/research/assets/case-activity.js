export function wireCaseActivity(api, selectedCase, showTime) {
  const byId = id => document.getElementById(id);
  const dialog = byId("activity-dialog");
  const status = byId("activity-status");
  const events = byId("activity-events");
  const older = byId("activity-older");
  const labels = {
    case_created: "Case created",
    evidence_saved: "Evidence saved",
    finding_added: "Report entry added",
    finding_edited: "Report entry edited",
    screening_reviewed: "Organization identity reviewed",
  };
  let pending;
  let before;

  function render(event) {
    const row = document.createElement("li");
    const label = document.createElement("strong");
    label.textContent = labels[event.action] + (event.version ? " · Revision " + event.version : "");
    const time = document.createElement("time");
    time.dateTime = event.occurred_at;
    time.textContent = showTime(event.occurred_at);
    row.append(label, time);
    return row;
  }

  async function load() {
    const caseId = selectedCase();
    if (pending || !caseId) return;
    const request = new AbortController();
    pending = request;
    status.textContent = "Loading activity…";
    older.disabled = true;
    const query = before ? "?before=" + encodeURIComponent(before) : "";
    try {
      const result = await api("/cases/" + encodeURIComponent(caseId) + "/activity" + query, {signal:request.signal});
      if (pending !== request) return;
      events.append(...result.events.map(render));
      status.textContent = events.children.length ? "" : "No recorded activity for this case yet.";
      before = result.next_before;
    } catch (failure) {
      if (pending === request) status.textContent = failure.message;
    } finally {
      if (pending === request) {
        pending = undefined;
        older.hidden = !before;
        older.disabled = false;
      }
    }
  }

  byId("open-case-activity").addEventListener("click", () => {
    if (!selectedCase()) return;
    before = null;
    events.replaceChildren();
    older.hidden = true;
    dialog.showModal();
    load();
  });
  older.addEventListener("click", load);
  dialog.addEventListener("close", () => {
    pending?.abort();
    pending = undefined;
  });
}
