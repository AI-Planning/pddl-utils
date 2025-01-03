
from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="pddl-utils",
    version="0.0.1",
    packages=find_packages(exclude=["tests"]),
    description="Library of miscellaneous utilies to work with PDDL (both in Python and on the command line).",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Christian Muise",
    author_email="christian.muise@gmail.com",
    install_requires=["pddl"],
    license="MIT",
    url="https://github.com/AI-Planning/pddl-utils",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
