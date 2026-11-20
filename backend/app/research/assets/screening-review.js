export const screeningDecisions = {
  same_organization: "Same organization",
  different_organization: "Different organization",
  inconclusive: "Inconclusive",
};

export function wireScreeningReview(api, selectedEvidence) {
  const byId = id => document.getElementById(id);
  const dialog = byId("screening-review-dialog");
  const form = byId("screening-review-form");
  const decision = byId("screening-decision");
  const rationale = byId("screening-rationale");
  const status = byId("screening-review-status");
  const submit = form.querySelector("button[type=submit]");
  let session;

  byId("review-screening-record").addEventListener("click", async () => {
    const selection = selectedEvidence();
    if (!selection?.id || !selection.caseId || dialog.open) return;
    const {record} = selection;
    const path = "/cases/" + encodeURIComponent(selection.caseId)
      + "/evidence/" + encodeURIComponent(selection.id) + "/screening-review";
    const current = {path, version:0};
    session = current;
    form.hidden = true;
    form.reset();
    submit.disabled = false;
    byId("screening-review-record").textContent = record.title + " · SDN entry " + record.list_uid
      + " · Snapshot published " + record.published_on;
    byId("screening-review-source").href = record.source_url;
    status.textContent = "Loading identity review…";
    dialog.showModal();
    try {
      const review = await api(path);
      if (session !== current) return;
      if (review) {
        current.version = review.version;
        decision.value = review.decision;
        rationale.value = review.rationale;
      }
      status.textContent = review ? "Review revision " + review.version + "." : "Review pending.";
      form.hidden = false;
      decision.focus();
    } catch (failure) {
      if (session === current) status.textContent = failure.message;
    }
  });
  dialog.addEventListener("close", () => { session = undefined; });
  form.addEventListener("submit", async event => {
    event.preventDefault();
    if (!session || submit.disabled) return;
    const current = session;
    submit.disabled = true;
    try {
      const review = await api(current.path, {
        method:"PUT", body:{decision:decision.value, rationale:rationale.value, version:current.version},
      });
      if (session !== current) return;
      current.version = review.version;
      status.textContent = "Identity review saved. Revision " + review.version + ".";
    } catch (failure) {
      if (session === current) status.textContent = failure.message;
    } finally {
      if (session === current) submit.disabled = false;
    }
  });
}
