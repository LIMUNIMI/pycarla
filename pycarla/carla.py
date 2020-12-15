import argparse
import sys

from .synth import CARLA_PATH, Carla, JackServer

version = "2.1"


def progress(count, block_size, total, status='Download'):
    bar_len = 60
    count *= block_size
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()


def download():
    import platform
    import tarfile
    import urllib.request
    import shutil
    import random

    if sys.platform == 'linux':
        # download carla
        print("Downloading...")
        arch = platform.architecture()[0][:2]
        target_url =\
            'https://github.com/falkTX/Carla/releases/download/v' + \
            version + '/Carla_' + version + '-linux' +\
            arch + '.tar.xz'
        try:
            fname, header = urllib.request.urlretrieve(target_url,
                                                       reporthook=progress)
        except Exception as e:
            print("Error while downloading Carla!", file=sys.stderr)
            print(e, file=sys.stderr)
        progress(10, 1, 10, status='Completed!')
        print("\n")

        print("Extracting archive...")
        rand = str(random.randint(10**4, 10**5))
        tmp_path = "/tmp/carla" + "-" + rand
        with tarfile.open(fname, "r:xz") as file:
            file.extractall(tmp_path)

        shutil.move(tmp_path + "/Carla_" + version + "-linux" + arch,
                    CARLA_PATH)
    else:
        print(
            "Your OS is against the freedom of software developers because its\
sources are closed. I don't support closed software. You can still download\
Carla by yourself and put the `Carla` command in your path.")


def run_carla():
    server = JackServer(['-R', '-d', 'alsa'])
    carla = Carla("", server, min_wait=0, nogui=False)
    carla.start()
    carla.process.wait()
    try:
        carla.kill()
    except:
        print("Processes already closed!")


argparser = argparse.ArgumentParser(
    description="Manage the Carla instance verion")
argparser.add_argument(
    "-d",
    "--download",
    action="store_true",
    help="Download the correct Carla version in the installation directory of\
this python package.")

argparser.add_argument("-r",
                       "--run",
                       action="store_true",
                       help="Run the Carla instance previously downloaded.")

if __name__ == "__main__":
    args = argparser.parse_args()
    if args.download and args.run:
        print("Please, provide one option at a time!")
    else:
        if args.download:
            download()
        elif args.run:
            run_carla()
        else:
            argparser.print_help()
