import threading
import Queue




class Producer(threading.Thread):
    def __init__(self, in_queue, out_queue):
        threading.Thread.__init__(self)
        self.in_queue = in_queue
        self.out_queue = out_queue

    def run(self):
        while True:
            item = self.in_queue.get()
            print('here is your item: %s\n' % item)

            result = item + 1
            self.out_queue.put(result)

            self.in_queue.task_done()


class Consumer(threading.Thread):

    def __init__(self, out_queue):
        threading.Thread.__init__(self)
        self.out_queue = out_queue

    def run(self):
        while True:
            item = self.out_queue.get()

            result = 'This is your awesome output. %s\n' % item
            print(result)

            self.out_queue.task_done()

if __name__ == '__main__':
    in_queue = Queue.Queue()
    out_queue = Queue.Queue()

    for i in xrange(len(item_list)):
       t = Producer(in_queue, out_queue)
       t.daemon = True
       t.start()

    for item in item_list:
        in_queue.put(item)

    for i in xrange(len(item_list)):
        t = Consumer(out_queue)
        t.daemon = True
        t.start()

    in_queue.join()
    out_queue.join()