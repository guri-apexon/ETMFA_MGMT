from setuptools import setup, find_packages
import os

version = "1.0"

def get_requirements():
    lines = []
    for line in open("requirements.txt"):
        line = line.strip()
        if not line.startswith(('-', '#')):
            lines.append(line)
    return lines


requirements = get_requirements()

setup(
    # Application name:
    name="pd-mgmt",

    # Version number (initial):
    version=version,

    # Application author details:
    author="Prathap Veera",
    author_email="prathap.veera@quintiles.com",

    # Packages
    packages=find_packages(),

	# Packages
    data_files=[('', ['requirements.txt', 'main.py']),
                ],
	include_package_data=True,

    # Details
    url="http://ca2spdml01q:9001/pd/api/",

    license="Usage restricted to IQVIA employees.",
    description="Document processing REST service for document classification.",

    long_description=open("README.md").read(),

    # Dependent packages (distributions)
    install_requires=requirements,

	python_requires=">=3.7.*",

	entry_points={
        'console_scripts': [
            'pd-mgmt = main:cli',
        ]
    }

)