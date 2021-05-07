# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=raise-missing-from
#
import html

from flask import Blueprint, jsonify, request, g, session
from flask_babel import _
from werkzeug.exceptions import BadRequest

from manager.auth import login_required, admin_required
from manager.log import get_log
from manager.ldap import get_ldap
from manager.otrs import create_ticket, ticket_url
from manager.apikey import get_apikeys, add_apikey, delete_apikey
from manager.component import get_components, add_component, delete_component
from manager.burst import get_bursts, update_bursts, set_ticket, Burst
from manager.template import Template
from manager.exceptions import ImpossibleException, ResourceNotFound, BadCall, AppException, LdapException
from manager.event import get_burst_events

bp = Blueprint('ajax', __name__, url_prefix='/xhr')

# ---------------------------------------------------------------------------
#                                                          DATABASE HELPERS
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
#                                                                   HELPERS
# ---------------------------------------------------------------------------

def _bursts_by_cluster():
  """
  Convert dict returned by get_bursts(), which is keyed on a tuple and cannot
  be jsonified, and key by cluster instead.  Add display values such as
  claimant's name.
  """

  ldap = get_ldap()

  # bursts by cluster
  bbc = {}

  # bursts by cluster and epoch
  bbce = get_bursts()

  # simplify to bursts by cluster
  if bbce:
    for ce, bursts in bbce.items():
      cluster = ce[0]
      epoch = ce[1]
      if cluster in bbc:
        # if this happens, then the data structure returned by get_bursts()
        # is semantically broken; probably because somehow two different
        # epochs were returned for the same cluster.
        raise ImpossibleException("Cluster reported twice in get_bursts()")

      bbc[cluster] = {}
      bbc[cluster]['epoch'] = epoch

      # serialize bursts individually so as to add attributes
      bbc[cluster]['bursts'] = []
      for burstObj in bursts:
        burst = burstObj.serialize()

        # add claimant's name
        cci = burst['claimant']
        if cci:
          person = ldap.get_person_by_cci(cci)
          if not person:
            get_log().error("Could not find name for cci '%s'", burst['claimant'])
            prettyname = cci
          else:
            prettyname = person['givenName']
          burst['claimant_pretty'] = prettyname

        # add ticket URL if there's a ticket
        if burstObj.ticket_id:
          burst['ticket_href'] = "<a href='{}' target='_ticket'>{}</a>".format(
            ticket_url(burstObj.ticket_id), burstObj.ticket_no)
        else:
          burst['ticket_href'] = None

        # add any prettified fields
        burst['state_pretty'] = _(str(burstObj.state))
        burst['resource_pretty'] = _(str(burstObj.resource))

        bbc[cluster]['bursts'].append(burst)
  return bbc

def _get_project_pi(account):

  # initialize
  ldap = get_ldap()

  # look up project
  project = ldap.get_project(account)
  if not project:
    error = "Could not find project {}".format(account)
    raise LdapException(error)

  # look up PI
  pi = ldap.get_person_by_cci(project['ccResponsible'], ['ccPrimaryEmail'])
  if not pi:
    error = "Could not lookup PI {} for project {}".format(project['ccResponsible'], project)
    raise LdapException(error)

  # extract PI information
  try:
    return {
      'language': pi['preferredLanguage'],
      'uid': pi['uid'],
      'email': pi['ccPrimaryEmail'][0],
      'givenName': pi['givenName']
    }
  except KeyError:
    error = "Incomplete information for PI {}".format(project['ccResponsible'])
    raise LdapException(error)

def _render_template(template, burstID):

  # retrieve burst object and info
  burst = Burst(burstID)
  burst_info = burst.info

  try:
    pi = _get_project_pi(burst.account)
  except Exception as e:
    raise LdapException("Could not lookup PI: {}".format(e))

  # determine templates to use
  title_template = template + " title"

  # set up values for template substitutions
  template_values = dict({
    'piName': pi['givenName'],
    'analyst': session['givenName'],
  }, **burst_info)

  # parametrize templates
  try:
    title = Template(title_template, pi['language']).render(values=template_values)
    body = Template(template, pi['language']).render(values=template_values)
  except ResourceNotFound as e:
    error = "Could not find template: {}".format(e)
    raise ResourceNotFound(error)

  return {
    'title': title,
    'body': body
  }

# ---------------------------------------------------------------------------
#                                                   ROUTES - authorizations
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
#                                                         ROUTES - API keys
# ---------------------------------------------------------------------------

@bp.route('/apikeys/', methods=('GET',))
@admin_required
def xhr_get_apikeys():

  access_keys = get_apikeys(pretty=True)
  return jsonify(access_keys)


@bp.route('/apikeys/', methods=('POST',))
@admin_required
def xhr_add_apikey():

  access = request.form['apikey_name']
  secret = request.form['apikey']
  component = request.form['component']
  get_log().debug("Adding API key (%s)", access)
  try:
    add_apikey(access, secret, component)
  except Exception as e:
    get_log().error(
      "Exception in adding API key (%s=%s for component %s): %s",
      access, secret, component, e)
    return None
  return jsonify({'status': 'OK'}), 200


