import nox


@nox.session
def install(session):
    """Install ultratrace. Assumes required system libraries are installed."""
    session.install("--requirement", "./requirements.txt")
