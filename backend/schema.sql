CREATE DATABASE IF NOT EXISTS cs179g;
USE cs179g;

CREATE TABLE IF NOT EXISTS hourly_crimes (
    hour INT,
    crime_count BIGINT,
    PRIMARY KEY (hour)
);

CREATE TABLE IF NOT EXISTS time_period_crimes (
    time_period VARCHAR(20),
    total_crimes BIGINT,
    PRIMARY KEY (time_period)
);

CREATE TABLE IF NOT EXISTS monthly_crimes (
    month INT,
    total_crimes BIGINT,
    PRIMARY KEY (month)
);

CREATE TABLE IF NOT EXISTS season_crimes (
    season VARCHAR(20),
    total_crimes BIGINT,
    PRIMARY KEY (season)
);

CREATE TABLE IF NOT EXISTS holidays (
    holiday_date DATE,
    holiday_name VARCHAR(100),
    PRIMARY KEY (holiday_date)
);

CREATE TABLE IF NOT EXISTS holiday_vs_nonholiday (
    day_type VARCHAR(20),
    total_crimes BIGINT,
    PRIMARY KEY (day_type)
);

CREATE TABLE IF NOT EXISTS christmas_by_type (
    primary_type VARCHAR(100),
    total BIGINT,
    PRIMARY KEY (primary_type)
);

CREATE TABLE IF NOT EXISTS halloween_by_type (
    primary_type VARCHAR(100),
    total BIGINT,
    PRIMARY KEY (primary_type)
);

CREATE TABLE IF NOT EXISTS thanksgiving_by_type (
    primary_type VARCHAR(100),
    total BIGINT,
    PRIMARY KEY (primary_type)
);

CREATE TABLE IF NOT EXISTS great_recession_by_type (
    primary_type VARCHAR(100),
    total BIGINT,
    PRIMARY KEY (primary_type)
);

CREATE TABLE IF NOT EXISTS yearly_crimes (
    year INT,
    total_crimes BIGINT,
    PRIMARY KEY (year)
);

CREATE TABLE IF NOT EXISTS crimes_by_location (
    location_description VARCHAR(255),
    total_crimes BIGINT,
    PRIMARY KEY (location_description)
);

CREATE TABLE IF NOT EXISTS crimes_by_location_and_type (
    location_description VARCHAR(255),
    primary_type VARCHAR(100),
    total BIGINT,
    PRIMARY KEY (location_description, primary_type)
);

CREATE TABLE IF NOT EXISTS community_area_crimes (
    community_area VARCHAR(50),
    total_crimes BIGINT,
    PRIMARY KEY (community_area)
);
CREATE TABLE IF NOT EXISTS sport_location_crimes_by_type (
    location_description VARCHAR(255),
    primary_type VARCHAR(100),
    total_crimes BIGINT,
    PRIMARY KEY (location_description, primary_type)
);
CREATE TABLE IF NOT EXISTS theft_by_location (
    location_description VARCHAR(255) NOT NULL,
    total_thefts BIGINT,
    total_crimes BIGINT,
    PRIMARY KEY (location_description)
);

CREATE TABLE IF NOT EXISTS downtown_vs_residential_theft_robbery (
    area_type VARCHAR(20),
    tr_crimes BIGINT,
    total_crimes BIGINT,
    rate DOUBLE,
    PRIMARY KEY (area_type)
);

CREATE TABLE IF NOT EXISTS transit_vs_commercial_robbery_count (
    location_type VARCHAR(20),
    robbery_count BIGINT,
    PRIMARY KEY (location_type)
);


CREATE TABLE IF NOT EXISTS airport_theft_count_comparison (
    location_type VARCHAR(20),
    theft_count BIGINT,
    total_crimes BIGINT,
    theft_rate DOUBLE,
    PRIMARY KEY (location_type)
);

CREATE TABLE IF NOT EXISTS christmas_vs_nonchristmas_by_type (
    day_type VARCHAR(20),
    primary_type VARCHAR(100),
    total BIGINT,
    PRIMARY KEY (day_type, primary_type)
);

CREATE TABLE IF NOT EXISTS halloween_vs_nonhalloween_by_type (
    day_type VARCHAR(20),        
    primary_type VARCHAR(100),  
    total BIGINT,        
    PRIMARY KEY (day_type, primary_type)
);
