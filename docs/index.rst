jack_synth
==========

A python module based on Linux commands for synthesizing MIDI events and files
from python code with ultra time precision using any kind of audio plugin!

A python module based on ``carla``, ``jack_capture``, ``jack-smf-utils``, and ``jack``, of course!

.. toctree::
   :maxdepth: 2
   :caption: Table of Contents

    Installation
    Examples
    Classes
    
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
