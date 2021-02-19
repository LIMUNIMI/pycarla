import shutil

from .utils import ExternalProcess, Popen


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

    def restart(self):
        """
        Wait for the duration of this `ExternalProcess`, then kill and restart.
        If the duration is not set, it doesn't return
        """
        self.wait()
        self.start()
