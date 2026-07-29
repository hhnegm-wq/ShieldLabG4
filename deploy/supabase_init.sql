-- ShieldLab G4 — Supabase bootstrap
--
-- Apply in the Supabase SQL editor after creating the project.
-- This creates a profile table, sync trigger, and RLS so tier/role metadata can
-- drive the hosted Streamlit UI auth surface without exposing write access to
-- other users' profile rows.

create extension if not exists pgcrypto;

create table if not exists public.user_profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    email text unique,
    full_name text,
    tier text not null default 'free' check (tier in ('free', 'pro')),
    role text not null default 'viewer' check (role in ('viewer', 'operator', 'admin')),
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

drop trigger if exists trg_user_profiles_updated_at on public.user_profiles;
create trigger trg_user_profiles_updated_at
before update on public.user_profiles
for each row execute procedure public.set_updated_at();

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.user_profiles (id, email, full_name, tier, role)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data ->> 'full_name', ''),
    coalesce(new.raw_user_meta_data ->> 'tier', 'free'),
    coalesce(new.raw_user_meta_data ->> 'role', 'viewer')
  )
  on conflict (id) do update set
    email = excluded.email,
    full_name = coalesce(nullif(excluded.full_name, ''), public.user_profiles.full_name),
    tier = excluded.tier,
    role = excluded.role,
    updated_at = timezone('utc', now());
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure public.handle_new_user();

alter table public.user_profiles enable row level security;

create policy "Users can view their own profile"
on public.user_profiles
for select
using (auth.uid() = id);

create policy "Users can update their own profile basics"
on public.user_profiles
for update
using (auth.uid() = id)
with check (auth.uid() = id);

revoke update on public.user_profiles from anon, authenticated;
grant update (full_name) on public.user_profiles to authenticated;

-- Seed an admin/operator manually after sign-up, e.g.:
-- update public.user_profiles
-- set role = 'admin', tier = 'pro'
-- where email = 'hhnegm@ju.edu.sa';
