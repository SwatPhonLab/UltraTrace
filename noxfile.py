import nox


@nox.session
def format(session):
    session.install("black")
    session.run("black", "--check", "ultratrace2")


@nox.session
def install(session):
    """Install ultratrace2. Assumes required system libraries are installed."""
    session.install(".")


@nox.session
def typecheck(session):
    """Run static analyzer against source files."""
    session.install(".[dev]")
    session.run("mypy", "ultratrace2")


@nox.session
def lint(session):
    session.install(".[dev]")
    session.run("flake8", "ultratrace2")


@nox.session
def tests(session):
    session.install(".[dev]")
    session.run("pytest", "ultratrace2")
