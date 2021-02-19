import multiprocessing
import os
import shutil
import time
from typing import Union

import mido

from .utils import ExternalProcess, get_smf_duration, progressbar, Popen


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

    def synthesize_midi_file(self,
                             midifile: Union[mido.MidiFile, str],
                             sync=True,
                             progress=True) -> multiprocessing.Process:
        """
        Send midi messages contained in `filename` to `self.port`

        `midifile` can be a `mido.MifiFile` object or a string

        `self.port` is initialized during in the constructor of this object but
        if no Carla instance is found it is automatically updated when
        enetering this method. You can force an update with `self._update_port`
        method.

        If `sync` is set to False, a new sub-process is dispached and this
        function returns suddenly.  The `multiprocessing.Process` object is
        returned and you can wait for that process to terminate (e.g. by
        calling its `join` method). You can also wait by calling the `wait`
        method of this object.

        If `sync` is True, a new process is dispatched, but it is waited in
        before returning.

        If `progress` is True, a bar is printed showing the progress of the
        synthesis. If `sync` is False, `progress` is not used.
        """
        if not hasattr(self, 'port'):
            self._update_port()

        if type(midifile) is str:
            midifile = mido.MidiFile(midifile)

        def play():
            with mido.open_output(self.port, autoreset=True) as outport:
                for i, msg in enumerate(midifile.play()):
                    outport.send(msg)

        self.process = multiprocessing.Process(target=play)
        self.process.start()

        if sync:
            _wait_dur(midifile.length, progress)  # type: ignore
            self.wait()

        return self.process

    def wait(self):
        """
        Wait for this object has finished sending midi events
        """
        if not hasattr(self, 'process'):
            return
        self.process.join()


class ExternalMIDIPlayer(ExternalProcess):

    MIDI_PORT = 'Carla:events-in'

    def __init__(self):
        super().__init__()
        self._tempname = 'tmp.mid'

        # check dependencies
        if shutil.which('jack-smf-player') is None:
            raise RuntimeError(
                "Dependencies not satisfied, install jack-smf-player in your\
PATH")

    def _start_player(self, filename):
        self.process = Popen(
            ['jack-smf-player', '-q', '-a', self.MIDI_PORT, filename])
        return self.process

    def synthesize_midi_note(self,
                             pitch: int,
                             velocity: int,
                             duration: float,
                             sustain: int = 0,
                             soft: int = 0,
                             sostenuto: int = 0,
                             channel: int = 0,
                             program: int = 0):
        """
        Send midi messages representing the note to `MIDI_PORT` and waits for
        it

        The `Popen` object is in `self.process`.
        """
        self.process.wait()
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        # program
        track.append(
            mido.Message('program_change', program=program, channel=channel))
        # sustain
        track.append(
            mido.Message('control_change',
                         control=64,
                         time=0,
                         value=sustain,
                         channel=channel))
        # sostenuto
        track.append(
            mido.Message('control_change',
                         control=66,
                         time=0,
                         value=sostenuto,
                         channel=channel))
        # soft
        track.append(
            mido.Message('control_change',
                         control=67,
                         time=0,
                         value=soft,
                         channel=channel))
        # note on
        track.append(
            mido.Message('note_on',
                         velocity=velocity,
                         time=0,
                         note=pitch,
                         channel=channel))
        # note off
        track.append(
            mido.Message('note_off',
                         note=pitch,
                         time=duration,
                         channel=channel))
        mid.save(self._tempname)
        self._duration = duration
        self._start_player(self._tempname)
        self.wait()

    def synthesize_midi_file(self,
                             midifile: Union[mido.MidiFile, str],
                             sync=True,
                             progress=True) -> multiprocessing.Process:
        """
        Send midi messages contained in `filename` to `self.port`

        `midifile` can be a `mido.MifiFile` object or a string

        `self.port` is initialized during in the constructor of this object but
        if no Carla instance is found it is automatically updated when
        entering this method. You can force an update with `self._update_port`
        method.

        If `sync` is set to False, a new sub-process is dispached and this
        function returns suddenly.  The `multiprocessing.Process` object is
        returned and you can wait for that process to terminate (e.g. by
        calling its `join` method). You can also wait by calling the `wait`
        method of this object.

        If `sync` is True, a new process is dispatched, but it is waited in
        before returning.

        If `progress` is True, a bar is printed showing the progress of the
        synthesis. If `sync` is False, `progress` is not used.
        """
        self.process.wait()
        if type(midifile) is mido.MidiFile:
            self._duration = midifile.length  # type: ignore
            midifile.save(self._tempname)  # type: ignore
            midifile = self._tempname
        else:
            self._duration = get_smf_duration(midifile)
        self._start_player(midifile)

        if sync:
            _wait_dur(self._duration, progress)
            self.kill()
        return self.process

    def close(self):
        """
        Remove temporary files created by this instance
        """
        if os.path.exists(self._tempname):
            os.remove(self._tempname)


def _wait_dur(dur, progress):
    q = 0.005
    i = 0.0
    while i < dur:
        if progress:
            progressbar(i, 1, dur, status='Synthesis')
        time.sleep(q)
        i += q
    if progress:
        progressbar(dur, 1, dur, status='Completed!')
