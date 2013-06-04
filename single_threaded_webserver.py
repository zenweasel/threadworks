import os
import sys
import socket
import re

import threading
import Queue
import time

from wsgi.header import Headers


def run_with_cgi(application):

    environ = dict(os.environ.items())
    environ['wsgi.input']        = sys.stdin
    environ['wsgi.errors']       = sys.stderr
    environ['wsgi.version']      = (1, 0)
    environ['wsgi.multithread']  = True
    environ['wsgi.multiprocess'] = False
    environ['wsgi.run_once']     = True

    if environ.get('HTTPS', 'off') in ('on', '1'):
        environ['wsgi.url_scheme'] = 'https'
    else:
        environ['wsgi.url_scheme'] = 'http'

    headers_set = []
    headers_sent = []

    def write(data):
        if not headers_set:
             raise AssertionError("write() before start_response()")

        elif not headers_sent:
             # Before the first output, send the stored headers
             status, response_headers = headers_sent[:] = headers_set
             sys.stdout.write('Status: %s\r\n' % status)
             for header in response_headers:
                 sys.stdout.write('%s: %s\r\n' % header)
             sys.stdout.write('\r\n')

        sys.stdout.write(data)
        sys.stdout.flush()

    def start_response(status, response_headers, exc_info=None):
        if exc_info:
            try:
                if headers_sent:
                    # Re-raise original exception if headers sent
                    raise exc_info[0], exc_info[1], exc_info[2]
            finally:
                exc_info = None     # avoid dangling circular ref
        elif headers_set:
            raise AssertionError("Headers already set!")

        headers_set[:] = [status, response_headers]
        return write

    result = application(environ, start_response)
    try:
        for data in result:
            if data:    # don't send headers until body appears
                write(data)
        if not headers_sent:
            write('')   # send headers now if body was empty
    finally:
        if hasattr(result, 'close'):
            result.close()


class Producer(threading.Thread):
    def __init__(self, in_queue, out_queue):
        threading.Thread.__init__(self)
        self.in_queue = in_queue
        self.out_queue = out_queue

    def run(self):
        while True:
            item = self.in_queue.get()
            print('here is your item: %s\n' % vars(item))
            self.out_queue.put(item)
            self.in_queue.task_done()


class Consumer(threading.Thread):

    def __init__(self, out_queue, server):
        threading.Thread.__init__(self)
        self.out_queue = out_queue
        self.server = server

    def run(self):
        while True:
            item = self.out_queue.get()
            self.server.handle_response(item)
            self.out_queue.task_done()

class Request(object):
    pass

def wsgi_application(environ, start_response):
    """Simplest possible application object"""
    status = '200 OK'
    response_headers = [('Content-type', 'text/html')]
    start_response(status, response_headers)
    page = ['<html><head><head><body><h1>Hello World</h1></body></html>']
    return page

class QueueConsumerServer(object):

    def __init__(self, addr='127.0.0.1', port=8080)
        self.iq = Queue.Queue()
        self.oq = Queue.Queue()
        self.port = port
        self.socket = socket.socket()
        self.socket.bind((addr, self.port))
        environ = dict(os.environ.items())
        environ['wsgi.input']        = sys.socket
        environ['wsgi.errors']       = sys.stderr
        environ['wsgi.version']      = (1, 0)
        environ['wsgi.multithread']  = True
        environ['wsgi.multiprocess'] = False
        environ['wsgi.run_once']     = True

        if environ.get('HTTPS', 'off') in ('on', '1'):
            environ['wsgi.url_scheme'] = 'https'
        else:
            environ['wsgi.url_scheme'] = 'http'

        headers_set = []
        headers_sent = []


    def run(self):
        self.socket.listen(1)
        while True:
            cli, addr = self.socket.accept()
            self.handle_request(cli, addr)

    def handle_response(self, item):

            item.cli.send('''HTTP/1.0 200 Ok

        Hello world''')
            item.cli.shutdown(socket.SHUT_WR)

    def handle_request(self, cli, addr):
        print('handle request')


        data = cli.recv(1024)

        print('receive data')
        request_line = (data).splitlines()[0]
        request_data = request_line.split(' ')


        req = Request()
        req.method = request_data[0]
        req.path = request_data[1]
        req.cli = cli

        self.iq.put(req)
        print('request placed in queue')
        return
        # except Exception, ex:
        #     print 'e', ex,
        #     sys.exit(1)
        # finally:
        #     sys.stdout.flush()
        #     self.socket.close()

if __name__ == '__main__':


    server = QueueConsumerServer(in_queue, out_queue, 8080)

    for i in xrange(3):
       t = Producer(in_queue, out_queue)
       t.daemon = True
       t.start()

    for i in xrange(3):
        t = Consumer(out_queue, server)
        t.daemon = True
        t.start()
    server.run()
    #in_queue.join()
    #out_queue.join()


    

