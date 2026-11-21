const statusLabels = {
  results: "Records returned",
  no_match: "No matching records",
  setup_required: "Setup required",
  unavailable: "Temporarily unavailable",
  not_applicable: "Outside this query",
};

const intentLabels = {
  domain: "Domain",
  organization: "Organization",
  advisory: "CVE",
  earthquake: "Earthquake",
  topic: "News topic",
};

function node(tag, value) {
  const element = document.createElement(tag);
  if (value) element.textContent = value;
  return element;
}

export function renderResearchSummary(data, reveal) {
  const byId = id => document.getElementById(id);
  const statuses = byId("research-source-status");
  const insights = byId("research-insight-list");
  const records = new Map(data.records.map(item => [item.record.id, item.record]));
  const completed = data.sources.filter(source => ["results", "no_match"].includes(source.status)).length;
  const blocked = data.sources.filter(source => ["unavailable", "setup_required"].includes(source.status)).length;
  byId("research-coverage-label").textContent = "Source coverage · " + intentLabels[data.intent] + " · " + completed + " checked"
    + (blocked ? " · " + blocked + (blocked === 1 ? " needs attention" : " need attention") : "");
  byId("research-coverage").open = !data.records.length;
  statuses.replaceChildren(...data.sources.map(source => {
    const item = node("li");
    const heading = node("strong", source.name);
    const status = node("span", source.status === "results"
      ? (source.shown === source.available ? source.shown + " shown" : source.shown + " shown of " + source.available + " source rows")
      : statusLabels[source.status]);
    status.dataset.sourceStatus = source.status;
    item.append(heading, status);
    if (source.query || source.reason) {
      item.append(node("p", [source.query && "Query: " + source.query, source.reason].filter(Boolean).join(" · ")));
    }
    return item;
  }));
  insights.replaceChildren(...data.insights.map(insight => {
    const item = node("li");
    const references = node("ul");
    for (const id of insight.record_ids) {
      const record = records.get(id);
      if (!record) continue;
      const citation = node("li");
      const button = node("button", record.source + " · " + record.title);
      button.className = "insight-link";
      button.type = "button";
      button.addEventListener("click", () => reveal(id));
      citation.append(button);
      references.append(citation);
    }
    item.append(node("h4", insight.title), node("p", insight.explanation), references);
    return item;
  }));
  byId("research-insights").hidden = !data.insights.length;
  byId("workbench-summary").hidden = false;
}
