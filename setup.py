from setuptools import setup, find_packages

setup(
    name="retirement_engine",
    version="0.1.0",
    package_dir={"": "backend"},
    packages=find_packages(
        where="backend", include=["retirement_engine", "retirement_engine.*"]
    ),
    install_requires=[
        "pandas>=2.0",
        "numpy>=1.24",
        "matplotlib>=3.7",
        "ipywidgets>=8.0",
        "streamlit>=1.30",  # Optional: for web app transition
        "PyYAML>=6.0",
    ],
    author="John Friedrich",
    description="Modular retirement simulation engine with interactive controls and realistic portfolio modeling.",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)
