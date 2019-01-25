from setuptools import setup, find_packages

setup(
    # Application name:
    name="translation-management-service",

    # Version number (initial):
    version="1.0.02",

    # Application author details:
    author="joseph munoz",
    author_email="joseph.munoz@quintiles.com",

    # Packages
    packages=find_packages(),

    data_files = [
                  ('config', ['README.md'])
                 ],


    # Include additional files into the package
    include_package_data=True,

    # Details
    url="https://gitlab.ims.io/CC07/translation-management-service",

    #
    license="Usage restricted to IQVIA employees.",
    description="Document Translation REST service for translating documents.",

    long_description=open("README.md").read(),

    # Dependent packages (distributions)
    install_requires=[
        "flask>=0.12",
        "pandas>=0.16",
        "flasgger>=0.6.6",
        "flask-sqlalchemy",
        "Flask-API",
        "pyodbc>=4.0.17",
        "flask-restplus",
        "argparse",
        "python-logstash-async",
        "Flask-Migrate",
        "flask_cors",
        "lxml",
        "gevent",
        "amqp==2.1.3",
        "kombu",
    ],
)