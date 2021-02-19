import shutil
import time

from .utils import Popen, ExternalProcess


class JackServer(ExternalProcess):
    def __init__(self, options):
        """
        Creates a jack server with given options.

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
            self._start = time.time()

    def restart(self):
        """
        Wait for the duration of this `ExternalProcess`, then kill and restart.
        """
        self.wait()
        self.start()

