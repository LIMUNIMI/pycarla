pyCarla
=======

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.4332847.svg
   :target: https://doi.org/10.5281/zenodo.4332847

A python module for synthesizing MIDI events and files
from python code using any kind of audio plugin!

A python module based on ``carla`` and ``jack``!

.. toctree::
   :maxdepth: 2
   :caption: Table of Contents

   Installation
   Examples
   Classes
    
Why so many external dependencies?
----------------------------------

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

#. Support LADISH sessions for automatically starting LinuxSampler if needed

Credits
=======

#. `Federico Simonetta <https://federicosimonetta.eu.org>`_
    ``federico.simonetta`` ``at`` ``unimi.it``
