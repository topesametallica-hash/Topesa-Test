const relayTiles = [...document.querySelectorAll(".relay-tile")];
const allOffButton = document.querySelector("#allOffButton");
const statusText = document.querySelector("#statusText");

function setRelay(tile, enabled) {
  tile.classList.toggle("is-on", enabled);
  tile.querySelector(".relay-state").textContent = enabled ? "ON" : "OFF";
}

relayTiles.forEach((tile) => {
  tile.addEventListener("click", () => {
    const enabled = !tile.classList.contains("is-on");
    setRelay(tile, enabled);
    statusText.textContent = `${tile.dataset.relay} set to ${enabled ? "ON" : "OFF"}`;
  });
});

allOffButton.addEventListener("click", () => {
  relayTiles.forEach((tile) => setRelay(tile, false));
  statusText.textContent = "All relays are OFF";
});
