
# eTMFA Management Service

The eTMFA Management Service (<em>eTMF-MS</em>) provides a series of endpoints for the coordination of the document eTMF Automation workflow ("Classifier"), consisting of the <em>Triage</em>, <em>Digitizer</em>, <em>Classifier</em>, <em>Attribute Extraction</em>, <em>Finalization</em> microservices. 

... supported formats
## Outline

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Workflow](#workflow)
5. [Usage](#usage)
6. [Contribution](#contribution)
7. [Tentative Roadmap](#roadmap)
8. [Contacts](#contacts)
9. [License](#license)

## Quick Start
1. Given the application python package
   * ```pip install <local package>```
2. Start central Luigi scheduler, the core task runner for running the eTMFA AI pipeline.
   * ```python main.py```


### Development
1. Clone the git repository
2. Install project dependencies
    * `python setup.py`
4. Run the development server
    * `python ./main.py`
        * This starts a web interface for uploading files to process.
        * Interact with the Open API Documentation at **'http://morsetmfml01d:9001/etmfa/api/v1/documents/' **

### Production (single node)
1. Given the application python package
   * `pip install <local package>`
2. Run the server:
    * `python ./main.py --level production` file and run:
*Note*: If served on Windows, consider wrapping the above line in a Windows Service through [NSSM](https://www.nssm.cc). For example usage, go to the [usage section](#usage). If you require a package distribution, please contact the project authors.

#### SSL support:
Include the certificate and key files when starting the project.

Example:
* `python ./main.py --level production --key ./server.key --cert ./certificate.cert`

### Generate package

To generate a pip-installable package of the server for deployment, run `python setup.py sdist`. The resulting package will be generated in the "./dist" folder.

## Installation

1. Clone this repository to the working directory via ```git clone <repository link>```
2. Install Python dependencies. Pip is used in the example, but and alternatives are fine (e.g. Anaconda, easy_install).
   * (Optional) Create a python [virtual environment](http://python-guide-pt-br.readthedocs.io/en/latest/dev/virtualenvs/).
      * ```virtualenv eTMF-MS```
   * ```python setup.py```

##### Dependencies
* Python 3 
  * Pandas
  * Flask and flask utility libraries
      * Provides web interface for administrative REST API and file uploads.
  * Sqlalchemy
      * Python and SQL compatible ORM. 
  * Pyodbc
      *  SQL Server driver and connection management.
  * [Gevent](http://www.gevent.org/index.html)
    * Server code
  * **SQL Server**
    * Location configured in the package
 * (Optional)
   * [RabbitMQ](https://www.rabbitmq.com) messaging
   * [ELK](https://www.elastic.co/elk-stack) logging

#### OpenAPI
The hosted application also allows discovery of endpoints through a UI, hosted at **<hostname>/api**. 

## Configuration

The eTMF-MS supports configuration through the REST API. To begin processing, users must configure the processing directory.

### Processing_upload_folder
processing upload folder settings can be changed in config.py through DFS_UPLOAD_FOLDER

## Workflow
The eTMF-MS was build to support the potential for human translator involvement. In the eTMFA Management Service workflow, the machine classification is used to augment the human eTMF Records Management effort by generating the initial document attributes. Reviewers are then allowed to review the document attributes. If changes are made, the results are fed back to the eTMF AI system, triggering the incremental learning modifications.

## Usage

Document requests are submitted via the REST API and monitored through polling various properties. All requests return a JSON resource that corresponds to the document request. Each resource holds the state of the request and additional metadata.

The key endpoints and their descriptions are listed below:
* **POST /eTMFA/**
    * The initial request to classify a document.
* **GET /eTMFA/{id}**
    * Retrieve the corresponding document request object. This is frequently used to poll for the completion of a job, indicated by the ```is_processing``` property or ```status``` object.
* **GET /eTMFA/{id}/attributes**
    * Retrieve the document attributes.
* **PUT /eTMFA/{id}/attributes**
    * Update the document attributes with the human-verified feedback.

For further details, view the [Open API specification](OpenAPI).

---

## Contribution
Anyone is welcome to submit ideas and Pull Requests (e.g. "Merge Requests" in Gitlab) to this repository and activity is highly encouraged. Feel free to open up discussion on proposed changes prior to submitted for review to core contributors. 

## Contacts

## License
Property of IQVIA (2019). Not for distribution. Internal use only.

