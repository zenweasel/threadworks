import sys
import socket
import time
import threading
import gevent

def sequential(port):
    s = socket.socket()
    s.bind(('0.0.0.0', port))
    s.listen(500)
    while True:
        cli, addr = s.accept()
        handle_request(cli, time.sleep)

def threads(port):
    s = socket.socket()
    s.bind(('0.0.0.0', port))
    s.listen(500)
    while True:
        cli, addr = s.accept()
        t = threading.Thread(target=handle_request, args=(cli, time.sleep))
        t.daemon = True
        t.start()

def greenlet(port):
    from gevent import socket
    s = socket.socket()
    s.bind(('0.0.0.0', port))
    s.listen(500)
    while True:
        cli, addr = s.accept()
        gevent.spawn(handle_request, cli, gevent.sleep)

def handle_request(s, sleep):
    try:
        s.recv(1024)
        sleep(0.1)
        s.send('''HTTP/1.0 200 Ok

    Hello world''')
        s.shutdown(socket.SHUT_WR)
        print '.',
    except Exception, ex:
        print 'e', ex,
    finally:
        sys.stdout.flush()
        s.close()

if __name__ == '__main__':
    greenlet(int(sys.argv[1]))