from flask import url_for
from flask_restplus import Api


@property
def specs_url(self):
    """Fixes issue where swagger-ui makes a call to swagger.json over HTTP.
       This can ONLY be used on servers that actually use HTTPS.  On servers that use HTTP,
       this code should not be used at all.
    """
    return url_for(self.endpoint('specs'), _external=True, _scheme='https')

authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-API-KEY'
    }
}

api = Api(version='0.1',
          title='PD Automation Service API',
          description='PD Automation Service API for document processing.',
          contact="jiju.mohan@quintiles.com",
          authorizations=authorizations
          )
