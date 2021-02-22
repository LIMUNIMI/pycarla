import fnmatch
import multiprocessing
import os
import shutil
import threading
import time
from typing import Any, List, Union

import jack
import mido

from .utils import ExternalProcess, Popen, get_smf_duration, progressbar


class MIDIPlayer():

    MIDI_PORT = 'Carla:events-in*'

    def __init__(self, freewheel=False):
        """
        Creates a player which is able to connect to a Carla instance

        Optionally, `freewheel` cab be used to start freeewheel mode before of
        playing.

        For now, only one Carla instance should be active.
        """
        super().__init__()
        self.connected = False
        self.freewheel = freewheel
        self._is_freewheel = False

    def _setup(self):
        self.client = jack.Client('pycarla-midiplayer')
        self.port = self.client.midi_outports.register('output')
        if self._is_freewheel != self.freewheel:
            self.client.set_freewheel(self.freewheel)
            self._is_freewheel = self.freewheel

    def _update_port(self):
        real_ports = [port.name for port in self.client.get_ports()]
        for port in real_ports:
            if fnmatch.fnmatch(port, self.MIDI_PORT):
                if not self.connected or not self.port.is_connected_to(port):
                    try:
                        self.port.connect(port)
                    except Exception:
                        print("Cannot connect to Carla. Is the client active?")
                        self.connected = False
                    else:
                        self.connected = True

    def wait(self):
        if hasattr(self, 'process'):
            self.process.join()

    def synthesize_messages(self,
                            messages: List[mido.Message],
                            sync=False,
                            progress=False,
                            max_dur=1e15) -> multiprocessing.Process:
        """
        Synthesize a list of messages

        1. Create a jack client if not yet done
        2. Connect the port of this jack client to Carla if not yet done
        3. Send the list of messages to the Carla instance

        The process happens in a separate process saved in `self.process`

        If `sync` is True, this function waits until all messages have been
        processed, otherwise, it suddenly returns. You can wait by calling the
        `wait` method of this object.

        If `progress` is True, a bar is printed showing the progress of the
        synthesis. If `sync` is False, `progress` is not used.

        `max_dur` is the maximum time for after which messages are discarded

        This function is compatible with freewheeling mode.  Freewheel prevents
        jack from waiting between return calls. This allows for the maximum
        allowed speed, but not output/input operation is done with system audio
        (i.e. you cannot listen/recording to anything while in freewheeling
        mode)

        Note: Mido numbers channels 0 to 15 instead of 1 to 16. This makes them
        easier to work with in Python but you may want to add and subtract 1
        when communicating with the user.
        """
        self._messages = messages
        self.process = multiprocessing.Process(target=self._play)
        self.process.start()

        dur = min(max_dur, sum(msg.time for msg in messages))
        if sync:
            _wait_dur(dur, progress, condition=self.process.is_alive)
            self.process.terminate

        return self.process

    def _play(self):
        event = threading.Event()
        self._setup()

        global msg, offset
        it = iter(self._messages)
        msg = next(it)
        offset = 0

        @self.client.set_process_callback
        def process(frames):
            global offset, msg
            self.port.clear_buffer()
            while True:

                if offset >= frames:
                    # wait for the correct block
                    offset -= frames
                    return
                # Note: This may raise an exception:
                self.port.write_midi_event(offset, msg.bytes())

                try:
                    msg = next(it)
                except StopIteration:
                    event.set()
                    raise jack.CallbackExit
                offset += round(msg.time * fs)

        @self.client.set_samplerate_callback
        def samplerate(sr):
            global fs
            fs = sr

        with self.client:
            # cannot connect if it's not active and running the callback...
            self._update_port()
            event.wait()

    def synthesize_midi_note(self,
                             pitch: int,
                             velocity: int,
                             duration: float,
                             sustain: int = 0,
                             soft: int = 0,
                             sostenuto: int = 0,
                             channel: int = 0,
                             program: int = 0,
                             **kwargs) -> multiprocessing.Process:
        """
        set up a list of messages representing one note and then calls
        `self.synthesize_messages`. All keywords from that method can be used
        here.
        """
        messages = [
            # program change
            mido.Message('program_change',
                         program=program,
                         channel=channel,
                         time=0),
            # sustain
            mido.Message('control_change',
                         control=64,
                         value=sustain,
                         channel=channel,
                         time=0),
            # sostenuto
            mido.Message('control_change',
                         control=66,
                         value=sostenuto,
                         channel=channel,
                         time=0),
            # soft
            mido.Message('control_change',
                         control=67,
                         value=soft,
                         channel=channel,
                         time=0),
            # note on
            mido.Message('note_on',
                         velocity=velocity,
                         note=pitch,
                         channel=channel,
                         time=0),
            # note off
            mido.Message('note_off',
                         note=pitch,
                         channel=channel,
                         time=duration)
        ]

        return self.synthesize_messages(messages, **kwargs)

    def synthesize_midi_file(self, midifile: Any,
                             **kwargs) -> multiprocessing.Process:
        """
        Send midi messages contained in `filename` using
        `self.synthesize_messages`. All keywords from that method can be used
        here.

        `midifile` can be a `mido.MidiFile` object or a string

        After the playback, ports are resetted
        """

        if type(midifile) is str:
            midifile = mido.MidiFile(midifile)

        messages = [m for m in midifile]

        return self.synthesize_messages(messages, **kwargs)


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
        mid.tracks.append(track)
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
            _wait_dur(self._duration,
                      progress,
                      condition=lambda: self.process.poll() is None)
            self.kill()
        return self.process

    def close(self):
        """
        Remove temporary files created by this instance
        """
        if os.path.exists(self._tempname):
            os.remove(self._tempname)


def _wait_dur(dur, progress, condition=lambda: True, q=0.005):
    i = 0.0
    while i < dur and condition():
        if progress:
            progressbar(i, 1, dur, status='Synthesis')
        time.sleep(q)
        i += q
    if progress:
        progressbar(dur, 1, dur, status='Completed!')
