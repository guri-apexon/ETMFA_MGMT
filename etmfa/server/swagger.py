from flasgger import Swagger

def configure_swagger(app):
    """
    parameters:
    ===========
    app: Flask "app" object.

    returns:
    =======
    Swagger object handler
    """
    template = {
      "swagger": "2.0",
      "info": {
        "title": "Document Processing API",
        "description": "API for processing documents to extract metadata information.",
        "contact": {
          "responsibleOrganization": "QuintilesIMS",
          "responsibleDeveloper": "Prathap Veera",
          "email": "prathap.veera@quintiles.com"
        },
        "version": "0.1"
      },
      "basePath": "/",  # base bash for blueprint registration
      "schemes": [
        "http",
        "https"
      ]
    }

    return Swagger(app, template=template)