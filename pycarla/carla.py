from typing import List
import argparse
import fnmatch
import os
import platform
import random
import shutil
import signal
import sys
import tarfile
import time
import urllib.request

import jack
import mido

import psutil
from .jackserver import JackServer
from .generics import ExternalProcess, FakeProcess
from .utils import progressbar, kill_psutil_process

version = "2.1"


def download():

    if sys.platform == 'linux':
        # download carla
        print("Downloading...")
        arch = platform.architecture()[0][:2]
        target_url =\
            'https://github.com/falkTX/Carla/releases/download/v' + \
            version + '/Carla_' + version + '-linux' +\
            arch + '.tar.xz'
        try:
            fname, header = urllib.request.urlretrieve(target_url,
                                                       reporthook=progressbar)
        except Exception as e:
            print("Error while downloading Carla!", file=sys.stderr)
            print(e, file=sys.stderr)
        progressbar(10, 1, 10, status='Completed!')
        print("\n")

        print("Extracting archive...")
        rand = str(random.randint(10**4, 10**5))
        tmp_path = "/tmp/carla" + "-" + rand
        with tarfile.open(fname, "r:xz") as file:
            file.extractall(tmp_path)

        shutil.move(tmp_path + "/Carla_" + version + "-linux" + arch,
                    CARLA_PATH)
    else:
        print(
            "Your OS is against the freedom of software developers because its\
sources are closed. I don't support closed software. You can still download\
Carla by yourself and put the `Carla` command in your path.")


def run_carla():
    carla = Carla("", ['-R', '-d', 'alsa'], min_wait=0, nogui=False)
    carla.start()
    carla.process.wait()
    try:
        carla.kill()
    except Exception:
        print("Processes already closed!")


mido.set_backend('mido.backends.rtmidi/UNIX_JACK')

THISDIR = os.path.dirname(os.path.realpath(__file__))

if sys.platform == 'linux':
    # use our carla version
    CARLA_PATH = os.path.join(THISDIR, "carla") + "/"
    # from pathlib import Path
    # CARLA_PATH = Path(THISDIR) / "source" / "frontend" / "carla"
else:
    # use the system version
    CARLA_PATH = ""


class Carla(ExternalProcess):
    def __init__(self,
                 proj_path: str,
                 server_options: List[str] = [],
                 min_wait: float = 0,
                 nogui: bool = True):
        """
        Creates a Carla object, ready to be started.

        * `server_options` are the the options that will be used to start
        `jackd`; the format is similar to `subprocess.Popen` -- e.g. ``['-d',
        'alsa', '-r', '48000']

        * `min_wait` is the minimum amount of seconds waited when starting
        Carla; it is useful if your preset takes a bit to be loaded.

        * `nogui` is False if you want to use the gui
        """
        super().__init__()

        self.proj_path = proj_path
        self.server = JackServer(server_options)
        self.min_wait = min_wait
        if nogui:
            self.nogui = "-n"
        else:
            self.nogui = ""

        self.error = False

        if sys.platform == 'linux':
            if not os.path.exists(CARLA_PATH):
                raise Warning("Carla seems not to be installed. Run \
``python -m pycarla.carla -d`` to install it!")
        else:
            if not shutil.which('carla'):
                raise Warning(
                    "Carla seems not to be installed. Download it and put the \
``Carla`` command in your path.")

    def restart_carla(self):
        """
        Only restarts Carla, not the Jack server!
        """
        self.kill_carla()
        self.start()

    def restart(self):
        """
        Restarts both the server and Carla!
        """
        print("Restarting Carla")
        self.kill_carla()
        self.server.kill()
        self.start()

    def __make_carla_popen(self, proj_path):
        self.process = psutil.Popen(
            [CARLA_PATH + "Carla", self.nogui, proj_path],
            preexec_fn=os.setsid)

    def get_ports(self):
        return [port.name for port in self.client.get_ports()]

    def start(self):
        """
        Start carla and Jack and wait `self.min_wait` seconds after a Carla
        instance is ready.
        """
        self.server.start()

        if self.proj_path:
            proj_path = os.path.abspath(self.proj_path)
        else:
            proj_path = ""

        # starting Carla
        self.__make_carla_popen(proj_path)

        self.client = jack.Client("pycarla")

        # a simple callback that restart carla if
        # carla disconnects
        @self.client.set_process_callback
        def carla_process(frames):
            if (self.client.last_frame_time // frames) % 8 == 0:
                if not self.exists():
                    print("Carla doesn't exists anymore, restarting it")
                    self.restart_carla()
                    self.error = True

        # waiting until Carla is ready
        start = time.time()
        READY = self.exists()
        while True:
            if not READY and self.exists():
                start = time.time()
                READY = True
            if time.time() - start >= self.min_wait and READY:
                break
            if time.time() - start >= 20:
                self.kill_carla(sign=signal.SIGKILL)
                self.server.restart()
                self.__make_carla_popen()
                start = time.time()
            time.sleep(0.1)

        # activate AFTER having started the Carla process
        self.client.activate()

    def kill_carla(self):
        """
        kill carla, but not the server
        """
        self.client.deactivate()
        self.client.close()
        del self.client
        kill_psutil_process(self.process)

    def kill(self):
        """
        kill carla and wait for the server
        """
        for i in range(10):
            self.kill_carla()
            if not self.exists():
                break
            time.sleep(0.5)
        self.server.kill()

    def exists(self, ports=["Carla:events*", "Carla:audio*"]):
        """
        simply checks if the Carla process is running and ports are available

        `ports` is a list of string name representing Jack ports; you can use
            '*', '?' etc.

        Returns
        ---
        bool: True if all ports in `ports` exist and the Carla process is
            running, false otherwise
        """
        try:
            real_ports = self.get_ports()
        except Exception:
            return False

        for port in ports:
            if not fnmatch.filter(real_ports, port):
                return False

        if not self.process.is_running():
            return False

        if self.process.status() == 'zombie':
            print("Warning! Carla is Zombie!")
            del self.process
            self.process = FakeProcess()
            return False

        return True

    def wait_exists(self):
        """
        Waits until a Carla instance is ready in Jack
        """
        while not self.exists():
            time.sleep(0.5)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description="Manage the Carla instance verion")
    argparser.add_argument(
        "-d",
        "--download",
        action="store_true",
        help=
        "Download the correct Carla version in the installation directory of\
    this python package.")

    argparser.add_argument(
        "-r",
        "--run",
        action="store_true",
        help="Run the Carla instance previously downloaded.")

    args = argparser.parse_args()
    if args.download and args.run:
        print("Please, provide one option at a time!")
    else:
        if args.download:
            download()
        elif args.run:
            run_carla()
        else:
            argparser.print_help()
