import argparse
import logging

from .app import initialize_app

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    # noqa: E128
    parser.add_argument(
        "path",
        default=None,
        help="path (unique to a participant) where subdirectories contain raw data",
    )
    parser.add_argument(
        "--no-audio",
        dest="audio",
        action="store_false",
        help="don't try to load the audio widget",
    )
    parser.add_argument(
        "--no-dicom",
        dest="dicom",
        action="store_false",
        help="don't try to load the dicom widget",
    )
    parser.add_argument(
        "--no-textgrid",
        dest="textgrid",
        action="store_false",
        help="don't try to load the textgrid widget",
    )
    parser.add_argument(
        "--no-spectrogram",
        dest="spectrogram",
        action="store_false",
        help="don't try to load the spectrogram widget",
    )
    parser.add_argument(
        "--no-video",
        dest="video",
        action="store_false",
        help="don't try to load the video widget",
    )
    parser.add_argument("--theme", help="TtkTheme to use for application")
    parser.add_argument(
        "--max-undo-memory",
        type=int,
        default=1000,
        help="number of operations to remember in the UndoManager",
    )

    args = parser.parse_args()

    app = initialize_app(args)
    app.main()
