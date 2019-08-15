from flask_restplus import Api
from flask import url_for

@property
def specs_url(self):
    """Fixes issue where swagger-ui makes a call to swagger.json over HTTP.
       This can ONLY be used on servers that actually use HTTPS.  On servers that use HTTP,
       this code should not be used at all.
    """
    return url_for(self.endpoint('specs'), _external=True, _scheme='https')


api = Api(version='0.1', 
	    title='eTMF Automation Service API',
	    description='eTMF Automation Service API for document processing.',
	    contact="prathap.veera@quintiles.com"
    )
