Usage
-----

Carla presets
`````````````

#. **Configure Carla in ``patchbay`` mode (if you cannot use GUI, set ``ProcessMode=3`` into ``~/.config/falkTX/Carla2.conf``)**
#. ``python -m pycarla.carla --run`` to launch Carla and prepare configurations

Initialization
``````````````

.. code-block:: python

   from pycarla import Carla, MIDIPlayer, AudioRecorder, get_smf_duration
   carla = Carla("carla_project.carxp", ['-R', '-d', 'alsa'], min_wait=4)
   carla.start()

   player = MIDIPlayer()
   recorder = AudioRecorder()

   # or
   with MIDIPlayer() as player, AudioRecorder() as recorder:
       # [...]
       pass

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
        carla.kill() # this kills both Carla and Jack
        # carla.kill_carla() # this kills Carla but not Jack
        sys.exit()

Playing and recording a full MIDI file
``````````````````````````````````````

.. code-block:: python

    print("Playing and recording full file using freewheeling mode..")
    duration = get_smf_duration("filename.mid")
    # in the following, `condition` ensures that both the recorder and player
    # start in the same cycle
    recorder.start(duration + FINAL_DECAY, condition=player.is_ready)
    player.synthesize_midi_file("filename.mid",
        condition=recorder.is_ready, in_fw=True, out_fw=True)
    # or asynchronously:
    # player.synthesize_midi_file("filename.mid", sync=False)
    # in this case, use
    # player.wait(in_fw=True, out_fw=True)
    recorder.wait(in_fw=True, out_fw=True)
    recorder.save_recorded("session.wav")
    player.close()
    server.close()

In future, there shold be a function that does this snippet for you

You can also use ``AudioRecorder`` and ``MIDIPlayer`` as context managers in a
``with`` block; in this case, skip the `close()` at the end:

.. code-block:: python

    with pycarla.AudioRecorder() as recorder, pycarla.MIDIPlayer() as player:
        # do your stuffs
        pass

Closing server
``````````````

.. code-block:: python

    try:
        carla.kill()
    except Exception as e:
        print("Processes already closed!")
