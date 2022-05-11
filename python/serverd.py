import sys, os
import server
from settings import env

try:
        pid = os.fork()
        if pid > 0:
                # exit first parent
                sys.exit(0)
except OSError as e:
        sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

# decouple from parent environment
os.chdir("/home/vova/ritter")
os.setsid()
os.umask(0)

# do second fork
try:
        pid = os.fork()
        if pid > 0:
                # exit from second parent
                sys.exit(0)
except OSError as e:
        sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

# redirect standard file descriptors
sys.stdout.flush()
sys.stderr.flush()
si = open('/dev/null', 'r')
so = open(env['LOG_FORLDER'] + '/output', 'a+')
se = open(env['LOG_FORLDER'] + '/errors', 'a+')
os.dup2(si.fileno(), sys.stdin.fileno())
os.dup2(so.fileno(), sys.stdout.fileno())
os.dup2(se.fileno(), sys.stderr.fileno())

server.run(handler_class=server.HttpGetHandler)