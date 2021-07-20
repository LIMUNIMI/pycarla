import subprocess
import sys
import time

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
            if not self.process.is_running():
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
