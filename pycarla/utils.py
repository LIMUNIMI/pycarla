import subprocess
import sys
import time
import os

import jack
import psutil
import mido


def get_smf_duration(filename):
    """
    Return note dration of a file from a path
    """
    return mido.MidiFile(filename).length


def progressbar(count, block_size, total, status='Download'):
    bar_len = 60
    count *= block_size
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()


def Popen(command, **args):
    """
    Custom call to ``psutil.Popen``
    """
    return psutil.Popen(command,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        **args)


def kill_psutil_process(process):
    """
    Kills a tree of `psutil.Process`
    """

    children = process.children(recursive=True)
    children.append(process)
    for p in children:
        try:
            p.kill()
        except psutil.NoSuchProcess:
            pass


def find_procs_by_name(name):
    """Return a list of processes matching 'name'."""
    ls = []
    for p in psutil.process_iter(["name", "exe", "cmdline"]):
        if name == p.info['name'] or \
                p.info['exe'] and os.path.basename(p.info['exe']) == name or \
                p.info['cmdline'] and p.info['cmdline'][0] == name:
            ls.append(p)
    return ls


class JackClient:
    def __init__(self, name):
        self.client = jack.Client(name)
        self.is_active = False
        self.ready_at = -1

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

    def wait(self, in_fw=False, out_fw=False):
        """
        waits while setting freewheeling mode to `in_fw`
        it then set freewheeling mode to `out_fw` before exiting
        """
        raise NotImplementedError("Abstract method")


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
        except subprocess.TimeoutExpired:
            self.kill()
