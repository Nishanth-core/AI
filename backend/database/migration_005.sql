-- Add role column to users table
alter table users
add column role text default 'user';
