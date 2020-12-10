# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import ldap
from flask import current_app, g
from ccldap import ccldap
from app.log import get_log
from app.exceptions import LdapException

# LDAP options translation table
_ldap_opts = {
  'LDAP_TLS_REQCERT': (
    ldap.OPT_X_TLS_REQUIRE_CERT,
    {
      'never':  ldap.OPT_X_TLS_NEVER,
      'allow':  ldap.OPT_X_TLS_ALLOW,
      'try':    ldap.OPT_X_TLS_TRY,
      'demand': ldap.OPT_X_TLS_DEMAND
    }
  )
}


def _translate_options(config):
  """
  Translate options given in application configuration to LDAP options
  understood by the ccldap module and the LDAP client library.

  args:
    config (map): configuration items from app initialization

  returns:
    map: key-value pairs of LDAP options understood by python-ldap.
  """

  f = lambda x: (
    x.startswith('LDAP_')
    and x not in ('LDAP_BINDDN', 'LDAP_PASSWORD', 'LDAP_URI', 'LDAP_SKIP_TLS',
                  'LDAP_STUB')
  )

  options = {}
  try:
    for key in filter(f, config):
      options[_ldap_opts[key][0]] = _ldap_opts[key][1][config[key]]
  except KeyError as e:
    # pylint: disable=W0707
    # ...because I don't want to have the traceback of this expected exception
    raise LdapException("Bad LDAP option: '%s'" % (e.args[0],))

  return options


def get_ldap():
  if 'ldap' not in g:

    options = _translate_options(current_app.config)

    if current_app.config.get('LDAP_STUB'):
      g.ldap = current_app.config['LDAP_STUB']
    else:
      try:
        ldapconn = ccldap.CCLdap(
          current_app.config['LDAP_BINDDN'],
          current_app.config['LDAP_PASSWORD'],
          current_app.config['LDAP_URI'],
          insecure_skip_tls=current_app.config['LDAP_SKIP_TLS'],
          options=options
        )
      except ldap.INVALID_CREDENTIALS as e:
        get_log().critical('Could not connect to LDAP: invalid credentials')
        get_log().debug(e)
        raise LdapException("Invalid credentials") from e
      except Exception as e:
        get_log().critical('Could not connect to LDAP')
        get_log().debug(e)
        raise LdapException("Could not connect to LDAP server") from e
      g.ldap = ldapconn
  return g.ldap

def close_ldap(e=None):
  if e:
    get_log().info("LDAP connection will be dropped in presence of error condition: '%s'", e)

  # On deletion of LDAPObject the connection is automatically unbound and
  # closed, so no explicit close() message needs to be sent.
