CREATE DATABASE IF NOT EXISTS Ritter;
USE Ritter;

CREATE TABLE IF NOT EXISTS User (
    user_id INTEGER NOT NULL AUTO_INCREMENT,
    username CHAR(100) NOT NULL,
    password_hash CHAR(128) NOT NULL,
    PRIMARY KEY(user_id)
);

CREATE TABLE IF NOT EXISTS Tweet (
    tweet_id INTEGER NOT NULL AUTO_INCREMENT,
    user_id INTEGER NOT NULL,
    tweet_time DATETIME NOT NULL,
    tweet_text CHAR(140) NOT NULL,
    retweet_id INTEGER,
    FOREIGN KEY(user_id) REFERENCES User(user_id),
    FOREIGN KEY(retweet_id) REFERENCES Tweet(tweet_id),
    PRIMARY KEY(tweet_id)
);