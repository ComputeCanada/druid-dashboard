# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=raise-missing-from
#
import html

from flask import Blueprint, jsonify, request, g, session
from werkzeug.exceptions import BadRequest

from manager.auth import login_required, admin_required
from manager.log import get_log
from manager.ldap import get_ldap
from manager.otrs import create_ticket, ticket_url
from manager.apikey import get_apikeys, add_apikey, delete_apikey
from manager.cluster import Cluster, get_clusters
from manager.component import get_components, add_component, delete_component
from manager.burst import update_bursts, set_ticket, Burst
from manager.template import Template
from manager.exceptions import ResourceNotFound, BadCall, AppException, LdapException, DatabaseException
from manager.event import get_burst_events
from manager.reporter import registry

bp = Blueprint('ajax', __name__, url_prefix='/xhr')

# ---------------------------------------------------------------------------
#                                                          DATABASE HELPERS
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
#                                                                   HELPERS
# ---------------------------------------------------------------------------

# Response wrappers for REST calls.
# See RFC 7807 (https://datatracker.ietf.org/doc/html/rfc7807)
def xhr_response(status, msg, *args, title=None):
  response = { 'status': status }
  if msg:
    response['detail'] = msg % args
  if title:
    response['title'] = title
  return jsonify(response), status

def xhr_error(status, msg, *args, title=None):
  response = { 'status': status }
  if msg:
    if args:
      #get_log().error(msg, args)
      response['detail'] = msg % args
    else:
      get_log().error(msg)
      response['detail'] = msg
  if title:
    response['title'] = title
  return jsonify(response), status
  # TODO: figure out why I couldn't swap the above with:
  #return xhr_response(status, msg, args, title)
  # ...it's something to do about args being reinterpreted or augmented

def xhr_success(status=200, title=None):
  response = { 'status': status }
  if title:
    response['title'] = title
  return jsonify(response), status

# Given dict and a list of keys, returns list of any keys not occurring in
# dict.
def _must_have(dct, keys):
  missing = [
    key
    for key in keys if key not in dct
  ]
  return missing or None

def _reports_by_cluster(cluster):
  """
  Collect reports available for given cluster.
  """

  # trivial response structure
  reports = {
    'cluster': cluster
  }

  # add reports
  for name, reporter in registry.reporters.items():
    get_log().debug("Getting view from %s reporter", name)
    report = reporter.view({'cluster':cluster})
    if report:
      reports[name] = report

  return reports

# def _bursts_by_cluster():
#   """
#   Convert dict returned by get_bursts(), which is keyed on a tuple and cannot
#   be jsonified, and key by cluster instead.  Add display values such as
#   claimant's name.
#   """

#   ldap = get_ldap()

#   # bursts by cluster
#   bbc = {}

#   # bursts by cluster and epoch
#   bbce = get_bursts()

#   # simplify to bursts by cluster
#   if bbce:
#     for ce, bursts in bbce.items():
#       cluster = ce[0]
#       epoch = ce[1]
#       if cluster in bbc:
#         # if this happens, then the data structure returned by get_bursts()
#         # is semantically broken; probably because somehow two different
#         # epochs were returned for the same cluster.
#         raise ImpossibleException("Cluster reported twice in get_bursts()")

#       bbc[cluster] = {}
#       bbc[cluster]['epoch'] = epoch

#       # serialize bursts individually so as to add attributes
#       bbc[cluster]['bursts'] = []
#       for burstObj in bursts:
#         burst = burstObj.serialize()

#         # add claimant's name
#         cci = burst['claimant']
#         if cci:
#           person = ldap.get_person_by_cci(cci)
#           if not person:
#             get_log().error("Could not find name for cci '%s'", burst['claimant'])
#             prettyname = cci
#           else:
#             prettyname = person['givenName']
#           burst['claimant_pretty'] = prettyname

#         # add ticket URL if there's a ticket
#         if burstObj.ticket_id:
#           burst['ticket_href'] = "<a href='{}' target='_ticket'>{}</a>".format(
#             ticket_url(burstObj.ticket_id), burstObj.ticket_no)
#         else:
#           burst['ticket_href'] = None

#         # add any prettified fields
#         burst['state_pretty'] = _(str(burstObj.state))
#         burst['resource_pretty'] = _(str(burstObj.resource))

#         bbc[cluster]['bursts'].append(burst)
#   return bbc

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

def _render_template(template, burstID, recipient=None):

  # retrieve burst object and info
  burst = Burst(burstID)
  burst_info = burst.info

  # use requested recipient if provided
  if recipient:
    userrec = get_ldap().get_person(recipient, ['ccPrimaryEmail'])
    if not userrec:
      raise LdapException("Could not lookup recipient {}".format(recipient))
    try:
      email = userrec['ccPrimaryEmail'][0]
      givenName = userrec['givenName']
      language = userrec['preferredLanguage']
    except KeyError:
      raise LdapException("Could not find e-mail, given name and/or language for recipient {}".format(recipient))
  else:    # get PI
    pi = _get_project_pi(burst.account)

    recipient = pi['uid']
    email = pi['email']
    givenName = pi['givenName']
    language = pi['language']

  # determine templates to use
  title_template = template + " title"

  # set up values for template substitutions
  template_values = dict({
    'pi': recipient,
    'piName': givenName,
    'email': email,
    'analyst': session['givenName'],
  }, **burst_info)

  # parametrize templates
  try:
    title = Template(title_template, language).render(values=template_values)
    body = Template(template, language).render(values=template_values)
  except ResourceNotFound as e:
    error = "Could not find template: {}".format(e)
    raise ResourceNotFound(error)

  return dict({
    'recipient': recipient,
    'email': email,
    'title': title,
    'body': body,
  }, **template_values)

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
#                                                         ROUTES - clusters
# ---------------------------------------------------------------------------

