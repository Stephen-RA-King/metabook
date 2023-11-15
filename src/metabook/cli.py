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
        "-r",
        "--recurse",
        action="store_true",
        help="recurse through subdirectories",
    )

    return parser.parse_args(args), parser