@bp.route('/apikeys/<string:access>', methods=('DELETE',))
@admin_required
def xhr_delete_apikey(access):

  get_log().debug("Deleting API key: %s", access)
  try:
    delete_apikey(access)
  except Exception as e:
    get_log().error("Exception in deleting API key: %s", e)
    return jsonify({'error': 'error'}), 500

  return jsonify({'status': 'OK'}), 200

# ---------------------------------------------------------------------------
#                                                           ROUTES - bursts
# ---------------------------------------------------------------------------

@bp.route('/bursts/', methods=['GET'])
@login_required
def xhr_get_bursts():
  return jsonify(_bursts_by_cluster())

@bp.route('/bursts/', methods=['PATCH'])
@login_required
def xhr_update_bursts():

  # parse request
  try:
    data = request.get_json()
  except BadRequest as e:
    get_log().error("Could not parse request data: %s", e)
    return jsonify({'error': str(e)}), 400

  # sanitize any strings
  for item in data:
    for (key, val) in item.items():
      if isinstance(val, str):
        sanitized = html.escape(val)
        if val != sanitized:
          item[key] = sanitized
          get_log().info("Client tried to send in HTML for key %s: '%s'",
            key, sanitized)

  try:
    update_bursts(data, user=g.user['cci'])
  except BadCall as e:
    get_log().info("Client error: %s", e)
    return jsonify({'error': str(e)}), 400
  except AppException as e:
    get_log().error(e)
    return jsonify({'error': str(e)}), 500
  except Exception as e:
    get_log().error(e)
    return jsonify({'error': str(e)}), 500

  try:
    return jsonify(_bursts_by_cluster())
  except Exception as e:
    get_log().error(e)
    return jsonify({'error': str(e)}), 500

@bp.route('/bursts/<int:id>/events/', methods=['GET'])
@login_required
def xhr_get_burst_events(id):

  get_log().debug("Retrieving events for burst %d", id)
  events = get_burst_events(id)
  return jsonify(events), 200

# ---------------------------------------------------------------------------
#                                                          ROUTES - templates
# ---------------------------------------------------------------------------

@bp.route('/templates/<string:name>', methods=['GET'])
@login_required
def xhr_get_template(name):

  get_log().debug("In xhr_get_template(%s)", name)

  # get request data, if available
  if 'burst_id' in request.args:
    # get burst information
    burst_id = int(request.args['burst_id'])

    # render template with burst and account information
    try:
      return jsonify(_render_template(name, burst_id)), 200
    except AppException as e:
      get_log().error(e)
      return jsonify({'error': str(e)}, 500)

  if session.get('admin'):
    # TODO: implement for admin dashboard
    return jsonify({'error': 'Not implemented'}), 501

  return jsonify({'error': 'Forbidden'}), 403

# ---------------------------------------------------------------------------
#                                                          ROUTES - tickets
# ---------------------------------------------------------------------------

@bp.route('/tickets/', methods=['POST'])
@login_required
def xhr_create_ticket():

  # get request data
  try:
    burst_id = int(request.form['burst_id'])
    title = request.form['title']
    body = request.form['body']
  except KeyError:
    error = "Missing required request parameter"
    get_log().error(error)
    return jsonify({'error': error}), 400

  # get burst
  burst = Burst(burst_id)
  account = burst.account

  # get PI
  pi = _get_project_pi(account)

  get_log().debug("About to create ticket with title '%s', PI %s, to e-mail %s",
    title, pi['uid'], pi['email'])

  # create ticket via OTRS
  ticket = create_ticket(title, body, g.user['id'], pi['uid'], pi['email'])
  if not ticket:
    error = "Unable to create ticket"
    get_log().error(error)
    return jsonify({'error': error}), 500
  get_log().info("Ticket created for burst %d on account %s.  Details: %s",
     burst_id, account, ticket)

  # register the ticket with the burst candidate
  set_ticket(burst_id, ticket['ticket_id'], ticket['ticket_no'])

  return jsonify(dict({
    'burst_id': burst_id,
    'url': ticket_url(ticket['ticket_id'])
  }, **ticket))

# ---------------------------------------------------------------------------
#                                          ROUTES - clusters and components
# ---------------------------------------------------------------------------

@bp.route('/components/', methods=('GET',))
@admin_required
def xhr_get_components():

  return jsonify(get_components(get_last_heard=True))

@bp.route('/components/', methods=('POST',))
@admin_required
def xhr_add_component():

  name = request.form['name']
  cluster = request.form['cluster']
  service = request.form['service']
  id = cluster + '_' + service

  get_log().debug("Adding component (%s)", id)
  try:
    add_component(id, name, cluster, service)
  except Exception as e:
    get_log().error(
      "Exception in adding component %s (%s)", id, e)
    return None
  return jsonify({'status': 'OK'}), 200


@bp.route('/components/<string:id>', methods=('DELETE',))
@admin_required
def xhr_delete_component(id):

  get_log().debug("Deleting component %s", id)
  try:
    delete_component(id)
  except Exception as e:
    get_log.error("Exception in deleting component: %s", e)

    # I cannot figure out how to respond in such a way that indicates error, except
    # not to respond at all.  Have not tried using 4xx HTTP response status because
    # that is not necessarily appropriate
    #return jsonify({'status': 'error'}), 200
    return None

  return jsonify({'status': 'OK'}), 200

# ---------------------------------------------------------------------------
#                                               ROUTES - site configuration
# ---------------------------------------------------------------------------
