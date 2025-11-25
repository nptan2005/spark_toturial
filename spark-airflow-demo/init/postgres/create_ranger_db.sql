-- Create Ranger DB + user
CREATE USER rangeradmin WITH PASSWORD 'rangeradmin123';
CREATE DATABASE ranger OWNER rangeradmin;
GRANT ALL PRIVILEGES ON DATABASE ranger TO rangeradmin;

-- Create Atlas DB + user
CREATE USER atlas WITH PASSWORD 'atlas123';
CREATE DATABASE atlas OWNER atlas;
GRANT ALL PRIVILEGES ON DATABASE atlas TO atlas;