import datetime
from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
from http import cookies
import mysql.connector
import hashlib 
import uuid
import cgi
import re
from settings import DB_CONFIG, COOKIEJAR_PATH, PORT, PASSWORD_SALT
from resources import HTML_TEMPLATES, QUERIES


STATIC_URLS = [
    '/web.css'
]

URLS = {
    'link_logout': '/logout',
    'link_login': '/login',
    'link_new_tweet': '/new',
    'link_feed': '/feed'
}


def hash_password(open_password):
    return hashlib.sha512((open_password + PASSWORD_SALT).encode()).hexdigest()

def new_user(username, open_password):
    return "INSERT INTO User(username, password_hash) VALUES ({}, '{}')".format(
        username,
        hash_password(open_password)
    )

def print_tweet(data):
    if len(data) == 0:
        return ""
    retweets = [
        HTML_TEMPLATES['retweet'].format(
            username = x[6],
            date = x[7],
            text = x[8]
        )
        for x in data
        if x[5] != None
    ]
    retweets_text = HTML_TEMPLATES['retweets'].format(
        number = len(retweets),
        retweets = '\n'.join(retweets)
    ) if len(retweets) > 0 else ""
    return HTML_TEMPLATES['tweet'].format(
        id = data[0][0],
        username = data[0][2],
        date = data[0][3],
        text = data[0][4],
        retweets = retweets_text,
        **URLS
    )


db_cursor = None
db_connection = None

try:
    with open(COOKIEJAR_PATH, encoding='utf-8') as fin: 
        users_cookie = eval(fin.read())
except FileNotFoundError:
    users_cookie = {}


