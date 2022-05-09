SELECT 
    t1.tweet_id,
    t1.user_id,
    t3.username,
    t1.tweet_time,
    t1.tweet_text,
    t2.user_id,
    t4.username,
    t2.tweet_time,
    t2.tweet_text
FROM
    Tweet AS t1 
        LEFT JOIN
    Tweet AS t2 ON t1.tweet_id = t2.retweet_id
        JOIN 
    User AS t3 ON t1.user_id = t3.user_id
        LEFT JOIN
    User AS t4 ON t2.user_id = t4.user_id
WHERE
    t1.retweet_id IS NULL
ORDER BY 
    t1.tweet_time DESC, t2.tweet_time;