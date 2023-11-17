# Core Library modules
import argparse


def _parse_args(args: list) -> tuple[argparse.Namespace, argparse.ArgumentParser]:
    """Function to return the ArgumentParser object created from all the args.

    Args:
        args:   A list of arguments from the commandline
                e.g. ['metabook', '.', '-r']
    """
    parser = argparse.ArgumentParser(
        prog="metabook",
        description="Find a pdf book metadata and update filename and file metadata ",
    )
    parser.add_argument(
        "folder",
        nargs=1,
        default="None",
        help="The directory to search for pdf books",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="process all pdf files",
    )
    parser.add_argument(
        "-d",
        "--dryrun",
        action="store_true",
        help="process the pdf files but do not write to the files",
    )
    parser.add_argument(
        "-l",
        "--log",
        action="store_true",
        help="create a file to record the file changes",
    )
    parser.add_argument(
        "-r",
        "--recurse",
        action="store_true",
        help="recurse through subdirectories",
    )

    return parser.parse_args(args), parser
