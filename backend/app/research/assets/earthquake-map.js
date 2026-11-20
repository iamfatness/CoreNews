const get = id => document.getElementById(id);

function node(tag, text) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  return element;
}

export function wireEarthquakeMap(api, selectedCase) {
  const dialog = get("earthquake-dialog");
  const markers = get("earthquake-markers");
  const list = get("earthquake-list");
  const details = get("earthquake-detail");
  const exportButton = get("export-earthquakes");
  let entries = [];
  let active;
  let generation = 0;
  let pending;

  function status(message) {
    get("earthquake-status").textContent = message;
  }

  function open(entry, marker, button) {
    active = entry;
    for (const circle of markers.children) circle.dataset.selected = String(circle === marker);
    for (const item of list.querySelectorAll("button")) item.setAttribute("aria-pressed", String(item === button));
    const {record} = entry;
    const original = node("a", "Open original USGS event");
    original.href = record.source_url;
    original.target = "_blank";
    original.rel = "noopener noreferrer";
    const save = node("button", "Save event to case");
    save.type = "button";
    save.className = "secondary";
    save.disabled = !selectedCase();
    const feedback = node("p", save.disabled ? "Select a case to save this event." : "");
    feedback.setAttribute("role","status");
    save.addEventListener("click", async () => {
      save.disabled = true;
      try {
        await api("/cases/" + selectedCase() + "/evidence", {method:"PUT", body:entry});
        if (active === entry) feedback.textContent = "Saved to the case.";
      } catch (error) {
        if (active === entry) feedback.textContent = error.message;
      } finally {
        if (active === entry) save.disabled = false;
      }
    });
    details.replaceChildren(node("strong", record.title),
      node("p", "Magnitude " + record.magnitude + " · depth " + record.depth_km + " km"),
      node("p", "Epicenter " + record.latitude + ", " + record.longitude),
      node("p", record.occurred_at ? "Occurred " + record.occurred_at : "Event time unavailable"),
      original, node("p"), save, feedback);
  }

  function render(result) {
    entries = result.records;
    for (const entry of entries) {
      const {record} = entry;
      const marker = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      marker.setAttribute("cx", (record.longitude + 180) * 2);
      marker.setAttribute("cy", (90 - record.latitude) * 2);
      marker.setAttribute("r", Math.max(4, Math.min(10, record.magnitude * 1.6)));
      const button = node("button", record.title);
      button.type = "button";
      button.className = "secondary";
      button.setAttribute("aria-pressed","false");
      for (const control of [marker, button]) control.addEventListener("click", () => open(entry, marker, button));
      const item = node("li");
      item.append(button);
      markers.append(marker);
      list.append(item);
    }
    exportButton.disabled = !entries.length;
    status(entries.length ? "Showing " + entries.length + " of " + result.available + " matching events."
      : "No USGS events match these filters.");
  }

  function clear() {
    entries = [];
    active = undefined;
    markers.replaceChildren();
    list.replaceChildren();
    details.replaceChildren();
    exportButton.disabled = true;
  }

  async function load() {
    pending?.abort();
    const request = new AbortController();
    pending = request;
    const current = generation;
    clear();
    status("Loading public USGS events.");
    const params = new URLSearchParams({
      window: get("earthquake-window").value,
      region: get("earthquake-region").value,
      min_magnitude: get("earthquake-min").value,
    });
    try {
      const data = await api("/geo/earthquakes?" + params, {signal:request.signal});
      if (current === generation && !request.signal.aborted) render(data);
    } catch (error) {
      if (current === generation && !request.signal.aborted) status(error.message);
    } finally {
      if (pending === request) pending = undefined;
    }
  }

  get("open-earthquake-map").addEventListener("click", () => {
    if (dialog.open) return;
    generation += 1;
    dialog.showModal();
    load();
  });
  get("earthquake-filters").addEventListener("submit", event => {
    event.preventDefault();
    load();
  });
  dialog.addEventListener("close", () => {
    generation += 1;
    pending?.abort();
    clear();
  });
  exportButton.addEventListener("click", () => {
    const collection = {type:"FeatureCollection", features:entries.map(({record}) => ({
      type:"Feature", id:record.id,
      geometry:{type:"Point", coordinates:[record.longitude, record.latitude]},
      properties:{title:record.title, magnitude:record.magnitude, depth_km:record.depth_km,
        occurred_at:record.occurred_at, collected_at:record.collected_at, source:record.source,
        source_url:record.source_url},
    }))};
    const url = URL.createObjectURL(new Blob([JSON.stringify(collection, null, 2)], {type:"application/geo+json"}));
    const link = node("a");
    link.href = url;
    link.download = "corenews-earthquakes.geojson";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
}
