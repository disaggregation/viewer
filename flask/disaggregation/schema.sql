drop table if exists user;
create table user (
  user_id integer primary key autoincrement,
  username text not null,
  email text not null,
  pw_hash text not null
);

drop table if exists follower;
create table follower (
  who_id integer,
  whom_id integer
);

drop table if exists message;
create table message (
  message_id integer primary key autoincrement,
  author_id integer not null,
  text text not null,
  pub_date integer
);

drop table if exists devices;
create table devices (
  device_id integer primary key autoincrement,
  author_id integer not null,
  name text not null,
  type text not null,
  confirm_datetime timestamp,
  power integer,
  energy integer,
  first_datetime timestamp,
  last_datetime timestamp
);

drop table if exists disaggregated_loads;
create table disaggregated_loads (
  loads_id integer primary key autoincrement,
  device_id integer,
  power integer,
  energy integer,
  first_seen_datetime timestamp,
  last_seen_datetime timestamp
);


