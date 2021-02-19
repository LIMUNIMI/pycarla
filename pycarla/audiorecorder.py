import soundfile as sf
import sounddevice as sd


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

        If the Carla instance is not found, this method rase a
        `RuntimeWarning`. To avoid it, use ``Carla.exists`` method. Note that
        ``Carla.start`` already does that!
        """
        super().__init__()

        # make newer jack and carla instances visible to sounddevice and jack:
        sd._exit_handler()
        sd._initialize()

        self.get_default_params()
        if channels:
            self.channels = channels
        if samplerate:
            self.samplerate = samplerate
        self.dtype = dtype
        sd.default.device = self.AUDIO_PORT

    def get_default_params(self):
        """
        Set channels and samplerate according to the default paramters of the
        device.

        If the Carla instance is not found, this method rase a
        `RuntimeWarning`. To avoid it, use ``Carla.exists`` method. Note that
        ``Carla.start`` already does that!
        """
        # get default values and params
        devicelist = sd.query_devices()
        found = False
        for device in devicelist:
            if self.AUDIO_PORT in device['name'].lower():
                found = True
                self.channels = device['max_output_channels']
                self.samplerate = device['default_samplerate']

        if not found:
            raise RuntimeWarning(
                "Cannot find the Carla instance, Retry later!")
        sd.default.device = self.AUDIO_PORT

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
        Save the recorded array to file. Extensions supported by
        ``libsndfile``!
        """

        if not hasattr(self, 'recorded'):
            raise RuntimeError("No recorded array!")

        sf.write(filename, self.recorded, int(self.samplerate))
