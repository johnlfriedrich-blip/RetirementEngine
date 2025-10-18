from setuptools import setup, find_packages

setup(
    name="retirement_engine",
    version="0.1.0",
    packages=find_packages(where="retirement_engine"),
    package_dir={"": "retirement_engine"},
)
