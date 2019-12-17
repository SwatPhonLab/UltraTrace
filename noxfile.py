import nox


@nox.session
def format(session):
    session.install("black")
    session.run("black", "--check", "ultratrace2")


@nox.session
def install(session):
    """Install ultratrace2. Assumes required system libraries are installed."""
    session.install(".")