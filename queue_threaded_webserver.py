import os
import sys
import socket
import re

import threading
import Queue
import time
from pprint import pprint

from StringIO import StringIO
from wsgiref.util import FileWrapper
from wsgiref.headers import Headers


def weasel_application(environ, start_response):
    """Simplest possible application object"""
    print('Application Environ\n')
    print(environ)
    if environ.get('PATH_INFO') == '/lost':
        status = '404 Not Found'
    else:
        status = '200 OK'
    response_headers = [('Content-type', 'text/html')]
    start_response(status, response_headers)
    if status == '200 OK':
        page = ['<html><head>', '<head><body>', '<h1>Hello World</h1>', '</body></html>']
    else:
        page = ['<html><head>', '<head><body>', '<h1>404 Not Found</h1>', '</body></html>']
    return page


class Producer(threading.Thread):
    def __init__(self, in_queue, out_queue):
        threading.Thread.__init__(self)
        self.in_queue = in_queue
        self.out_queue = out_queue

    def run(self):
        while True:

            item = self.in_queue.get()
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
            self.server.ResponseHandler(self.server, item)
            self.out_queue.task_done()


class Request(object):
    
    def __init__(self):
        self.method = None
        self.path = None
        self.headers = None
        self.cli = None

    def __repr__(self):
        return u'%s - %s - %s' % (self.method, self.path, self.headers)


class Response(object):

    def __init__(self):
        self.headers = dict()
        self.status = None
        self.content = None


def make_my_server(host, port, application):
    qcs = QueueConsumerServer(host, port, application)
    return qcs


class QueueConsumerServer(object):

    methods_allowed = ['get', 'post', 'put', 'patch', 'delete', 'options', 'upgrade']

    def __init__(self, host, port, application):
        self.host = host
        self.port = port
        self.application = application
        self.iq = Queue.Queue()
        self.oq = Queue.Queue()

        self.socket = socket.socket()
        self.socket.bind((self.host, self.port))
        environ = dict()
        environ['wsgi.input'] = self.socket
        environ['wsgi.errors'] = sys.stderr
        environ['wsgi.version'] = (1, 0)
        environ['wsgi.multithread'] = True
        environ['wsgi.multiprocess'] = False
        environ['wsgi.run_once'] = True
        environ['REQUEST_METHOD'] = ""
        environ['SCRIPT_NAME'] = ""
        environ['PATH_INFO'] = ""
        environ['QUERY_STRING'] = ""
        environ['CONTENT_TYPE'] = ""
        environ['CONTENT_LENGTH'] = ""
        environ['SERVER_NAME'] = ""
        environ['SERVER_PORT'] = ""
        environ['SERVER_PROTOCOL'] = ""
        if environ.get('HTTPS', 'off') in ('on', '1'):
            environ['wsgi.url_scheme'] = 'https'
        else:
            environ['wsgi.url_scheme'] = 'http'
        self.environ = environ
        for i in xrange(3):
            thr = Producer(self.iq, self.oq)
            thr.daemon = True
            thr.start()

        for i in xrange(3):
            thr = Consumer(self.oq, self)
            thr.daemon = True
            thr.start()

    class ResponseHandler(object):

        def __init__(self, server, item):
            environ = server.environ
            environ['REQUEST_METHOD'] = item.method
            environ['SERVER_NAME'] = item.headers.get('SERVER_NAME')
            environ['PATH_INFO'] = item.path
            self.response = Response()
            self.item = item
            self.headers_set = False
            self.headers_sent = False
            self.results = server.application(environ, self)
            self.respond()

        def __call__(self, status, response_headers, exc_info=None):
            self.response.status = 'HTTP/1.1 %s' % status
            for header in response_headers:
                self.response.headers[header[0]] = header[1]

        def respond(self):
            if not self.headers_sent:
                print('sending headers')
                # Before the first output, send the stored headers
                self.headers_sent = True
                self.item.cli.send(self.response.status)
                self.item.cli.send('\r\n')
                for key, value in self.response.headers.items():
                    self.item.cli.send('%s: %s' % (key, value))
                    self.item.cli.send('\r\n')
                self.item.cli.send('\r\n')

            if hasattr(self, 'results'):

                for result in self.results:
                    print('sending results: %s' % result)
                    self.item.cli.send(result)
                    if hasattr(result, 'close'):
                        result.close()
                self.item.cli.shutdown(socket.SHUT_WR)
            else:
                print('huh?')

    def _parse_methods(self, header_line):
        url_data = header_line.split(' ')
        method = url_data[0].strip(' ')
        path = url_data[1].strip(' ')
        http_version = url_data[2].strip(' ')

        return method, path

    def parse_request_data(self, data, req):
        headers = dict()
        request_lines = data.splitlines()
        for x, rdata in enumerate(request_lines):
            print(rdata)
            header_key = rdata.split(':')
            if len(header_key) > 1:
                headers[header_key[0]] = header_key[1].strip(' ')
            for method in self.methods_allowed:
                if method in rdata[:5].lower():
                    req.method, req.path = self._parse_methods(rdata)
                    headers['REQUEST_METHOD'] = method.upper()
            if rdata[:4].lower() == 'host':
                if len(rdata[5:].split(':')) == 2:
                    host_port_split = rdata[5:].split(':')
                    headers['SERVER_NAME'] = host_port_split[0].strip(' ')
                    headers['SERVER_PORT'] = host_port_split[1].strip(' ')
                else:
                    headers['SERVER_NAME'] = rdata[5:].split(':')
        return headers

    def handle_request(self):
        self.socket.listen(1)
        try:
            while True:
                cli, addr = self.socket.accept()
                data = cli.recv(1024)
                req = Request()
                req.headers = self.parse_request_data(data, req)
                req.cli = cli
                req.environ = self.environ
                pprint(req)
                self.iq.put(req)

        except Exception, ex:
            print 'EXCEPTION', ex,
            sys.exit(1)
        finally:
            sys.stdout.flush()
            sys.stderr.flush()
            self.socket.close()

if __name__ == '__main__':
    httpd = make_my_server('', 8000, weasel_application)
    httpd.handle_request()



    

