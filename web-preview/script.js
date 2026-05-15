const relayTiles = [...document.querySelectorAll(".relay-tile")];
const allOffButton = document.querySelector("#allOffButton");
const statusText = document.querySelector("#statusText");

const relayState = {};
const API_URL = "/api/relays";

function updateTile(tile, enabled) {
  tile.classList.toggle("is-on", enabled);
  tile.querySelector(".relay-state").textContent = enabled ? "ON" : "OFF";
}

function syncRelayTiles() {
  relayTiles.forEach((tile) => {
    const relayName = tile.dataset.relay;
    const enabled = relayState[relayName] || false;

    updateTile(tile, enabled);
  });
}

async function fetchRelayState() {
  try {
    const response = await fetch(API_URL);
    const data = await response.json();

    Object.assign(relayState, data);

    syncRelayTiles();
  } catch (error) {
    console.error("Failed to fetch relay state", error);
  }
}

async function pushRelayState() {
  try {
    await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(relayState),
    });
  } catch (error) {
    console.error("Failed to push relay state", error);
  }
}

relayTiles.forEach((tile) => {
  tile.addEventListener("click", async () => {
    const relayName = tile.dataset.relay;
    const enabled = !tile.classList.contains("is-on");

    relayState[relayName] = enabled;

    updateTile(tile, enabled);

    await pushRelayState();

    statusText.textContent = `${relayName} set to ${enabled ? "ON" : "OFF"}`;
  });
});

allOffButton.addEventListener("click", async () => {
  relayTiles.forEach((tile) => {
    relayState[tile.dataset.relay] = false;
    updateTile(tile, false);
  });

  await pushRelayState();

  statusText.textContent = "All relays are OFF";
});

fetchRelayState();
setInterval(fetchRelayState, 1000);
