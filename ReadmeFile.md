# eTMFA Management Service

The eTMFA Management Service (<em>eTMF-MS</em>) provides a series of endpoints for the coordination of the document eTMF Automation workflow ("Classifier"), 
consisting of the <em>Triage</em>, <em>Digitizer</em>, <em>Classifier</em>, <em>Attribute Extraction</em>, <em>Finalization</em> microservices. 



1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Workflow](#workflow)
5. [Usage](#usage)
6. [Contribution](#contribution)
7. [Tentative Roadmap](#roadmap)
8. [Contacts](#contacts)
9. [License](#license)


1. [Quick Start](#quick-start)
2. [Installation of Packages](#installation)
3. [Configuration](#configuration)
4. [Workflow](#workflow)


## Quick Start
1. Given the application python package
   * ```pip install <local package>```
2. run main.py from Anaconda prompt , the core task runner for running the eTMFA AI pipeline.
   * ```python main.py`
   
   
 ### Production (single node)
1. Given the application python package
   * `pip install <local package>`
2. Run the server:
    * `python ./main.py --level production` file and run:
*Note*: If served on Windows, consider wrapping the above line in a Windows Service through [NSSM](https://www.nssm.cc). For example usage, go to the [usage section](#usage). If you require a package distribution, please contact the project authors.