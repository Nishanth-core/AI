create table password_reset_otps (

    id uuid primary key
        default gen_random_uuid(),

    email text not null,

    otp text not null,

    expires_at timestamptz not null,

    verified boolean default false,

    created_at timestamptz
        default now()
);
