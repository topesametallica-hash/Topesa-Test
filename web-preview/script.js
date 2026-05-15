const relayTiles = [...document.querySelectorAll('.relay-tile')];
const allOffButton = document.querySelector('#allOffButton');
const statusText = document.querySelector('#statusText');

const SUPABASE_URL = 'https://jbvqrzidxhfihqlpbryq.supabase.co';
const SUPABASE_KEY = 'sb_publishable_Ucz350hs8Df0_CwQq2mRfw_jz-9qSbM';

const supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

function updateTile(tile, enabled) {
  tile.classList.toggle('is-on', enabled);
  tile.querySelector('.relay-state').textContent = enabled ? 'ON' : 'OFF';
}

async function loadRelayState() {
  const { data, error } = await supabaseClient
    .from('relay_state')
    .select('*');

  if (error) {
    console.error(error);
    return;
  }

  data.forEach((relay) => {
    const tile = document.querySelector(`[data-relay="${relay.relay_name}"]`);

    if (tile) {
      updateTile(tile, relay.enabled);
    }
  });
}

async function setRelayState(relayName, enabled) {
  const { error } = await supabaseClient
    .from('relay_state')
    .upsert({
      relay_name: relayName,
      enabled,
    });

  if (error) {
    console.error(error);
  }
}

relayTiles.forEach((tile) => {
  tile.addEventListener('click', async () => {
    const enabled = !tile.classList.contains('is-on');

    updateTile(tile, enabled);

    await setRelayState(tile.dataset.relay, enabled);

    statusText.textContent = `${tile.dataset.relay} set to ${enabled ? 'ON' : 'OFF'}`;
  });
});

allOffButton.addEventListener('click', async () => {
  for (const tile of relayTiles) {
    updateTile(tile, false);
    await setRelayState(tile.dataset.relay, false);
  }

  statusText.textContent = 'All relays are OFF';
});

supabaseClient
  .channel('relay-sync')
  .on(
    'postgres_changes',
    {
      event: '*',
      schema: 'public',
      table: 'relay_state',
    },
    (payload) => {
      const relay = payload.new;

      if (!relay) {
        return;
      }

      const tile = document.querySelector(`[data-relay="${relay.relay_name}"]`);

      if (tile) {
        updateTile(tile, relay.enabled);
      }
    }
  )
  .subscribe();

loadRelayState();
