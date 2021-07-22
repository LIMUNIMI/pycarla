import multiprocessing
import os
import threading
import shutil
import time
from typing import Any, List, Union

import mido

from .utils import ExternalProcess, Popen, JackClient, get_smf_duration, progressbar


class MIDIPlayer(JackClient):

    MIDI_PORT = 'Carla'

    def __init__(self):
        """
        Creates a player which is able to connect to a Carla instance

        Optionally, `freewheel` can be used to start freeewheel mode before of
        playing.

        For now, only one Carla instance should be active.
        """
        super().__init__("MIDIPlayer")

    def activate(self):
        """
        Activate the MIDI player client and set the connections.

        If the Carla instance is not found, this method rase a
        `RuntimeWarning`. To avoid it, use ``Carla.exists`` method. Note that
        ``Carla.start`` already does that!
        """
        carla_ports = self.client.get_ports(self.MIDI_PORT,
                                            is_midi=True,
                                            is_input=True)
        if len(carla_ports) != 1:
            raise RuntimeWarning(
                "Cannot find the Carla instance, Retry later!")
        self.client.activate()
        self.client.midi_outports.clear()
        self.port = self.client.midi_outports.register('out')
        if not self.port.is_connected_to(carla_ports[0]):
            self.client.connect(self.port, carla_ports[0])
        self.is_active = True

    def wait(self, in_fw=False, out_fw=False):
        """
        waits while setting freewheeling mode to `in_fw`
        it then set freewheeling mode to `out_fw` before exiting
        """
        if hasattr(self, 'end_midiplayer'):
            self.client.set_freewheel(in_fw)
            self.end_midiplayer.wait()
            self.client.set_freewheel(out_fw)
        self.deactivate()

    def clear(self):
        """
        clears the `_messages` list
        """
        del self._messages
        self._messages = []

    def synthesize_messages(self,
                            messages: List[mido.Message],
                            sync=False,
                            condition=lambda: True,
                            **kwargs):
        """
        Synthesize a list of messages

        1. Connect the port of this jack client to Carla if not yet done
        2. Send the list of messages to the Carla instance

        If `sync` is True, this function waits until all messages have been
        processed, otherwise, it suddenly returns. You can wait by calling the
        `wait` method of this object.

        This function is compatible with freewheeling mode.  Freewheel prevents
        jack from waiting between return calls. This allows for the maximum
        allowed speed, but not output/input operation is done with system audio
        (i.e. you cannot listen/recording to anything while in freewheeling
        mode).

        `condition` is a function checked in the playing callback. If
        `condition()` is False, no message is sent. The callback start playing
        at the cycle after the one in which `condition()` becomes True.

        `kwargs` are passed to `wait` if `sync` is True.

        Note: Mido numbers channels 0 to 15 instead of 1 to 16. This makes them
        easier to work with in Python but you may want to add and subtract 1
        when communicating with the user.
        """
        self._messages = messages

        global msg, offset
        it = iter(self._messages)
        msg = next(it)
        offset = 0
        self.end_midiplayer = threading.Event()
        self.ready_at = -1

        @self.client.set_process_callback
        def process(frames):
            if self.is_active:
                global offset, msg
                for port in self.client.midi_outports:
                    if not self.is_ready():
                        print(self.client.name + " ready!")
                        # let other clients know that this is ready
                        self.ready_at = self.client.last_frame_time
                    elif condition():
                        # start only if other clients are ready too
                        port.clear_buffer()
                        while True:

                            if offset >= frames:
                                # wait for the correct block
                                offset -= frames
                                return
                            # Note: This may raise an exception:
                            port.write_midi_event(offset, msg.bytes())

                            try:
                                msg = next(it)
                            except StopIteration:
                                self.end_midiplayer.set()
                            offset += round(msg.time * self.client.samplerate)

        self.activate()
        if sync:
            self.wait(**kwargs)

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
                      condition=lambda: self.process.is_running())
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
