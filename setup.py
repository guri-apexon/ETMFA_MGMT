from setuptools import setup, find_packages
import os

version = "1.0"
build_number = os.getenv("bamboo_buildNumber")
if build_number:
    version += "." + build_number

setup(
    # Application name:
    name="etmfa_mgmt",

    # Version number (initial):
    version=version,

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
		"alembic==1.1.0",
		"amqp==2.5.1",
		"aniso8601==7.0.0",
		"attrs==19.1.0",
		"certifi==2019.6.16",
		"cffi==1.12.3",
		"chardet==3.0.4",
		"Click==7.0",
		"cx-Oracle==7.2.2",
		#"etmfa-mgmt==1.0.14",
		"filehash==0.1.dev3",
		"Flask==1.1.1",
		"Flask-Cors==3.0.8",
		"Flask-Migrate==2.5.2",
		"flask-restplus==0.13.0",
		"Flask-Script==2.0.6",
		"Flask-SQLAlchemy==2.4.0",
		"gevent==1.4.0",
		"greenlet==0.4.15",
		"idna==2.8",
		"importlib-metadata==0.20",
		"itsdangerous==1.1.0",
		"Jinja2==2.10.1",
		"jsonschema==3.0.2",
		"kombu==4.6.4",
		"limits==1.3",
		"lxml==4.4.1",
		"Mako==1.0.12",
		"MarkupSafe==1.1.1",
		"more-itertools==7.2.0",
		"numpy==1.17.2",
		"pandas==0.25.1",
		"pycparser==2.19",
		"pylogbeat==1.0.2",
		"pyrsistent==0.15.4",
		"python-dateutil==2.8.0",
		"python-editor==1.0.4",
		"python-logstash-async==1.5.1",
		"pytz==2019.2",
		"requests==2.22.0",
		"six==1.12.0",
		"SQLAlchemy==1.3.8",
		"urllib3==1.25.3",
		"vine==1.3.0",
		"Werkzeug==0.15.6",
		"zipp==0.6.0"])