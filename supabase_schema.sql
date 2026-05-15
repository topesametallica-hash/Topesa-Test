create table if not exists public.relay_states (
  relay_id text primary key,
  name text not null,
  pin integer not null,
  is_on boolean not null default false,
  updated_at timestamptz not null default now()
);

alter table public.relay_states enable row level security;

drop policy if exists relay_states_public_select on public.relay_states;
drop policy if exists relay_states_public_insert on public.relay_states;
drop policy if exists relay_states_public_update on public.relay_states;

create policy relay_states_public_select
  on public.relay_states for select
  using (true);

create policy relay_states_public_insert
  on public.relay_states for insert
  with check (true);

create policy relay_states_public_update
  on public.relay_states for update
  using (true)
  with check (true);
