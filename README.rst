pyCarla
==========

A python module for synthesizing MIDI events and files
from python code with using any kind of audio plugin!

See `docs <https://pycarla.readthedocs.org>`_ for more installation and more info.

TLDR
----

Python has no strong real-time capabilities since it cannot run with parallel threads.
This method delegates most of the realtime stuffs to external C/C++ programs, improving
the performances and the accuracy against pure-Python based approaches.

This method is really portable and supports almost any type of plugins and
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

For sure
~~~~~~~~

#. Add single function to synthesize midi file
#. Add single function to batch-synthesize midi files
#. Make synchronization handling xruns (edit `is_ready`)
#. Update Carla
#. refactoring with a generic `start` method in `JackClient` and 
   specific methods `get_callback` and `get_duration`

Maybe
~~~~~

#. Use Carla python code to control Carla host
#. Support LADISH sessions for automatically starting LinuxSampler if needed
#. Installation scripts for windows and mac


Credits
=======

#. `Federico Simonetta <https://federicosimonetta.eu.org>`_
    ``federico.simonetta`` ``at`` ``unimi.it``
