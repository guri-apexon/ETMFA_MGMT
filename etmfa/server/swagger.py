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
        "title": "Document Translation API",
        "description": "API for translating documents between source and target languages.",
        "contact": {
          "responsibleOrganization": "QuintilesIMS",
          "responsibleDeveloper": "Joseph Munoz",
          "email": "joseph.munoz@quintiles.com"
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