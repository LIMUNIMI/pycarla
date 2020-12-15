#!/usr/bin/env python3
import fnmatch
import multiprocessing
import os
import signal
import subprocess
import sys
import threading
import time

import mido
import soundfile as sf

import jack
import sounddevice as sd

mido.set_backend('mido.backends.rtmidi/UNIX_JACK')

THISDIR = os.path.dirname(os.path.realpath(__file__))

if sys.platform == 'linux':
    # use our carla version
    CARLA_PATH = os.path.join(THISDIR, "carla") + "/"
else:
    # use the system version
    CARLA_PATH = ""


def Popen(command, **args):
    return subprocess.Popen(command,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            **args)


class ExternalProcess:
    def __init__(self):
        self.process = threading.Event()  # just something with a wait method
        self.process.set()
        self._start = time.time()
        self._duration = 0

    def kill(self):
        self.process.terminate()

    def wait(self):
        """
        Child objects should set `self._start` and `self._duration` so that
        `self.wait` works as expected.
        """
        sleep = self._duration - (time.time() - self._start)
        if sleep > 0:
            time.sleep(sleep)
        self.kill()


class JackServer(ExternalProcess):
    def __init__(self, options):
        """
        Creates a jack server with given options.

        Args
        ----
        `options` : list[str]
            list of options to be passed to Popen
        """
        super().__init__()
        self.options = options

    def start(self):
        """
        Starts the server
        """
        self.process = Popen(['jackd'] + self.options)

    def restart(self):
        """
        Kill and restarts
        """
        self.wait()
        self.start()


class Carla(ExternalProcess):
    def __init__(self,
                 proj_path: str,
                 server: JackServer,
                 min_wait: float = 0,
                 nogui: bool = True):
        """
        Creates a Carla object, ready to be started.

        `min_wait` is the minimum amount of seconds waited when starting Carla

        `nogui` is False if you want to use the gui
        """
        super().__init__()
        # create Jack client to query Jack
        self.proj_path = proj_path
        self.server = server
        self.min_wait = min_wait
        if nogui:
            self.nogui = "-n"
        else:
            self.nogui = ""

    def restart_carla(self):
        """
        Only restarts Carla, not the Jack server!
        """
        self.kill()
        self.start()

    def restart(self):
        """
        Restarts both the server and Carla!
        """
        print("Restarting Carla")
        self.server.restart()
        self.restart_carla()

    def start(self):
        """
        Start carla and Jack and wait `self.min_wait` seconds after a new port
        is created and ready in Jack. At least one new port must be created
        because this returns.
        """
        self.server.start()
        self.client = jack.Client('temporary')
        ports_before = self.client.get_ports()

        if self.proj_path:
            proj_path = os.path.abspath(self.proj_path)
        else:
            proj_path = ""

        # starting Carla
        self.process = subprocess.Popen(
            [CARLA_PATH + "Carla", self.nogui, proj_path],
            preexec_fn=os.setsid)

        # waiting
        ports_after = self.client.get_ports()
        start = time.time()
        CHANGED = False
        while True:
            if len(ports_before) != len(ports_after):
                start = time.time()
                CHANGED = True
                ports_before = ports_after
            if time.time() - start >= self.min_wait and CHANGED:
                break
            if time.time() - start >= 20:
                self.restart()
            time.sleep(0.025)
            ports_after = self.client.get_ports()

    def kill_carla(self):
        self.client.close()
        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

    def kill(self):
        self.server.wait()
        self.kill_carla()

    def exists(self, ports=["Carla:events-in", "Carla:audio*"]):
        """
        simply checks if the Carla process is running and ports are available

        `ports` is a list of string name representing Jack ports; you can use
            '*', '?' etc.

        Returns
        ---
        bool: True if all ports in `ports` exist and the Carla process is
            running, false otherwise
        """
        real_ports = [port.name for port in self.client.get_ports()]
        for port in ports:
            if not fnmatch.filter(real_ports, port):
                return False

        if self.process.poll():
            return False

        return True


