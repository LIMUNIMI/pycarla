import threading

import numpy as np
import soundfile as sf

from .generics import JackClient


class AudioRecorder(JackClient):
    AUDIO_PORT = 'Carla'

    def __init__(self):
        """
        Records output from a Carla instance.

        For now, only one Carla instance should be active.

        If the Carla instance is not found, this method raises a
        `RuntimeWarning`. To avoid it, use ``Carla.exists`` method. Note that
        ``Carla.start`` already does that!
        """
        super().__init__("AudioRecorder")

    def activate(self):
        """
        Activate the recording client and set the connections.
        Set self.channels and create one input port per each Carla output port.

        If the Carla instance is not found, this method rase a
        `RuntimeWarning`. To avoid it, use ``Carla.exists`` method. Note that
        ``Carla.start`` already does that!
        """
        # get default values and params
        carla_ports = self.client.get_ports(self.AUDIO_PORT,
                                            is_audio=True,
                                            is_output=True)
        if len(carla_ports) == 0:
            raise RuntimeWarning(
                "Cannot find the Carla instance, Retry later!")
        self.channels = len(carla_ports)
        self.ports = []
        self.client.activate()
        self.client.inports.clear()
        for i, p in enumerate(carla_ports):
            inp = self.client.inports.register(f"in{i}")
            if not inp.is_connected_to(p):
                self.client.connect(p, inp)
            self.ports.append(inp)
        self.is_active = True

    def clear(self):
        """
        Clears the `recorded` array
        """
        del self.recorded
        self.recorded = []

    def start(self,
              duration=None,
              sync=False,
              condition=lambda: True,
              **kwargs):
        """
        Record audio for ``duration`` seconds. Note that this function blocks
        if `sync` is True, otherwise, this returns suddenly and you
        should wait/stop by calling the `wait` method of this object which
        constructs the recorded array in `self.recorded`

        `condition` is a function checked in the recording callback. If
        `condition()` is False, blocks are discarded. The callback start
        recording at the cycle after the one in which `condition()` becomes
        True.

        This function is compatible with Jack freewheeling mode to record
        offline sessions.

        `kwargs` are passed to `wait` if `sync` is True.
        """
        global callback
        self.recorded = []
        self.ready_at = -1
        self.end_wait = threading.Event()

        if duration is not None:
            self._needed_samples = int(duration * self.client.samplerate)
        else:
            # values <= 0 causes the `end_wait` never being set
            self._needed_samples = -1

        @self.client.set_process_callback
        def callback(frames):
            channels = [i.get_array() for i in self.client.inports]
            if len(channels) == self.channels:
                if not self.is_ready():
                    # let other clients know that this is ready
                    print(self.client.name + " ready!")
                    self.ready_at = self.client.last_frame_time
                elif condition():
                    # start only if other clients are ready too
                    self.recorded.append(np.stack(channels))
                    if self._needed_samples > 0:
                        recorded_frames = self.client.last_frame_time -\
                            self.ready_at
                        if recorded_frames > self._needed_samples:
                            self.end_wait.set()

        self.activate()
        if sync:
            self.wait(**kwargs)

    def wait(self, timeout=None, in_fw=False, out_fw=False):
        """
        Wait until recording is finished. If `timeout` is a number, it should
        be the maximum number of seconds until which the recording stops. A
        boolean is returned representing if timeout is reached.
        (returns `False` if timeout is not set)

        The recording stops when `timeout` or the duration passed when calling
        `start` is reached. In these cases, the recording client is deactivated
        and the callback stopped.

        waits while setting freewheeling mode to `in_fw`
        it then set freewheeling mode to `out_fw` before exiting
        """
        assert timeout is not None or self._needed_samples > 0, "Please, provide one between`timeout` and `duration`"
        out = super().wait(timeout, in_fw, out_fw)
        if len(self.recorded) > 0:
            try:
                self.recorded = np.concatenate(self.recorded, axis=1)
            except Exception:
                print(
                    "Cannot concatenate the recorded blocks in one array, have you changed the number of channels while recording? In the `AudioRecorder.recorded` you will find the list of recorded blocks"
                )
        return out

    def save_recorded(self, filename):
        """
        Save the recorded array to file. Extensions supported by
        ``libsndfile``!

        `start_frame` is the frame from which recorded is saved (use it to
        discard initial delays due to Jack setup).
        """

        if not hasattr(self, 'recorded'):
            raise RuntimeError("No recorded array!")

        recorded = self.recorded.T
        try:
            sf.write(str(filename), recorded, int(self.client.samplerate))
        except Exception:
            print(
                "Cannot write with default sounddevice parameters. Try writing by yourself using `recorded` field!"
            )
