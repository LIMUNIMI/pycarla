Usage
-----

Setup:

.. code-block:: python

   from jack_synth import Carla, MIDIPlayer, MIDIRecorder, JackServer, get_smf_duration
   server = JackServer(['-R', '-d', 'alsa'])
   carla = Carla("carla_project.carxp", server, min_wait=4)
   carla.start()

   player = MIDIPlayer()
   recorder = MIDIRecorder()

Playing and recording one note:

.. code-block:: python 

    print("Playing and recording one note..")
    duration = 2
    pitch = 64
    recorder.start('tmp.wav', duration + FINAL_DECAY)
    player.synthesize_midi_note(pitch, 64, duration, 0)
    player.wait()
    recorder.wait()
    audio, sr = recorder.get_recorded()
    if not np.any(audio):
        print("Error, no sample != 0")
        carla.kill()
        sys.exit()

Playing and recording a full midi file:

.. code-block:: python

    print("Playing and recording full file..")
    duration = get_smf_duration("filename.mid")
    recorder.start('session.wav', duration + FINAL_DECAY)
    player.synthesize_midi_file("filename.mid")
    player.wait()
    recorder.wait()

Closing server, processes and deleting recorded files:

.. code-block:: python

    recorder.del_recorded()
    player.close()
    carla.kill()

