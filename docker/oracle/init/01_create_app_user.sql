ALTER SESSION SET CONTAINER = XEPDB1;

-- Create a database user specifically for the WebApp.
CREATE USER FATE_APP IDENTIFIED BY fate_app_password;

-- Grant access to the database.
GRANT CONNECT TO FATE_APP;

-- Grant permission to create common database objects.
GRANT CREATE SESSION TO FATE_APP;
GRANT CREATE TABLE TO FATE_APP;
GRANT CREATE SEQUENCE TO FATE_APP;
GRANT CREATE VIEW TO FATE_APP;

-- Grant the user tablespace permissions to prevent the "insufficient tablespace permissions" error when creating tables.
GRANT UNLIMITED TABLESPACE TO FATE_APP;

EXIT;