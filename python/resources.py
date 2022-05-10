QUERIES = {
    'tweets': """
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
    """,

    'retweet': """
SELECT 
    tweet_id, 
    username,
    tweet_text,
    retweet_id
FROM
    Tweet
        JOIN
    User USING(user_id)
WHERE
    tweet_id = {}
;
    """,

    'new_tweet': """
INSERT INTO Tweet(user_id, tweet_time, tweet_text, retweet_id) VALUES ({user_id}, "{tweet_time}", "{text}", {retweet});
"""
}

HTML_TEMPLATES = {
    'base': """
<html>
    <head>
        <title>{title}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" type="text/css" href="/web.css" />
    </head>
    <body>
        <h1>Риттер</h1>
        <div class="main-wrapper">
        {content}
        </div>
    </body>
</html>
    """,

    'feed_content': """
        <aside>
            <h3>Привет, {username}!</h3>
            <p><a href="{link_new_tweet}">Новый твит</a></p>
            <p><a href="{link_feed}">Лента</a></p>    
            <p><a href="{link_logout}">Выйти</a></p>
        </aside>
        <div id="content">
            {tweets}
        </div>
    </div>
    """,

    'tweet': """
    <div class="tweet">
        <h3>{username}</h3>
        <h4>{date}</h4>
        <p>{text}</p>
        {retweets}
        <a href="{link_new_tweet}/{id}">Ретвитнуть</a>
    </div>
    """,

    'retweets': """
    <details>
        <summary>Ретвиты ({number})</summary>
        {retweets}
    </details>
    """,

    'retweet': """
    <div class="retweet">
                <h3>{username}</h3>
                <h4>{date}</h4>
                <p>{text}</p>
    </div>
    """,

    'login': """
<div>
    {error}
    <form class="login" method="post" , enctype="multipart/form-data" action="#" >
        <label for="username">Логин:</label>
        <input type="text" id="username" name="username" maxlength="100" required/>
        <label for="password">Пароль:</label>
        <input type="password" id="password" name="password" maxlength="100" required/>
        <input type="submit" value="Войти"/>
    </form>
</div>
    """,

    'login_error': """
    <h2 class="error">{}</h2>
    """,

    'not_found': """
    <h2>404: Страница не найдена</h2>
    """,

    'new_tweet': """
    <div class="new-tweet">
        <h2>{header}</h2>
        {retweet}
        <form method="post" , enctype="multipart/form-data" class="new-tweet" action="#">
            <label for="tweet">Введите твит (до 140 символов):</label>
            <textarea maxlength="140" name="tweet" id="tweet" placeholder="Введите твит..." required></textarea>
            <input type="submit" value="Отправить твит">
        </form>
    </div>
""",

    'retweet_form': """
        <div class="retweet-form">
            <h4>{username}</h4>
            <p>{text}</p>
        </div>
    """
}


