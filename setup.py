from setuptools import setup, find_packages

setup(
    # Application name:
    name="etmfa_mgmt",

    # Version number (initial):
    version="1.0.0",

    # Application author details:
    author="Prathap Veera",
    author_email="prathap.veera@quintiles.com",

    # Packages
    packages=find_packages(),

    data_files = [
                  ('', ['main.py', 'manage.py'])
                 ],


    # Include additional files into the package
    include_package_data=True,

    # Details
    url="http://usadc-vsairnd02:3000/cognitive-automation-solutions/etmfa-management-service",

    #
    license="Usage restricted to IQVIA employees.",
    description="Document processing REST service for document classification.",

    long_description=open("README.md").read(),

    # Dependent packages (distributions)
    install_requires=[
	    "flask_restplus",
		"flask_migrate==2.5.2",
        "flask-sqlalchemy>=1.0",
		"alembic>=0.7",
		"flask>=0.9",
		"SQLAlchemy>=0.8.0",
		"Mako==1.0.12",
        "flask_cors",
        "requests",
        "pandas",
        "lxml",
		"kombu",
        "gevent",
        "cx_Oracle",
        "filehash",
		"python-logstash_async"])