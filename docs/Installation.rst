Installation
------------

The backbone of this project are the multiple dependencies on which it depends. Since it's difficult to provide a script to automatically install all of these dependencies, here is a little handbook about how to install them.

#. Use Linux: it's free. For Windows and Mac, you can still install Carla and
   Jack by yourself; however, I refuse to support non-free software.
#. In general, use https://pkgs.org to look for the command needed in your
   distro.
#. Install: ``jackd``
#. Make sure that it is available in your ``PATH`` environment variable

Installing pycarla
``````````````````

``pip install --upgrade pip pycarla``

Installing jack
```````````````

#. Ubuntu/Debian based: ``sudo apt-get install jackd2``
#. Arch based: ``sudo pacman -Sy jack2``
#. Gentoo based: ``sudo emerge -a media-sound/jack2``
#. Fedora based: ``sudo dnf install jack-audio-connection-kit``

For other Os, pre-built binaries are available at
https://jackaudio.org/downloads/

Installing Carla
``````````````````

After having installed the package, run ``python -m pycarla.carla --download``
to download the correct version of Carla.

If you're not in Linux, pre-built binaries for major OS available at
https://github.com/falkTX/Carla/releases/latest

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

#. Run ``poetry run -m pycarla`` to do a little test
