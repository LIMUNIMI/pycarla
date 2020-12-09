Installation
------------

The backbone of this project are the multiple dependencies on which it depends. Since it's difficult to provide a script to automatically install all of these dependencies, here is a little handbook about how to install them.

#. Use Linux: it's free. For Windows and Mac, you can still install the
   dependencies by compiling both ``jack_capture`` and ``jack-smf-utils`` from
   scratch; however, I refuse to support non-free software.
#. In general, use https://pkgs.org to llok for the command needed in your distro.
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


