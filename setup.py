from setuptools import setup, find_packages

setup(
    # Application name:
    name="electronic Trial Master File Automation",

    # Version number (initial):
    version="1.0.02",

    # Application author details:
    author="Prathap Veera",
    author_email="prathap.veera@quintiles.com",

    # Packages
    packages=find_packages(),

    data_files = [
                  ('config', ['README.md'])
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
		"python-editor-1.0.4" ,
		"kombu",
		"python-logstash_async"])