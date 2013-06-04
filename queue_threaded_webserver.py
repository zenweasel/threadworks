import os
import sys
import socket
import re

import threading
import Queue
import time

from StringIO import StringIO
from wsgiref.util import FileWrapper
from wsgiref.headers import Headers


def get_url_path(path):
    from urllib import quote
    url = environ['wsgi.url_scheme']+'://'

    if environ.get('HTTP_HOST'):
        url += environ['HTTP_HOST']
    else:
        url += environ['SERVER_NAME']

        if environ['wsgi.url_scheme'] == 'https':
            if environ['SERVER_PORT'] != '443':
               url += ':' + environ['SERVER_PORT']
        else:
            if environ['SERVER_PORT'] != '80':
               url += ':' + environ['SERVER_PORT']

    url += quote(environ.get('SCRIPT_NAME', ''))
    url += quote(environ.get('PATH_INFO', ''))
    if environ.get('QUERY_STRING'):
        url += '?' + environ['QUERY_STRING']



def weasel_application(environ, start_response):
    """Simplest possible application object"""
    status = '200 OK'
    response_headers = [('Content-type', 'text/html')]
    start_response(status, response_headers)
    page = ['<html><head><head><body><h1>Hello World</h1></body></html>']
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
        return u'%s - %s - %s - %s' % (self.method, self.path, self.headers, self.cli)

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
        environ['wsgi.input']        = self.socket
        environ['wsgi.errors']       = sys.stderr
        environ['wsgi.version']      = (1, 0)
        environ['wsgi.multithread']  = True
        environ['wsgi.multiprocess'] = False
        environ['wsgi.run_once']     = True
        environ['REQUEST_METHOD']    = ""
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
        headers_set = []
        headers_sent = []
        for i in xrange(3):
            thr = Producer(self.iq, self.oq)
            thr.daemon = True
            thr.start()

        for i in xrange(3):
            thr = Consumer(self.oq, self)
            thr.daemon = True
            thr.start()

    def serve_forever(self):
        self.socket.listen(1)
        while True:
            cli, addr = self.socket.accept()
            self.handle_request(cli, addr)


    class ResponseHandler(object):

        def __init__(self, server, item):
            print(server.environ)
            self.item = item
            self.headers_set = False
            self.headers_sent = False
            self.results = server.application(server.environ, self)
            self.respond()


        def __call__(self, status, response_headers, exc_info=None):
            if not self.headers_sent:
                 # Before the first output, send the stored headers
                 #status, response_headers = headers_sent[:] = headers_set
                 self.item.cli.send('Status: %s\r\n' % status)
                 for header in response_headers:
                     self.item.cli.send('%s: %s\r\n' % header)
                 self.item.cli.send('\r\n')

        def respond(self):
            if hasattr(self, 'results'):
                for result in self.results:
                    self.item.cli.send(result)
                self.item.cli.shutdown(socket.SHUT_WR)
            else:
                print('huh?')


    def _parse_methods(self, header_line):
        url_data = header_line.split(' ')
        method = url_data[0].strip(' ')
        path = url_data[1].strip(' ')
        http_version = url_data[2].strip(' ')
        print(method, path, http_version)
        # if rdata[:3].lower() == 'get':
        #     self.environ['REQUEST_METHOD'] = "GET"
        # if rdata[:4].lower() == "post":
        #     self.environ['REQUEST_METHOD'] = "POST"



    def parse_request_data(self, data):
        
        request_lines = data.splitlines()
        for x, rdata in enumerate(request_lines):
            print('rdata %s: %s' % (x, rdata))
            for method in self.methods_allowed:
                if method in rdata[:5].lower():
                    self._parse_methods(rdata)
            if rdata[:4].lower() == 'host':
                if len(rdata[5:].split(':')) == 2:
                    host_port_split = rdata[5:].split(':')
                    self.environ['SERVER_NAME'] = host_port_split[0].strip(' ')
                    self.environ['SERVER_PORT'] = host_port_split[1].strip(' ')
                else:
                    self.environ['SERVER_NAME'] = rdata[5:].split(':')
        print(self.environ)

    def handle_request(self):
        self.socket.listen(1)
        try:
            while True:
                cli, addr = self.socket.accept()
                data = cli.recv(1024)
                request_data = self.parse_request_data(data)
                req.path = request_data[1]
                req.cli = cli
                self.iq.put(req)
                return
        except Exception, ex:
            print 'e', ex,
            sys.exit(1)
        finally:
            sys.stdout.flush()
            self.socket.close()

if __name__ == '__main__':
    httpd = make_my_server('', 8000, weasel_application)
    httpd.handle_request()



    

