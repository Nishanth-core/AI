create table refresh_tokens (

    id uuid primary key
        default gen_random_uuid(),

    user_id uuid not null
        references users(id)
        on delete cascade,

    token text not null,

    expires_at timestamptz not null,

    revoked boolean
        default false,

    created_at timestamptz
        default now()
);
