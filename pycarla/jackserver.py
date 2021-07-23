import shutil
import time

import jack

from .generics import ExternalProcess
from .utils import Popen, find_procs_by_name, kill_psutil_process


class JackServer(ExternalProcess):
    def __init__(self, options):
        """
        Starts a jack server with given options and create a dummy client named
        `pycarla` to query and interact with it

        Args
        ----
        `options` : list[str]
            list of options to be passed to Popen
        """
        super().__init__(options)
        self.options = options
        if not shutil.which('jackd'):
            raise Warning(
                "Jack seems not to be installed. Install it and put the \
``jackd`` command in your path.")

    def start(self):
        """
        Starts the server if not already started
        """
        try:
            self.process = find_procs_by_name('jackd')[0]
        except (IndexError, jack.JackOpenError) as e:
            print("Jack server is not running, starting it!")
            if not self.process.is_running():
                self.process = Popen(['jackd'] + self.options)
            else:
                raise e
            time.sleep(1)

    def restart(self):
        """
        Wait for the duration of this `ExternalProcess`, then kill and restart.
        If the duration is not set, it doesn't return
        """
        self.wait()
        self.start()

    def kill(self):
        kill_psutil_process(self.process)
        super().kill()
