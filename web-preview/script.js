const relayTiles = [...document.querySelectorAll(".relay-tile")];
const allOffButton = document.querySelector("#allOffButton");
const statusText = document.querySelector("#statusText");

const relayState = {};

function setRelay(tile, enabled) {
  tile.classList.toggle("is-on", enabled);
  tile.querySelector(".relay-state").textContent = enabled ? "ON" : "OFF";

  relayState[tile.dataset.relay] = enabled;
}

function syncRelayTiles() {
  relayTiles.forEach((tile) => {
    const relayName = tile.dataset.relay;
    const enabled = relayState[relayName] || false;

    tile.classList.toggle("is-on", enabled);
    tile.querySelector(".relay-state").textContent = enabled ? "ON" : "OFF";
  });
}

function broadcastRelayUpdate(relayName, enabled) {
  relayState[relayName] = enabled;

  localStorage.setItem(
    "relay-sync-state",
    JSON.stringify({
      relayState,
      updatedAt: Date.now(),
    })
  );
}

function loadRelayState() {
  const saved = localStorage.getItem("relay-sync-state");

  if (!saved) {
    return;
  }

  try {
    const parsed = JSON.parse(saved);

    Object.assign(relayState, parsed.relayState || {});

    syncRelayTiles();
  } catch (error) {
    console.error("Failed to load relay state", error);
  }
}

relayTiles.forEach((tile) => {
  tile.addEventListener("click", () => {
    const enabled = !tile.classList.contains("is-on");

    setRelay(tile, enabled);
    broadcastRelayUpdate(tile.dataset.relay, enabled);

    statusText.textContent = `${tile.dataset.relay} set to ${enabled ? "ON" : "OFF"}`;
  });
});

allOffButton.addEventListener("click", () => {
  relayTiles.forEach((tile) => {
    setRelay(tile, false);
    broadcastRelayUpdate(tile.dataset.relay, false);
  });

  statusText.textContent = "All relays are OFF";
});

window.addEventListener("storage", (event) => {
  if (event.key !== "relay-sync-state") {
    return;
  }

  loadRelayState();
});

loadRelayState();

setInterval(loadRelayState, 1000);
