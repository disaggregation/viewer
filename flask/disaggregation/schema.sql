drop table if exists user;
create table user (
  user_id integer primary key autoincrement,
  username text not null,
  email text not null,
  pw_hash text not null
);

-- NOT USED: follower can be changed to people following devices (alerting or something like that).
drop table if exists follower;
create table follower (
  who_id integer,
  whom_id integer
);

-- NOT USED:  messages can used for system messages, alert the user of specific events.
drop table if exists message;
create table message (
  message_id integer primary key autoincrement,
  author_id integer not null,
  text text not null,
  pub_date integer
);

-- what know devices can be suggested to the user
drop table if exists device_types;
create table device_types (
  device_type_id integer primary key autoincrement,
  title text not null,
  name text not null,
  image_url text);
INSERT INTO `device_types` VALUES (1,'coffe_machine','Coffe machine','https://portal.plugwise.net/3/img/devices/coffee_maker.png');
INSERT INTO `device_types` VALUES (2,'computer_desktop','Desktop','https://portal.plugwise.net/3/img/devices/computer_desktop.png');
INSERT INTO `device_types` VALUES (3,'computer_laptop','Laptop','https://portal.plugwise.net/3/img/devices/computer_desktop.png');
INSERT INTO `device_types` VALUES (4,'freezer','Freezer','https://portal.plugwise.net/3/img/devices/freezer.png');
INSERT INTO `device_types` VALUES (5,'Heater','Heater','');
INSERT INTO `device_types` VALUES (6,'Oven','Oven','https://portal.plugwise.net/3/img/devices/computer_desktop.png');
INSERT INTO `device_types` VALUES (7,'Router','Router','https://portal.plugwise.net/3/img/devices/computer_desktop.png');
INSERT INTO `device_types` VALUES (8,'Television','Television','https://portal.plugwise.net/3/img/devices/tv.png');
INSERT INTO `device_types` VALUES (9,'washshing_machine','Washshing Machine','https://portal.plugwise.net/3/img/devices/washingmachine.png');
INSERT INTO `device_types` VALUES (10,'water_cooker','Water Cooker','https://portal.plugwise.net/3/img/devices/watercooker.png');
-- https://portal.plugwise.net/3/img/devices/water_bed.png
-- https://portal.plugwise.net/3/img/devices/oven_microwave.png
-- https://portal.plugwise.net/3/img/devices/heater_central.png	
-- https://portal.plugwise.net/3/img/devices/hometheater.png
-- https://portal.plugwise.net/3/img/devices/pump_heater.png
-- https://portal.plugwise.net/3/img/devices/vcr.png
-- https://portal.plugwise.net/3/img/devices/dryer.png


-- found and registered devices (loads) which can be confirmed by the user.
drop table if exists devices;
create table devices (
  device_id integer primary key autoincrement,
  name text not null,
  type text,
  power integer,
  energy integer,
  first_datetime timestamp,
  last_datetime timestamp,
  author_id integer, -- confirm_author_id?
  confirm_datetime timestamp
);

-- log of disaggregation loads (used)
drop table if exists disaggregated_loads;
create table disaggregated_loads (
  loads_id integer primary key autoincrement,
  device_id integer,
  power integer,
  energy integer,
  start_datetime timestamp,
  end_datetime timestamp,
  profile text
);


