import threading

buff_lock = threading.Lock()
buff_list = []


class ThreadClass(threading.Thread):
    global buff_list

    def run(self):
        while True:
            if "C" == raw_input():
                with buff_lock:
                    buff_list.append("C")
                print buff_list


class ThreadClass2(threading.Thread):
    global buff_list

    def run(self):
        while True :
            if  "B" == raw_input() and len(buff_list) > 0:
                with buff_lock:
                    buff_list.pop()
                print buff_list

a = ThreadClass()
b = ThreadClass2()

a.start()
b.start()