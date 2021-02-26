# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
from flask import Blueprint
from manager.db import get_schema_version, upgrade_schema
from manager.ldap import get_ldap
from manager import exceptions


# establish blueprint
bp = Blueprint('status', __name__, url_prefix='/status')

# ---------------------------------------------------------------------------
#                                                                    HELPERS
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
#                                                                     ROUTES
# ---------------------------------------------------------------------------

@bp.route('/', methods=['GET'])
def get_status():

  statuses = []
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

  # get schema version from database
  try:
    (actual, expected) = get_schema_version()
  except Exception as e:
    statuses.append("DB: {}".format(e))
    status = 500
  else:
    if actual == expected:
      statuses.append("DB: Okay (schema version {})".format(actual))
    else:
      statuses.append("DB: Schema version mismatch: {}, expected {}".format(actual, expected))
      status = 500

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
