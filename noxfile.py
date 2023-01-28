import nox


@nox.session
def install(session):
    """Install ultratrace. Assumes required system libraries are installed."""
    session.install("--requirement", "./requirements.txt")


@nox.session
def format(session):
    """Check code formatting."""
    session.install("--requirement", "./requirements-dev.txt")
    session.run("black", "--check", "./ultratrace")
