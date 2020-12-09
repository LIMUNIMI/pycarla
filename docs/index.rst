PyJackSynth
===========

Use any kind of plugin to synthesize midi events!

Installation
------------

The backbone of this project are the multiple dependencies on which it depends. Since it's difficult to provide a script to automatically install all of these dependencies, here is a little handbook about how to install them.

#. Use Linux: it's free. For Windows and Mac, you can still install the
   dependencies by compiling both ``jack_capture`` and ``jack-smf-utils`` from
   scratch; however, I refuse to support non-free software.
#. In general, use `https://pkgs.org`_ to llok for the command needed in your distro.
#. Install: ``jackd``, ``jack_capture``, ``jack-smf-utils``, ``carla``
#. Make sure that they are available in your ``PATH`` environment variable

TLDR
````

Use Arch, if you can, and install everything from the official repositories.
Use pip to install the package: ``pip install jack_synth``

Installing jack
```````````````

Pre-built binaries for major OS available at
https://jackaudio.org/downloads/

#. Ubuntu/Debian based: ``sudo apt-get install jackd2``
#. Arch based: ``sudo pacman -Sy jack2``
#. Gentoo based: ``sudo emerge -a media-sound/jack2``
#. Fedora based: ``sudo dnf install jack-audio-connection-kit``

Installing jack_capture
```````````````````````
#. Ubuntu/Debian based: ``sudo apt-get install jack-capture``
#. Arch based: ``sudo pacman -Sy jack_capture``
#. Gentoo based: ``sudo emerge -a media-sound/jack_capture``
#. Fedora based: ``sudo dnf install jack_capture``

Installing jack-smf-utils
`````````````````````````

TODO: automated compilation and installation in local directory

#. Ubuntu/Debian based: no package available, `download source
   <https://github.com/zynthian/jack-smf-utils>`_ and compile
#. Arch based: ``sudo pacman -Sy jack-smf-utils``
#. Gentoo based: ``sudo emerge -a media-sound/jack-smf-utils``
#. Fedora based: no package available, `download source
   <https://github.com/zynthian/jack-smf-utils>`_ and compile

Installing Carla
``````````````````

Pre-built binaries for major OS available at
https://github.com/falkTX/Carla/releases/latest

#. Ubuntu/Debian based: ``apt-get install carla``; for Debian, install `KXStudio
   repositories: <https://kx.studio/Repositories>`_
#. Arch based: ``sudo pacman -Sy cadence``
#. Gentoo based: no package available
#. Fedora based: ``dnf install carla``

**N.B. Configure Carla in ``patchbay`` mode (if you cannot use GUI, set ``ProcessMode=3`` into ``~/.config/falkTX/Carla2.conf``)**

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

Development setup
-----------------

#. Install poetry: ``curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python``
#. Enter root directory of this project
#. ``poetry update``
#. Put all the Carla configurations that you want to use in ``data/carla_proj``
   Note that you can use the default ones, provided you have the same plugins
   available, otherwise you have to delete the default project files. 

Used plugins are:
    * Pianoteq
    * SalamanderGrandPianoV3_ uncompressed in ``~/salamander/``
    * Calf Reverb

.. _SalamanderGrandPianoV3: http://freepats.zenvoid.org/Piano/SalamanderGrandPiano/SalamanderGrandPianoV3+20161209_48khz24bit.tar.xz

#. Run ``poetry run -m jack_synth`` to do a little test


Why so many external dependencies?
----------------------------------

Python has no strong real-time capabilities since it cannot run with parallel threads.
This method delegates all the realtime stuffs to external C/C++ programs, improving
the performances and the accuracy against Python based approaches.

Another problem with generic VSTs is that we cannot use Jack in freewheeling
mode because not all the plugins support it, thus, we need to play midi events
in real-time, with no speed-up - i.e. if a midi file lasts 4 minutes, the
synthesis process will also last 4 minutes.

Of course, there is a lot of overhead due to process spawning, registrations of Jack
clients and reading/writing to the SSD, but, after all, it is a little overhead
because the major part of time is taken by the real-time mode.

However, this method is really portable and supports almost any type of plugins and
virtual instruments thanks to the excellent Carla:

#. Linux VST2/VST3
#. Windows VST2/VST3
#. LV2
#. LADSPA
#. DSSI
#. AU
#. SF2/SF3
#. SFZ
#. Any other format supported by external plugins

TODO
----

#. Create installation scripts to:
  
   #. jack-smf-player
   #. setup carla configuration file
   #. setup path to the binaries

#. Support LADISH sessions for automatically starting LinuxSampler if needed

Credits
=======

#. `Federico Simonetta <https://federicosimonetta.eu.org>`_
    ``federico.simonetta`` ``at`` ``unimi.it``