class HttpGetHandler(BaseHTTPRequestHandler):
    """Обработчик с реализованным методом do_GET."""

    def send_404(self):
        self.send_response(404)
        self.end_headers()
        self.wfile.write(HTML_TEMPLATES['base'].format(
            title="Страница не найдена",
            content=HTML_TEMPLATES['not_found']
        ).encode())

    @staticmethod
    def parse_new_tweet_url(url):
        m = re.match(URLS['link_new_tweet'] + r'((/(\d+))?|/)$', url)
        if m:
            result = None 
            if m.group(3):
                db_cursor.execute(QUERIES['retweet'].format(m.group(3)))
                try:
                    result = next(db_cursor)
                except StopIteration:
                    raise ValueError("Invalid URL")
            return result
        raise ValueError("Invalid URL")
                

    def do_POST(self):
        ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
        pdict['boundary'] = bytes(pdict['boundary'], 'utf-8')
        fields = cgi.parse_multipart(self.rfile, pdict)
        print(fields)
        if self.path == URLS['link_login']:
            username = fields.get("username")[0].replace("'", "")
            open_password = fields.get("password")[0]
            hashed_password = hash_password(open_password)
            db_cursor.execute("SELECT user_id, username, password_hash FROM User WHERE username = '{}';".format(username))
            try:
                user_id, username, actual = next(db_cursor)
                if actual != hashed_password:
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(HTML_TEMPLATES['base'].format(
                        title = "Ошибка авторизации",
                        content = HTML_TEMPLATES['login'].format(
                            **URLS,
                            error=HTML_TEMPLATES['login_error'].format("Неверный пароль")
                        ),
                    ).encode())
                    return 
                c = cookies.SimpleCookie(self.headers['Cookie'])
                try:
                    users_cookie[c['session'].value] = (user_id, username)
                    session = c['session'].value
                except KeyError:
                    session = str(uuid.uuid4())
                    users_cookie[session] = (user_id, username)
                self.send_response(200)
                self.send_header('Set-Cookie', 'session={}'.format(session))
                # self.wfile.write(c.output().encode())
                self.end_headers()
                self.wfile.write(
                    '<html><head><meta http-equiv="refresh" content="0; URL={link_feed}" /></head></html>'.format(**URLS).encode()
                )
            except StopIteration:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(HTML_TEMPLATES['base'].format(
                    title = "Ошибка авторизации",
                    content = HTML_TEMPLATES['login'].format(
                        **URLS,
                        error=HTML_TEMPLATES['login_error'].format("Такой пользователь не зарегистрирован")
                    ),
                ).encode())
                return 
        elif self.path.startswith(URLS['link_new_tweet']):
            c = cookies.SimpleCookie(self.headers['Cookie'])
            try:
                user_id, _ = users_cookie[c['session'].value]
            except KeyError:
                self.send_error(401, "Unauthorized")
                return
            try:
                retweet = self.parse_new_tweet_url(self.path)
                new_tweet = fields.get('tweet')[0].replace('"', "'")
                db_cursor.execute(QUERIES['new_tweet'].format(
                    user_id=user_id, 
                    tweet_time=datetime.datetime.today(),
                    text=new_tweet,
                    retweet="NULL" if not retweet else retweet[3] if retweet[3] else retweet[0]
                ))
                db_connection.commit()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(
                    '<html><head><meta http-equiv="refresh" content="0; URL={link_feed}" /></head></html>'.format(**URLS).encode()
                )
            except ValueError:
                self.send_404()

    def do_GET(self):
        if self.path in STATIC_URLS:
            self.send_response(200)
            self.end_headers()
            with open('static' + self.path, encoding='utf-8') as fin:
                self.wfile.write(fin.read().encode())
            return
        c = cookies.SimpleCookie(self.headers['Cookie'])
        try:
            user_id, username = users_cookie[c['session'].value]
        except KeyError:
            if self.path != URLS['link_login']:
                self.send_response(307)
                self.send_header('Location', URLS['link_login'])
                self.end_headers()
                return 
        if self.path == URLS['link_feed']:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            db_cursor.execute(QUERIES['tweets'])
            prev_id = None 
            retweets = []
            content = ""
            for x in db_cursor:
                if prev_id != x[0]:
                    content += print_tweet(retweets)
                    retweets = [x]
                    prev_id = x[0]
                else:
                    retweets.append(x)
            content += print_tweet(retweets)
            result = HTML_TEMPLATES['base'].format(
                title = "Риттер",
                content = HTML_TEMPLATES['feed_content'].format(
                    username=username,
                    tweets = content,
                    **URLS
                )
            )
            self.wfile.write(result.encode())
        elif self.path.startswith(URLS['link_new_tweet']):
            try:
                retweet = self.parse_new_tweet_url(self.path)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(
                    HTML_TEMPLATES['base'].format(
                        title="Новый твит",
                        content=HTML_TEMPLATES['feed_content'].format(
                            username=username,
                            tweets=HTML_TEMPLATES['new_tweet'].format(
                                header="Ретвит" if retweet else "Новый твит",
                                retweet=HTML_TEMPLATES['retweet_form'].format(
                                    username=retweet[1],
                                    text=retweet[2]
                                ) if retweet else ""
                            ),
                            **URLS
                        )
                    ).encode()
                )
            except ValueError:
                self.send_404()
        elif self.path == URLS['link_login']:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(HTML_TEMPLATES['base'].format(
                title = "Авторизуйтесь",
                content = HTML_TEMPLATES['login'].format(error="", **URLS),
            ).encode())
        elif self.path == URLS['link_logout']:
            del users_cookie[c['session'].value]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(HTML_TEMPLATES['base'].format(
                title = "Вы вышли",
                content = '<div><h2>Вы вышли</h2><a href="{link_login}">Зайти заново</a></div>'.format(**URLS)
            ).encode())
        elif self.path == '/':
            self.send_response(307)
            self.send_header('Location', '/feed')
            self.end_headers()
        else:
            self.send_404()


def run(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
    server_address = ('', PORT)
    httpd = server_class(server_address, handler_class)
    global db_cursor, db_connection
    try:  
        db_connection = mysql.connector.connect(**DB_CONFIG)
        db_cursor = db_connection.cursor()
        httpd.serve_forever()
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    except KeyboardInterrupt:
        httpd.server_close()
        db_connection.close()
        with open(COOKIEJAR_PATH, mode='w', encoding='utf-8') as fout:
            print(users_cookie, file=fout)


if __name__ == '__main__':
    # print(hashlib.sha512("Hello".encode()).hexdigest())
    # print(hash_password("Вован"))
    # print(hash_password("Риточка"))
    run(handler_class=HttpGetHandler)
