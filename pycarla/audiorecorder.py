import time

import jack
import numpy as np
import soundfile as sf


class AudioRecorder():
    AUDIO_PORT = 'Carla'

    def __init__(self, channels=None):
        """
        Records output from a Carla instance.

        For now, only one Carla instance should be active.

        If `channels` is `None`, the maximum value usable for Carla is used

        If the Carla instance is not found, this method raises a
        `RuntimeWarning`. To avoid it, use ``Carla.exists`` method. Note that
        ``Carla.start`` already does that!
        """
        super().__init__()

        self.recorder = jack.Client("AudioRecorder")
        self.is_active = False

        if channels:
            self.channels = channels

    def deactivate(self):
        """
        Deactivates the client and unregisters all input ports
        """
        self.recorder.deactivate()
        self.recorder.inports.clear()
        self.is_active = False

    def activate(self):
        """
        Activate the recording client and set the connections.
        Set self.channels and create one input port per each Carla output port.

        If the Carla instance is not found, this method rase a
        `RuntimeWarning`. To avoid it, use ``Carla.exists`` method. Note that
        ``Carla.start`` already does that!
        """
        # get default values and params
        ports = self.recorder.get_ports(self.AUDIO_PORT,
                                        is_audio=True,
                                        is_output=True)

        if len(ports) == 0:
            raise RuntimeWarning(
                "Cannot find the Carla instance, Retry later!")
        self.channels = len(ports)
        self.ports = []
        self.recorder.activate()
        for i, p in enumerate(ports):
            inp = self.recorder.inports.register(f"in{i}")
            self.recorder.connect(p, inp)
            self.ports.append(inp)
        self.is_active = True

    def start(self, duration, sync=False):
        """
        Record audio for ``duration`` seconds. Note that this function blocks
        if `sync` is True, otherwise, this returns suddenly and you
        should wait/stop by calling the `wait` method of this object which
        constructs the recorded array in `self.recorded`

        This function is compatible with Jack freewheeling mode to record
        offline sessions.
        """
        global callback, data, client
        data = []
        client = self.recorder

        @client.set_process_callback
        def callback(frames):
            data.append(
                np.stack([i.get_array() for i in client.inports]))


        self._needed_samples = int(duration * self.recorder.samplerate)

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
        reached_timeout = False
        if self.is_active:
            global data
            # wait the needed number of blocks
            ttt = time.time()
            while sum(i.shape[1] for i in data) < self._needed_samples:
                if timeout is not None:
                    if time.time() - ttt > timeout:
                        reached_timeout = True
                        break
                time.sleep(0.001)
            self.deactivate()
            self.recorded = np.concatenate(data, axis=1)
            del data
        return reached_timeout

    def save_recorded(self, filename):
        """
        Save the recorded array to file. Extensions supported by
        ``libsndfile``!
        """

        if not hasattr(self, 'recorded'):
            raise RuntimeError("No recorded array!")

        recorded = self.recorded.T
        sf.write(filename, recorded, int(self.recorder.samplerate))

    def close(self):
        """
        Just deactivate and closes the recording client
        """
        self.deactivate()
        self.recorder.close()
