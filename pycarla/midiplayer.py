import multiprocessing
from typing import Any, List

import mido

from .generics import JackClient


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
                                self.end_wait.set()
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
