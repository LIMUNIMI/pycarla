from typing import List
import shutil
import time

import psutil
import jack

from .utils import ExternalProcess, Popen


def find_procs_by_name(name):
    """Return a list of processes matching 'name'."""
    ls = []
    for p in psutil.process_iter(["name", "exe", "cmdline"]):
        if name == p.info['name'] or \
                p.info['exe'] and os.path.basename(p.info['exe']) == name or \
                p.info['cmdline'] and p.info['cmdline'][0] == name:
            ls.append(p)
    return ls


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
            self.connect()
            self.process = find_procs_by_name('jackd')[0]
        except jack.JackOpenError:
            print("Jack server is not running, starting it!")
            if self.process.is_running():
                self.process = Popen(['jackd'] + self.options)
                self.freewheel = False
            time.sleep(1)
            self.connect()

    def connect(self):
        if not hasattr(self, 'client'):
            self.client = jack.Client('pycarla')
        if not hasattr(self, 'client'):
            print("Cannot connect to Jack server!")

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
