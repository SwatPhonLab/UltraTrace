from setuptools import setup, find_namespace_packages


def get_requirements(path):
    with open(path) as f:
        return list(filter(lambda s: len(s) > 0, (get_requirement(l) for l in f)))


def get_requirement(line):
    r, *_ = line.split("#")
    return r.strip().split()


setup(
    name="ultratrace",
    author="Jonathan Washington",
    author_email="jwashin1@swarthmore.edu",
    version="0.0.1",
    packages=find_namespace_packages(
        include=["ultratrace2.*"], exclude=["ultratrace.*"]
    ),
    description="A tool for manually annotating ultrasound tongue imaging (UTI) data",
    install_requires=get_requirements("requirements.txt"),
    entry_points={
        "console_scripts": [
            "ultratrace2 = ultratrace2.__main__:main"
        ]
    },
    extras_require={
        "dev": [
            "flake8",
            "black",
            "mypy",
            "pytest",
            "numpy-stubs @ git+https://github.com/numpy/numpy-stubs.git@master",
            "pytest-cov",
            "pytest-mock",
            "boto3",
            "mypy-boto3-s3",
        ]
    },
)
