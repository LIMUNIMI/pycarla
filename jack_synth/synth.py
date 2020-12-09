#!/usr/bin/env python3
import threading
import pretty_midi as pm
import subprocess
import soundfile as sf
import shutil
import os
import jack
import time
import signal
import fnmatch

MIDI_PORT = 'Carla:events-in'
AUDIO_PORT = 'Carla:audio-out*'


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


class MIDIRecorder(ExternalProcess):
    def __init__(self):
        super().__init__()
        self.filename = 'default_filename.mp3'
        if shutil.which('jack_capture') is None:
            raise RuntimeError(
                "Dependencies not satisfied, install jack_capture in your PATH"
            )

    def start(self, filename, duration, final_decay=4):
        """
        Record audio in output to `filename`.mp3 for `duration` seconds.
        """
        self.process.wait()
        self._duration = duration + final_decay
        self._start = time.time()
        self.filename = filename
        mp3 = '--mp3'
        if not filename.endswith('.mp3'):
            mp3 = ''
        self.process = subprocess.Popen([
            'jack_capture', mp3, '--absolutely-silent', '--filename', filename,
            '--port', AUDIO_PORT, '--recording-time',
            str(self._duration)
        ])

    def get_recorded(self):
        """
        Returns numpy data data and samplerate
        """
        if os.path.exists(self.filename):
            return sf.read(self.filename)
        else:
            raise Exception(self.filename + "does not exists!")

    def del_recorded(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)


class MIDIPlayer(ExternalProcess):
    def __init__(self):
        super().__init__()
        self._tempname = 'tmp.mid'

        # check dependencies
        if shutil.which('jack-smf-player') is None:
            raise RuntimeError(
                "Dependencies not satisfied, install jack-smf-player in your\
PATH")

    def _start_player(self, filename):
        self._start = time.time()
        self.process = subprocess.Popen(
            ['jack-smf-player', '-a', MIDI_PORT, filename])
        # ['jack-smf-player', '-q', '-a', MIDI_PORT, filename])

    def synthesize_midi_note(self,
                             pitch,
                             velocity,
                             duration,
                             sustain,
                             final_decay=4):
        """
        Send midi messages representing the note to `MIDI_PORT`

        The `Popen` object is in `self.synth`.
        """
        self.process.wait()
        mid = pm.PrettyMIDI()
        mid.instruments = [pm.Instrument(0)]
        mid.instruments[0].control_changes = [
            pm.ControlChange(64, int(sustain), 0)
        ]
        mid.instruments[0].notes = [
            pm.Note(int(velocity), int(pitch), 0, duration)
        ]
        mid.write(self._tempname)
        self._duration = duration + final_decay
        self._start_player(self._tempname)

    def synthesize_midi_file(self, filename, duration=0, final_decay=4):
        """
        Send midi messages contained in `filename` to `MIDI_PORT`

        The `Popen` object is in `self.synth`.
        """
        self.process.wait()
        if duration == 0:
            self._duration = get_smf_duration(filename) + final_decay
        else:
            self._duration = duration + final_decay
        self._start_player(filename)

    def close(self):
        """
        Remove temporary files created by this instance
        """
        if os.path.exists(self._tempname):
            os.remove(self._tempname)


def get_smf_duration(filename):
    """
    Return note dration of a file from a path
    """
    return max([
        note.end for instrument in pm.PrettyMIDI(filename).instruments
        for note in instrument.notes
    ])


class Carla(ExternalProcess):
    def __init__(self, proj_path, server, min_wait=0):
        """
        Creates a Carla object, ready to be started
        """
        super().__init__()
        # create Jack client to query Jack
        self.proj_path = proj_path
        self.server = server
        self.min_wait = min_wait
        if shutil.which('carla') is None:
            raise RuntimeError(
                "Dependencies not satisfied, install carla in your PATH"
            )

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
        self.server.restart()
        self.restart_carla()

    def start(self):
        """
        Start carla and Jack and wait `min_wait` seconds after a new port is
        created and ready in Jack. At least one new port must be created
        because this returns.
        """
        self.server.start()
        self.client = jack.Client('temporary')
        ports_before = self.client.get_ports()

        # starting Carla
        self.process = subprocess.Popen(
            ["carla", "-n",
             os.path.abspath(self.proj_path)],
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

    def exists(self, ports=[MIDI_PORT, AUDIO_PORT]):
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


