import argparse
import sys

from .synth import CARLA_PATH, Carla, JackServer, progressbar

version = "2.1"


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
                                                       reporthook=progressbar)
        except Exception as e:
            print("Error while downloading Carla!", file=sys.stderr)
            print(e, file=sys.stderr)
        progressbar(10, 1, 10, status='Completed!')
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


if __name__ == "__main__":
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