@bp.route('/clusters/', methods=['GET'])
@login_required
def xhr_get_clusters():
  return jsonify(get_clusters())

@bp.route('/clusters/<string:id>', methods=['GET'])
@login_required
def xhr_get_cluster(id):
  try:
    return jsonify(Cluster(id=id))
  except ResourceNotFound as e:
    return xhr_error(404, str(e))

@bp.route('/clusters/', methods=['POST'])
@admin_required
def xhr_create_clusters():
  missing_args = _must_have(request.form, ['id', 'name'])
  if missing_args:
    return xhr_error(400,
      "Must specify %s when creating cluster", ', '.join(missing_args))

  id = request.form['id']
  name = request.form['name']

  try:
    Cluster(id=id, name=name)
  except DatabaseException:
    # TODO: This assumes the exception is a certain type of database error
    return xhr_error(400, "Could not create cluster record")

  return xhr_success(201)

# ---------------------------------------------------------------------------
#                                                       ROUTES - components
# ---------------------------------------------------------------------------

@bp.route('/components/', methods=('GET',))
@admin_required
def xhr_get_components():

  #components = get_components(get_last_heard=True)
  #print(components)
  #return jsonify(components), 200
  return jsonify(get_components(get_last_heard=True)), 200

@bp.route('/components/', methods=('POST',))
@admin_required
def xhr_add_component():

  missing_args = _must_have(request.form, ['name', 'cluster', 'service'])
  if missing_args:
    return xhr_error(400,
      "Must specify %s when creating component", ', '.join(missing_args))

  name = request.form['name']
  cluster = request.form['cluster']
  service = request.form['service']
  id = request.form.get('id', cluster + '_' + service)

  get_log().debug("Adding component (%s)", id)
  try:
    add_component(id, name, cluster, service)
  except Exception as e:
    return xhr_error(400, "Unable to add component %s: %s", id, e)
  return xhr_success(200)

@bp.route('/components/<string:id>', methods=('DELETE',))
@admin_required
def xhr_delete_component(id):

  get_log().debug("Deleting component %s", id)
  try:
    delete_component(id)
  except Exception as e:
    # TODO: Need to differentiate between 400 (unknown component?) or 500
    # (database failure)
    return xhr_error(404, "Exception in deleting component: %s", e)

  return xhr_success(200)

# ---------------------------------------------------------------------------
#                                                           ROUTES - bursts
# ---------------------------------------------------------------------------

@bp.route('/reports/', methods=['GET'])
@login_required
def xhr_get_bursts():
  if 'cluster' not in request.args:
    get_log().error("No cluster specified when requesting reporsts")
    return jsonify({'error': 'error'}), 400
  # get cluster information
  cluster = request.args['cluster']
  return jsonify(_reports_by_cluster(cluster))

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
    # TODO: Require cluster name in update, or needs to return just the
    # updated reportable
    return jsonify(_reports_by_cluster('TODO: I have no cluster name'))
  except Exception as e:
    get_log().error(e)
    return jsonify({'error': str(e)}), 500

@bp.route('/bursts/<int:id>/events/', methods=['GET'])
@login_required
def xhr_get_burst_events(id):

  get_log().debug("Retrieving events for burst %d", id)
  events = get_burst_events(id)
  return jsonify(events), 200

@bp.route('/bursts/<int:id>/people/', methods=['GET'])
@login_required
def xhr_get_burst_people(id):

  get_log().debug("Retrieving people involved in burst %d", id)
  burst = Burst(id)

  # get PI
  try:
    pi = _get_project_pi(burst.account)
  except LdapException as e:
    get_log().error("Error in retrieving PI for account %s: %s", burst.account, e)
    return jsonify({'error': 'Error in retrieving PI information'}), 500

  return jsonify(dict({
    'pi': pi['uid'],
    'submitters': burst.submitters
    })), 200

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

    # if recipient specified
    recipient = request.args.get('recipient', None)

    # render template with burst and account information
    try:
      data = _render_template(name, burst_id, recipient)
      return jsonify(data), 200
    except LdapException as e:
      get_log().error("Error in rendering template: %s", e)
      return jsonify({'error': str(e)}), 500

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
    recipient = request.form['recipient']
    email = request.form['email']
  except KeyError:
    error = "Missing required request parameter"
    get_log().error(error)
    return jsonify({'error': error}), 400

  # get burst
  burst = Burst(burst_id)
  account = burst.account

  get_log().debug("About to create ticket with title '%s', recipient %s, to e-mail %s",
    title, recipient, email)

  ## testing
  #return jsonify({'error': "I don't wanna"}), 501

  # create ticket via OTRS
  ticket = create_ticket(title, body, g.user['id'], recipient, email)
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
#                                               ROUTES - site configuration
# ---------------------------------------------------------------------------
