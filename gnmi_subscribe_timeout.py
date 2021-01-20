import pprint
import yaml
import queue
import time
import kthread

from pygnmi.client import gNMIclient, telemetryParser


if __name__ == '__main__':

    def gnmi_subscriber_gen(msg_queue, _iterator ):
        while True:
            msg_queue.put(next(_iterator))

    def get_messages(msg_queue):  # consumer
        # while True:
        try:
            return msg_queue.get(timeout=receiver_timeout)
        except queue.Empty:
            return None

    host = ('192.168.56.31',50051)

    sample_interval = 5
    receiver_timeout = 3

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
        msg_queue = queue.Queue()
        gnmi_subscriber_gen_thread = kthread.KThread(
            target=gnmi_subscriber_gen,
            args=(msg_queue, telemetry_subscribe_gen))
        gnmi_subscriber_gen_thread.start()
        while True:
            _msg = get_messages(msg_queue)
            if _msg == None:
                gnmi_subscriber_gen_thread.terminate()
                gc.close()
                raise Exception("gnmi receiver timeout")
                break
            else:
                print(
                    yaml.dump(telemetryParser(_msg),default_flow_style=False))
        gnmi_subscriber_gen_thread.join()
