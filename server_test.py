#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""Serv Bench

  Very basic test server to try some stuff.

"""

import sys
import socket
import time
import argparse
import threading

try:
  import gevent
  from gevent import socket as gsocket
except ImportError:
  print >> sys.stderr, "WARNING: `gevent` not found."


RESPONSE = 'HTTP/1.0 200 Ok\n\nHello world!'
SLEEP = 1


def get_sock(host='127.0.0.1', port=8080, max_connections=5, use_gev=False):
  """Return server socket."""
  if use_gev:
    serv = gsocket.socket()
  else:
    serv = socket.socket()
  serv.bind((host, port))
  serv.listen(max_connections)
  return serv

def serv_socket(serv):
  """Serve using plain sockets and dispatch to function"""
  while True:
    client, addr = serv.accept()
    handle_request(client, time.sleep)

def serv_threads(serv):
  """Serve with plain sockets, dispatch to thread"""
  while True:
    client, addr = serv.accept()
    t = threading.Thread(target=handle_request, args=(client, time.sleep))
    t.daemon = True
    t.start()

def serv_greenlet(serv):
  """Serve with gevents socket, dispatch to greenlet"""
  while True:
    client, addr = serv.accept()
    gevent.spawn(handle_request, client, gevent.sleep)

def handle_request(client, sleepfunc, time=1):
  """Send *RESPONSE* to *client* sopcket."""
  global RESPONSE, SLEEP
  try:
    client.recv(1024)
    sleepfunc(SLEEP)  # simulate proccessing logic
    client.send(RESPONSE)
    client.shutdown(socket.SHUT_WR)
    print '.',
  except Exception:
    print 'e',
  finally:
    sys.stdout.flush()
    client.close()


METHODS = {
  'socket': serv_socket,
  'threads': serv_threads,
  'gevent': serv_greenlet
}


if __name__ == '__main__':
  # get options
  ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[1],
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
  )
  ap.add_argument('-i', '--host', default='127.0.0.1', help='host')
  ap.add_argument('-p', '--port', type=int, default=8080, help='port')
  ap.add_argument('-m', '--max-connections', type=int, default=5,
    help='max concurrent connections'
  )
  ap.add_argument('-s', '--sleep', type=float, default=0.25,
    help='sleeptime for each request'
  )
  ap.add_argument('-r', '--response', default=RESPONSE, help='response')
  ap.add_argument('server', choices=METHODS.keys(), type=str, help='set server method')
  opt = ap.parse_args()
  # set global options (for `handle_request`)
  RESPONSE = opt.response
  SLEEP = opt.sleep
  # run server
  serv = get_sock(opt.host, opt.port, opt.max_connections, opt.server == 'gevent')
  try:
    METHODS[opt.server](serv) # start serving with given method
  except KeyboardInterrupt:
    pass
  finally:
    serv.close()