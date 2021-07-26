import jack
import threading
import time
import psutil


class JackClient:
    def __init__(self, name):
        self.client = jack.Client(name)
        self.is_active = False
        self.ready_at = -1
        self.end_wait = threading.Event()
        self.error = False

        # a simple callback that ends the processing if
        # carla disconnects
        @self.client.set_client_registration_callback
        def client_unregister_callback(name, register):
            if 'carla' in name.lower() and not register:
                # this check works for both `pycarla` and `Carla-something`
                print("Carla disconnected: disconnecting " + self.client.name)
                self.end_wait.set()
                self.error = True

    def is_ready(self):
        """
        Check if the client is active,  if it is in condition of processing
        and, if the current cycle is successive to the one in which the client
        became in condition of processing.

        The latter condition is needed to guarantee to all the other clients
        that this function starts returning `True` in the same cycle --
        otherwise, clients that were processed before of this could see this
        client not ready, while clients processed after this see it as ready.
        """
        return self.ready_at < self.client.last_frame_time\
            and self.ready_at > 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        if isinstance(exc_type, Exception):
            print(exc_tb)

    def deactivate(self):
        """
        Deactivates the client and unregisters all input ports
        """
        if self.is_active:
            self.client.deactivate()
            self.client.inports.clear()
            self.client.outports.clear()
            self.client.midi_inports.clear()
            self.client.midi_outports.clear()
            self.is_active = False
            print(self.client.name + " deactivated!")

    def close(self):
        """
        Deactivate, close and clear memory from this client
        """
        self.deactivate()
        self.client.close()
        self.clear()

    def set_freewheel(self, onoff: bool):
        """
        Set freewheel on or off, without raising exceptions
        """
        try:
            self.client.set_freewheel(onoff)
        except jack.JackError:
            print(f"Cannot set freewheel to {onoff}")

    def clear(self):
        pass

    def activate(self):
        raise NotImplementedError("Abstract method")

    def wait(self, timeout=None, in_fw=False, out_fw=False):
        """
        Waits while setting freewheeling mode to `in_fw`
        It then always set freewheeling mode to `out_fw` before exiting. This
        object doesn't raise exceptions if freewheeling is already set.

        if `timeout` is a number, it waits but exits if `timeout` is reached
        and returns False in that case, otherwise, True
        """
        success = True
        if not self.end_wait.is_set():
            self.set_freewheel(in_fw)
            success = self.end_wait.wait(timeout)
        self.set_freewheel(out_fw)
        self.deactivate()
        return success and not self.error


class FakeProcess:
    """
    A class to create a fake process/popen for initializing
    `ExternalProcess`
    """
    def __init__(obj):
        pass

    def wait(obj):
        pass

    def is_running(obj):
        """
        from psutil.Process
        """
        return False

    def is_alive(obj):
        """
        from multiprocessing.Process
        """
        return False

    def status(obj):
        return 'dead'

    def children(obj, *args, **kwargs):
        return []

    def terminate(obj):
        pass

    def kill(obj):
        pass

    def start(obj):
        pass


class ExternalProcess:
    """
    A class for processes with a pre-defined duration
    """

    def __init__(self, *args):
        self.process = FakeProcess()
        self._duration = 0
        self.args = args

    def kill(self):
        """
        Just calls `self.process.kill()` and reset this object
        """
        for i in range(10):
            self.process.kill()
            if not self.process.is_running() or self.process.status(
            ) == 'zombie':
                self.__init__(*self.args)
                return
            time.sleep(0.5)

        raise Exception("Cannot kill a process:", self)

    def wait(self):
        """
        Wait the `self._duration` and then kill the process.
        """
        if self._duration > 0:
            timeout = None
        else:
            timeout = self._duration

        try:
            self.process.wait(timeout=timeout)
        except psutil.TimeoutExpired:
            self.kill()
