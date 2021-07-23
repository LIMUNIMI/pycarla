import subprocess
import sys
import os

import psutil
import mido


def get_smf_duration(filename):
    """
    Return note dration of a file from a path
    """
    return mido.MidiFile(filename).length


def progressbar(count, block_size, total, status='Download'):
    bar_len = 60
    count *= block_size
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()


def Popen(command, **args):
    """
    Custom call to ``psutil.Popen``
    """
    return psutil.Popen(command,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        **args)


def kill_psutil_process(process):
    """
    Kills a tree of `psutil.Process`
    """

    children = process.children(recursive=True)
    children.append(process)
    for p in children:
        try:
            p.kill()
        except psutil.NoSuchProcess:
            pass


def find_procs_by_name(name):
    """Return a list of processes matching 'name'."""
    ls = []
    for p in psutil.process_iter(["name", "exe", "cmdline"]):
        if name == p.info['name'] or \
                p.info['exe'] and os.path.basename(p.info['exe']) == name or \
                p.info['cmdline'] and p.info['cmdline'][0] == name:
            ls.append(p)
    return ls
