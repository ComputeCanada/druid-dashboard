# add application to Python path.  If done in wsgi call, will be prepended and
# mess up import of system ldap library over application's ldap module
import sys
sys.path.append('manager/')

# create app object invoked by wsgi
from manager import create_app
app = create_app()
