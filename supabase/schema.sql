create extension if not exists "pgcrypto";

create table if not exists players (
  id uuid primary key default gen_random_uuid(), first_name text not null, last_name text not null,
  jersey_number integer not null check (jersey_number between 0 and 99), photo_path text,
  position text default 'Attaquant', active boolean not null default true, created_at timestamptz not null default now()
);
create table if not exists rules (
  id uuid primary key default gen_random_uuid(), label_fr text not null, label_hu text not null,
  amount numeric(8,2) not null check (amount >= 0), active boolean not null default true, created_at timestamptz not null default now()
);
create table if not exists fines (
  id uuid primary key default gen_random_uuid(), player_id uuid not null references players(id) on delete cascade,
  rule_id uuid references rules(id) on delete set null, custom_reason text, base_amount numeric(8,2) not null check (base_amount >= 0),
  final_amount numeric(8,2) not null check (final_amount >= 0), match_day boolean not null default false,
  status text not null default 'pending' check (status in ('pending','paid','appeal','cancelled')),
  fine_date date not null default current_date, comment text, created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table if not exists payments (
  id uuid primary key default gen_random_uuid(), player_id uuid not null references players(id) on delete cascade,
  amount numeric(8,2) not null check (amount > 0), payment_date date not null default current_date,
  method text not null check (method in ('Wero','Espèces','Virement','Autre')), comment text, created_at timestamptz not null default now()
);
create index if not exists fines_player_date_idx on fines(player_id, fine_date);
create index if not exists payments_player_date_idx on payments(player_id, payment_date);

create or replace function set_updated_at() returns trigger language plpgsql as $$ begin new.updated_at=now(); return new; end $$;
drop trigger if exists fines_updated_at on fines;
create trigger fines_updated_at before update on fines for each row execute function set_updated_at();

alter table players enable row level security;
alter table rules enable row level security;
alter table fines enable row level security;
alter table payments enable row level security;
create policy "public read players" on players for select using (true);
create policy "public read rules" on rules for select using (true);
create policy "public read fines" on fines for select using (true);
create policy "public read payments" on payments for select using (true);
-- Les écritures passent par la service_role côté serveur Streamlit. Ne jamais exposer cette clé au navigateur.
