import pprint
import yaml
import queue
import time
import kthread

from pygnmi.client import gNMIclient, telemetryParser

class gnmi_timeout_iterator:
    def __init__(self, gnmi_generator, timeout):
        self.timeout = timeout
        self.msg_queue = queue.Queue()
        self.gnmi_generator = gnmi_generator
        self._thread = kthread.KThread(
            target=self.iter_gen)
        self._thread.start()

    def iter_gen(self):
        print("gnmi_gen started")
        while True:
            self.msg_queue.put(next(self.gnmi_generator))

    def terminate(self):
        self._thread.terminate()

    def join(self):
        self._thread.join()

    def __iter__(self):
        return self

    def next(self):
        try:
            return self.msg_queue.get(timeout=self.timeout)
        except queue.Empty:
            return None

if __name__ == '__main__':

    # Aristas VM
    host = ('192.168.56.31',50051)

    sample_interval = 5
    receiver_timeout = 7

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
        telemetry_subscribe_gen = gc.subscribe(subscribe=subscribe)
        _iterator = gnmi_timeout_iterator(
            telemetry_subscribe_gen, receiver_timeout)

        while True:
            _msg = _iterator.next()
            if _msg == None:
                _iterator.terminate()
                gc.close()
                raise Exception("gnmi receiver timeout")
                break
            else:
                print(
                    yaml.dump(telemetryParser(_msg),default_flow_style=False))
        _iterator.join()
