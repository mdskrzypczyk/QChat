import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="qchat",
    version="0.0.1",
    author="Matt Skrzypczyk",
    author_email="mdskrzypczyk@tuta.io",
    description="An encrypted chat application for use with Simulaqron.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mdskrzypczyk/QChat",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)