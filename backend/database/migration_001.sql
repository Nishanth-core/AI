create extension if not exists "pgcrypto";

create table users (
    id uuid primary key
        default gen_random_uuid(),

    email text unique not null,

    name text not null,

    avatar_url text,

    password_hash text not null,

    created_at timestamptz
        default now(),

    updated_at timestamptz
        default now()
);
