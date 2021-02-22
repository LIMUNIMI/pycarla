Usage
-----

Carla presets
`````````````

#. **Configure Carla in ``patchbay`` mode (if you cannot use GUI, set ``ProcessMode=3`` into ``~/.config/falkTX/Carla2.conf``)**
#. ``python -m pycarla.carla --run`` to launch Carla and prepare configurations

Initialization
``````````````

.. code-block:: python

   from pycarla import Carla, MIDIPlayer, AudioRecorder, JackServer, get_smf_duration
   server = JackServer(['-R', '-d', 'alsa'])
   carla = Carla("carla_project.carxp", server, min_wait=4)
   carla.start()

   player = MIDIPlayer()
   recorder = AudioRecorder()

Playing and recording one note
``````````````````````````````

.. code-block:: python

    print("Playing and recording one note..")
    duration = 2
    pitch = 64
    recorder.start(duration + FINAL_DECAY)
    player.synthesize_midi_note(pitch, 64, duration, 0, sync=True)
    recorder.wait()
    audio = recorder.recorded
    if not np.any(audio):
        print("Error, no sample != 0")
        carla.kill()
        sys.exit()

Playing and recording a full MIDI file
``````````````````````````````````````

.. code-block:: python

    print("Playing and recording full file using freewheeling mode..")
    duration = get_smf_duration("filename.mid")
    server.toggle_freewheel()
    recorder.start(duration + FINAL_DECAY)
    player.synthesize_midi_file("filename.mid", sync=True, progress=False)
    # or asynchronously:
    # player.synthesize_midi_file("filename.mid", sync=False)
    # in this case, use
    # player.wait()
    recorder.wait()
    server.toggle_freewheel()
    recorder.save_recorded("session.wav")

Closing server
``````````````

.. code-block:: python

    try:
        carla.kill()
    except Exception as e:
        print("Processes already closed!")
