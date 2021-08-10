# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
from flask import Blueprint
from manager.db import get_schema_version, upgrade_schema
from manager.ldap import get_ldap
from manager.otrs import get_otrs
from manager import exceptions


# establish blueprint
bp = Blueprint('status', __name__, url_prefix='/status')

# ---------------------------------------------------------------------------
#                                                                    HELPERS
# ---------------------------------------------------------------------------

def _check_status_app(statuses):

  # this is trivial
  statuses.append("I'm: Okay")
  return 200

def _check_status_db(statuses):

  status = 200

  # get schema version from database
  try:
    (actual, expected) = get_schema_version()
  except Exception as e:
    statuses.append("DB: Caught exception: {}".format(str(e).rstrip()))
    status = 500
  else:
    if actual == expected:
      statuses.append("DB: Okay (schema version {})".format(actual))
    else:
      statuses.append("DB: Schema version mismatch: {}, expected {}".format(actual, expected))
      status = 500

  return status

def _check_status_ldap(statuses):

  status = 200

  # try to get an LDAP record
  try:
    canary = get_ldap().get_person('ldapcanary')
  except Exception as e:
    statuses.append("LDAP: {}".format(e))
    status = 500
  else:
    if not canary:
      statuses.append("LDAP: Basic query failed")
      status = 500
    else:
      statuses.append("LDAP: Okay")

  return status

def _check_status_otrs(statuses):

  status = 200

  # test we have an OTRS client
  otrs = get_otrs()
  if otrs is None:
    statuses.append("OTRS: could not create client session")
    status = 500
  else:
    statuses.append("OTRS: Okay")

  return status

# ---------------------------------------------------------------------------
#                                                                     ROUTES
# ---------------------------------------------------------------------------

@bp.route('/', methods=['GET'])
def get_status():
  """
  Reports app health apart from external dependencies.  This is so limited
  in order that it can be used as a liveness probe in Kubernetes.  Failing
  this would then result in restarts of the container, and basing that on
  the connections to LDAP, OTRS, etc. does not make sense.
  """

  statuses = []
  status = 200

  # run some tests
  status = _check_status_app(statuses)

  status_all = "\n".join(statuses)
  return status_all, status, {'Content-type': 'text/plain; charset=utf-8'}

@bp.route('/services/ldap', methods=['GET'])
def get_services_status_ldap():

  statuses = []
  status = 200

  status = max(status, _check_status_ldap(statuses))

  status_all = "\n".join(statuses)
  return status_all, status, {'Content-type': 'text/plain; charset=utf-8'}

@bp.route('/services/otrs', methods=['GET'])
def get_services_status_otrs():

  statuses = []
  status = 200

  status = max(status, _check_status_otrs(statuses))

  status_all = "\n".join(statuses)
  return status_all, status, {'Content-type': 'text/plain; charset=utf-8'}

@bp.route('/services/db', methods=['GET'])
def get_services_status_db():

  statuses = []
  status = 200

  status = max(status, _check_status_db(statuses))

  status_all = "\n".join(statuses)
  return status_all, status, {'Content-type': 'text/plain; charset=utf-8'}

@bp.route('/services', methods=['GET'])
def get_services_status():

  statuses = []
  status = 200

  status = max(status, _check_status_ldap(statuses))
  status = max(status, _check_status_db(statuses))
  status = max(status, _check_status_otrs(statuses))

  status_all = "\n".join(statuses)
  return status_all, status, {'Content-type': 'text/plain; charset=utf-8'}

# Use as a startup probe.  Will check DB schema version and update if necessary.
@bp.route('/db', methods=['GET'])
def update_db():
  try:
    (actual, expected, actions) = upgrade_schema()
    if actions:
      status_text = "DB required upgrade from {} to {}\n{}".format(
        actual, expected, "\n".join(actions))
    else:
      status_text = "DB schema at {}, code schema at {}, no action taken".format(actual, expected)
    status_code = 200
  except exceptions.ImpossibleSchemaUpgrade as e:
    status_text = str(e)
    status_code = 500

  return status_text, status_code, {'Content-type': 'text/plain; charset=utf-8'}
