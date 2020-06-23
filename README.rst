PyJackSynth
===========

Use any kind of plugin to synthesize midi events!

Basic Setup (development)
-------------------------

#. Install poetry: ``curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python``
#. Enter root directory of this project
#. ``poetry install``
#. Download ``Carla`` for your OS and uncompress it under ``data/carla``
   directory
#. Configure Carla in ``patchbay`` mode (if you cannot use GUI, set
   ``ProcessMode=3`` into ``~/.config/falkTX/Carla2.conf``)
#. Install ``jack_capture`` and ``jack-smf-player`` in your ``PATH``
   environment variable
#. Put all the Carla configurations that you want to use in ``data/carla_proj``
   Note that you can use the default ones, provided you have the same plugins
   available, otherwise you have to delete the default project files. 

Used plugins are:
    * Pianoteq
    * SalamanderGrandPianoV3_ uncompressed in ``~/salamander/``
    * Calf Reverb

.. _SalamanderGrandPianoV3: http://freepats.zenvoid.org/Piano/SalamanderGrandPiano/SalamanderGrandPianoV3+20161209_48khz24bit.tar.xz


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
   #. optionally download Jack, Carla, jack-smf-player and jack_capture
   #. setup carla configuration file
   #. setup path to the binaries
#. Support LADISH sessions for automatically starting LinuxSampler if needed

Credits
=======

#. `Federico Simonetta <https://federicosimonetta.eu.org>`_
    ``federico.simonetta`` ``at`` ``unimi.it``
