import pprint
import yaml
import queue
import time
import kthread

from pygnmi.client import gNMIclient, telemetryParser

class nonblocking_iterator:
    def __init__(self, blocking_generator, timeout, stop_if_timeout = False):
        self.timeout = timeout
        self.stop_if_timeout = stop_if_timeout
        self.msg_queue = queue.Queue()
        self.blocking_generator = blocking_generator
        self._thread = kthread.KThread(
            target=self._put_messages_from_blocking_generator_to_queue)
        self._thread.start()

    def _put_messages_from_blocking_generator_to_queue(self):
        while True:
            self.msg_queue.put(next(self.blocking_generator))

    def terminate(self):
        self._thread.terminate()
        while self._thread.is_alive():
            self._thread.join()
        time.sleep(1)

    def is_alive(self):
        return self._thread.is_alive()

    def join(self):
        self._thread.join()

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return self.msg_queue.get(timeout=self.timeout)
        except queue.Empty:
            self._thread.terminate()
            while self._thread.is_alive():
                self._thread.join()
            time.sleep(1)
            raise Exception("timeout error")

    def next(self):
        return self.__next__()

if __name__ == '__main__':

    host = ('192.168.56.31',50051)

    sample_interval = 5
    recv_timeout = 3

    subscribe = {
                'subscription': [
                {
                    'path': 'interfaces/interface[name=Management1]/state/counters',
                    'mode': 'sample',
                    'sample_interval': sample_interval * 1000000000
                }
                    ],
                    'use_aliases': False,
                    'mode': 'stream',
                    'encoding': 'json'
                }

    gc = gNMIclient(
        target=host, username='admin', password='admin1', insecure=True)

    try:
        gc.__enter__()
        connect = True
    except:
        connect = False

    if connect:
        print ("#1#"*30)
        pygnmi_generator = gc.subscribe(subscribe=subscribe)
        print ("#1#"*30)
        _iter = nonblocking_iterator(pygnmi_generator, 3)
        print (f"_iter : {_iter}")
        try:
            while True:
                _msg = _iter.next()
                if _msg:
                    print(
                        yaml.dump(telemetryParser(
                            _msg),default_flow_style=False))
        except Exception as exc:
            print (f"got exception: {exc}")


        print ("#2#"*30)
        pygnmi_generator = gc.subscribe(subscribe=subscribe)
        print ("#2#"*30)
        _iter = nonblocking_iterator(pygnmi_generator, 7)
        print (f"_iter : {_iter}")
        try:
            i = 0
            while True:
                i += 1
                print (f"gnmi iteration {i}")
                _msg = _iter.next()
                if _msg == None:
                    print ("gnmi receiver timeout")
                    collecting = False
                else:
                    _parsed = telemetryParser(_msg)
                    print (f"parsed: {_parsed}")
                if i >= 10:
                    #_iter.terminate()
                    # _iter.join()
                    break
            _iter.terminate()
        except Exception as exc:
            print (f"!!! got exception: {exc}")

        print ("#3#"*30)
        pygnmi_generator = gc.subscribe(subscribe=subscribe)
        print ("#3#"*30)
        _iter = nonblocking_iterator(pygnmi_generator, 3)
        print (f"_iter : {_iter}")
        try:
            i = 0
            while True:
                i += 1
                print (f"gnmi iteration {i}")
                _msg = _iter.next()
                if _msg == None:
                    print ("gnmi receiver timeout")
                    collecting = False
                else:
                    _parsed = telemetryParser(_msg)
                    print (f"parsed: {_parsed}")
                    _synced = _parsed.get("sync_response",False)
                    if _synced == True:
                        print ("gnmi receiver synced")
                        print ("gnmi iterator terminated")
                        break
                if i >= 10:
                    break
            _iter.terminate()
            # _iter.join()
        except Exception as exc:
            print (f"got exception: {exc}")

        print ("#4#"*30)
        pygnmi_generator = gc.subscribe(subscribe=subscribe)
        print ("#4#"*30)
        try:
            for i, _msg in enumerate(nonblocking_iterator(pygnmi_generator, 3)):
                    if _msg == None:
                        print ("gnmi receiver timeout")
                        collecting = False
                    else:
                        _parsed = telemetryParser(_msg)
                        print (f"parsed: {_parsed}")
        except Exception as exc:
            print (f"got exception: {exc}")
        print ("#5#"*30)
        # gc.close()