class AudioRecorder():
    AUDIO_PORT = 'carla'

    def __init__(self, channels=None, samplerate=None, dtype='float32'):
        """
        Records output from a Carla instance.

        For now, only one Carla instance should be active.

        Uses ``sounddevice`` module, refer to it for more info about
        parameters.

        If `channels` and `samplerate` are not used, the maximum value usable
        for Carla is used (samplerate is usually set by jack server...)
        """
        # make newer jack and carla instances visible to sounddevice and jack:
        sd._exit_handler()
        sd._initialize()

        self.channels = channels
        self.samplerate = samplerate

        # get default values and params
        devicelist = sd.query_devices()
        for device in devicelist:
            if self.AUDIO_PORT in device['name'].lower():
                if not channels:
                    self.channels = device['max_output_channels']
                if not samplerate:
                    self.samplerate = device['default_samplerate']

        sd.default.device = self.AUDIO_PORT
        self.dtype = dtype
        super().__init__()

    def start(self, duration):
        """
        Record audio for ``duration`` seconds. Note that this function returns
        suddenly; call ``wait()`` for wating the end of the recording.
        """
        self.recorded = sd.rec((int(duration * self.samplerate)),
                               channels=self.channels,
                               samplerate=self.samplerate,
                               dtype=self.dtype)

    def rec(self, *args, **kwargs):
        """
        Records and waits for the end of the recording
        """
        self.start(*args, **kwargs)
        self.wait()

    def wait(self):
        sd.wait()

    def save_recorded(self, filename):
        """
        Save the recorded array to file. Extensions supported by ``libsndfile``!
        """

        if not hasattr(self, 'recorded'):
            raise RuntimeError("No recorded array!")

        sf.write(filename, self.recorded, int(self.samplerate))


class MIDIPlayer():

    MIDI_PORT = 'carla'

    def __init__(self):
        """
        Creates a player which is able to connect to a Carla instance

        For now, only one Carla instance should be active.
        """
        super().__init__()
        self._update_port()

    def _update_port(self):
        for port in mido.get_output_names():
            if self.MIDI_PORT in port.lower():
                self.port = port
                break

    def send_message(self, message: mido.Message, reset: bool = False):
        """
        0. If not yet done, look a for a Carla instance
        1. Open a Jack port
        2. Send a message to the Carla instance
        3. Reset control changes is `reset` is True
        4. Close the port
        """
        if not hasattr(self, 'port'):
            self._update_port()

        with mido.open_output(self.port, autoreset=reset) as outport:
            outport.send(message)

    def synthesize_midi_note(self,
                             pitch: int,
                             velocity: int,
                             duration: float,
                             sustain: int = 0,
                             soft: int = 0,
                             sostenuto: int = 0,
                             channel: int = 0,
                             program: int = 0,
                             reset: bool = False):
        """
        0. If not yet done, look a for a Carla instance
        1. Open a Jack port
        2. Send note_on, note_off, and control changes according to parameters
           to the Carla instance
        3. Reset control changes is `reset` is True
        4. Close the port

        Note: Mido numbers channels 0 to 15 instead of 1 to 16. This makes them
        easier to work with in Python but you may want to add and subtract 1
        when communicating with the user.
        """
        if not hasattr(self, 'port'):
            self._update_port()

        with mido.open_output(self.port, autoreset=reset) as outport:
            # program
            outport.send(
                mido.Message('program_change',
                             program=program,
                             channel=channel))
            # sustain
            outport.send(
                mido.Message('control_change',
                             control=64,
                             value=sustain,
                             channel=channel))
            # sostenuto
            outport.send(
                mido.Message('control_change',
                             control=66,
                             value=sostenuto,
                             channel=channel))
            # soft
            outport.send(
                mido.Message('control_change',
                             control=67,
                             value=soft,
                             channel=channel))
            # note on
            outport.send(
                mido.Message('note_on',
                             velocity=velocity,
                             note=pitch,
                             channel=channel))
            time.sleep(duration)
            # note off
            outport.send(mido.Message('note_off', note=pitch, channel=channel))

    def synthesize_midi_file(self, midifile, sync=True):
        """
        Send midi messages contained in `filename` to `self.port`

        `midifile` can be a `mido.MifiFile` object or a string

        `self.port` is initialized during in the constructor of this object but
        if no Carla instance is found it is automatically updated when
        enetering this method. You can force an update with `self._update_port`
        method.

        If `sync` is set to False, a new sub-process is dspached and this
        function returns suddenly.  The `multiprocessing.Process` object is
        returned and you can wait for that process to terminate (e.g. by
        calling its `join` method). You can also wait by calling the `wait`
        method of this object.
        """
        if not hasattr(self, 'port'):
            self._update_port()

        if type(midifile) is str:
            midifile = mido.MidiFile(midifile)

        def play():
            with mido.open_output(self.port, autoreset=True) as outport:
                for msg in midifile.play():
                    outport.send(msg)

        if sync:
            play()
        else:
            self.process = multiprocessing.Process(target=play)
            self.process.start()
            return self.process

    def wait(self):
        """
        Wait for this object has finished sending midi events
        """
        if not hasattr(self, 'process'):
            return
        self.process.join()


def get_smf_duration(filename):
    """
    Return note dration of a file from a path
    """
    return mido.MidiFile(filename).length
