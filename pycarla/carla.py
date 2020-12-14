import argparse
import sys

from .synth import CARLA_PATH, Carla, JackServer


def progress(count, block_size, total, status='Downloading...'):
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
    import urllib

    if sys.platform == 'linux':
        # download carla
        print("Downloading...")
        arch = platform.architecture()[0][:2]
        target_url =\
            'https://github.com/falkTX/Carla/releases/download/v2.1/Carla_2.1-linux' + arch + '.tar.xz'
        try:
            fname, header = urllib.request.urlretrieve(  # type: ignore
                target_url, reporthook=progress)
        except Exception as e:
            print("Error while downloading Carla!", file=sys.stderr)
            print(e, file=sys.stderr)

        print("Extracting archive...")
        with tarfile.open(fname, "r:xz") as file:
            file.extractall(CARLA_PATH)
    else:
        print(
            "I don't support closed software. You can still download Carla by yourself and put the `Carla` command in you command path"
        )


def run_carla():
    server = JackServer(['-R', '-d', 'alsa'])
    carla = Carla("", server, min_wait=0, nogui=False)
    carla.start()
    carla.process.wait()
    carla.kill()


argparser = argparse.ArgumentParser(
    description="Manage the Carla instance verion")
argparser.add_argument(
    "-d",
    "--download",
    action="store_true",
    help="Download the correct Carla version in the installation directory of this python package."
)

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
            argparser.print_usage()
