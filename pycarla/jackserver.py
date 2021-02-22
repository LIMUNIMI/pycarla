from typing import List
import shutil
import time

import jack

from .utils import ExternalProcess, Popen


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
        if self.process.poll() is not None:
            self.process = Popen(['jackd'] + self.options)
            self.freewheel = False
        self.connect()

    def connect(self):
        if not hasattr(self, 'client'):
            for i in range(10):
                try:
                    self.client = jack.Client('pycarla')
                except Exception:
                    time.sleep(1)
            if not hasattr(self, 'client'):
                raise RuntimeWarning("Cannot connect to Jack server!")

    def restart(self):
        """
        Wait for the duration of this `ExternalProcess`, then kill and restart.
        If the duration is not set, it doesn't return
        """
        self.wait()
        self.start()

    def get_ports(self) -> List[str]:
        return [port.name for port in self.client.get_ports()]

    def toggle_freewheel(self):
        self.client.set_freewheel(not self.freewheel)
        self.freewheel = not self.freewheel

    def kill(self):
        self.client.close()
        super().kill()
