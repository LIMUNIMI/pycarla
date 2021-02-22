pyCarla
==========

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.4332846.svg
   :target: https://doi.org/10.5281/zenodo.4332846

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

Credits
=======

#. `Federico Simonetta <https://federicosimonetta.eu.org>`_
    ``federico.simonetta`` ``at`` ``unimi.it``
