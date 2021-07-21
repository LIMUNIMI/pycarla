import time

import numpy as np
import soundfile as sf

from .utils import JackClient


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

    def start(self, duration=None, sync=False, condition=lambda: True):
        """
        Record audio for ``duration`` seconds. Note that this function blocks
        if `sync` is True, otherwise, this returns suddenly and you
        should wait/stop by calling the `wait` method of this object which
        constructs the recorded array in `self.recorded`

        `condition` is a function checked in the recording callback. If
        `condition` is False, blocks are discarded.

        This function is compatible with Jack freewheeling mode to record
        offline sessions.
        """
        global callback
        self.recorded = []

        @self.client.set_process_callback
        def callback(frames):
            channels = [i.get_array() for i in self.client.inports]
            if len(channels) == self.channels and condition():
                self.recorded.append(np.stack(channels))

        if duration is not None:
            self._needed_samples = int(duration * self.client.samplerate)
        else:
            # values <= 0 cause the wait to hang until `timeout`
            self._needed_samples = -1

        self.activate()
        if sync:
            self.wait()

    def wait(self, timeout=None):
        """
        Wait until recording is finished. If `timeout` is a number, it should
        be the maximum number of seconds until which the recording stops. A
        boolean is returned representing if timeout is reached.
        (returns `False` if timeout is not set)

        The recording stops when `timeout` or the duration passed when calling
        `start` is reached. In these cases, the recording client is deactivated
        and the callback stopped.
        """
        assert timeout is not None or self._needed_samples > 0, "Please, provide one between`timeout` and `duration`"
        reached_timeout = False
        if self.is_active:
            # wait the needed number of blocks
            ttt = time.time()
            CONTINUE = True
            while CONTINUE:
                if timeout is not None:
                    if time.time() - ttt > timeout:
                        reached_timeout = True
                        break
                time.sleep(0.001)
                if self._needed_samples > 0:
                    CONTINUE = sum(
                        i.shape[1]
                        for i in self.recorded) < self._needed_samples

            self.deactivate()
            try:
                self.recorded = np.concatenate(self.recorded, axis=1)
            except Exception:
                print(
                    "Cannot concatenate the recorded blocks in one array, have you changed the number of channels while recording? In the `AudioRecorder.recorded` you will find the list of recorded blocks"
                )
        return reached_timeout

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
