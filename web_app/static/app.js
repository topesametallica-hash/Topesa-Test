const relayGrid = document.querySelector("#relayGrid");
const relayTemplate = document.querySelector("#relayTemplate");
const statusText = document.querySelector("#statusText");
const clockText = document.querySelector("#clockText");
const modePill = document.querySelector("#modePill");
const allOffButton = document.querySelector("#allOffButton");

const tiles = new Map();

function setStatus(message) {
  statusText.textContent = message;
}

function updateClock() {
  clockText.textContent = new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date());
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

function renderState(state) {
  modePill.textContent = state.mode.toUpperCase();
  modePill.classList.toggle("is-demo", state.mode === "demo");
  modePill.classList.toggle("is-gpio", state.mode === "gpio");

  state.relays.forEach((relay) => {
    let tile = tiles.get(relay.id);
    if (!tile) {
      tile = relayTemplate.content.firstElementChild.cloneNode(true);
      tile.dataset.id = relay.id;
      tile.querySelector(".relay-name").textContent = relay.name;
      tile.querySelector(".relay-pin").textContent = `GPIO ${relay.pin}`;
      tile.addEventListener("click", () => toggleRelay(relay.id));
      tiles.set(relay.id, tile);
      relayGrid.append(tile);
    }

    tile.dataset.on = relay.on ? "1" : "0";
    tile.classList.toggle("is-on", relay.on);
    tile.querySelector(".relay-state").textContent = relay.on ? "ON" : "OFF";
  });
}

async function loadState() {
  try {
    renderState(await requestJson("/api/state"));
    setStatus("Ready");
  } catch (error) {
    setStatus("Cannot connect to relay server");
  }
}

async function toggleRelay(relayId) {
  const tile = tiles.get(relayId);
  const next = tile.dataset.on !== "1";
  tile.classList.add("is-busy");
  try {
    renderState(
      await requestJson(`/api/relays/${encodeURIComponent(relayId)}`, {
        method: "POST",
        body: JSON.stringify({ on: next }),
      })
    );
    const name = tile.querySelector(".relay-name").textContent;
    setStatus(`${name} set to ${next ? "ON" : "OFF"}`);
  } catch (error) {
    setStatus("Relay command failed");
  } finally {
    tile.classList.remove("is-busy");
  }
}

allOffButton.addEventListener("click", async () => {
  allOffButton.disabled = true;
  try {
    renderState(await requestJson("/api/all-off", { method: "POST" }));
    setStatus("All relays are OFF");
  } catch (error) {
    setStatus("All off command failed");
  } finally {
    allOffButton.disabled = false;
  }
});

updateClock();
setInterval(updateClock, 1000);
loadState();
