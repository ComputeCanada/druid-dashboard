# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=raise-missing-from
#
import html

from flask import Blueprint, jsonify, request, g, session
from werkzeug.exceptions import BadRequest

from manager.auth import login_required, admin_required
from manager.log import get_log
from manager.ldap import get_ldap
from manager.errors import xhr_error, xhr_success
from manager.otrs import create_ticket, ticket_url
from manager.apikey import get_apikeys, add_apikey, delete_apikey
from manager.cluster import Cluster, get_clusters
from manager.component import get_components, add_component, delete_component
from manager.template import Template
from manager.exceptions import ResourceNotFound, BadCall, AppException, LdapException, ResourceNotCreated
from manager.history import History
from manager.case import Case, registry
from manager.i18n import get_locale

bp = Blueprint('ajax', __name__, url_prefix='/xhr')

# ---------------------------------------------------------------------------
#                                                          DATABASE HELPERS
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
#                                                                   HELPERS
# ---------------------------------------------------------------------------

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
  get_log().debug("Starting to look through reports for cluster %s", cluster)
  for name, reporter in registry.reporters.items():
    get_log().debug("Getting view from %s reporter", name)
    report = reporter.view({'cluster':cluster, 'pretty': True})
    if report:
      reports[name] = report

  return reports

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

def _render_template(template, caseID, recipient=None):

  # retrieve case object and info
  case = Case.get(caseID)
  info = case.info

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
    pi = _get_project_pi(case.account)

    recipient = pi['uid']
    email = pi['email']
    givenName = pi['givenName']
    language = pi['language']

  # set up values for template substitutions
  template_values = dict({
    'pi': recipient,
    'piName': givenName,
    'email': email,
    'analyst': session['givenName'],
  }, **info)

  # retrieve and render template
  try:
    template = Template(template, language)
    template.render(template_values)
  except ResourceNotFound as e:
    error = "Could not find template: {}".format(e)
    raise ResourceNotFound(error)

  return dict({
    'recipient': recipient,
    'email': email,
    'title': template.title,
    'body': template.body,
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
  except ResourceNotCreated:
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
  except ResourceNotFound as e:
    return xhr_error(404, "Did not find component with ID %s (%s)", id, e)

  return xhr_success(200)

# ---------------------------------------------------------------------------
#                                                           ROUTES - cases
# ---------------------------------------------------------------------------

@bp.route('/cases/', methods=['GET'])
@login_required
def xhr_get_cases():
  get_log().debug("Retrieving cases")
  if 'cluster' not in request.args:
    return xhr_error(400, "No cluster specified when requesting reports")

  # get cluster information
  cluster = request.args['cluster']
  return jsonify(_reports_by_cluster(cluster))

@bp.route('/cases/<int:id>', methods=['GET'])
@login_required
def xhr_get_case(id):
  """
  Return detailed information about a case.
  """
  get_log().debug("In xhr_get_case(%d)", id)

  # load appropriate case record
  case = Case.get(id)
  if not case:
    return xhr_error(404, f"Could not find case with ID {id}")

  # get info
  info = case.info

  # get PI
  try:
    info['pi'] = _get_project_pi(case.account)
  except LdapException as e:
    get_log().error("Error in retrieving PI for account %s: %s", case.account, e)
    return jsonify({'error': 'Error in retrieving PI information'}), 500

  # get outreach templates appropriate for this case.  Use 'en' if nothing
  # found
  info['templates'] = case.appropriate_templates(get_locale() or 'en')

  return jsonify(info), 200

@bp.route('/cases/<int:id>', methods=['PATCH'])
@login_required
def xhr_update_case(id):

  get_log().debug("In xhr_update_case(%d)", id)

  # parse request
  try:
    data = request.get_json()
  except BadRequest as e:
    return xhr_error(400, "Could not parse request data: %s", e)

  # verify/validate/sanitize individual updates
  # note: For historical reasons this is an array although current UI workflow
  #       does not support this.  Since both the client-side JS and this code
  #       work together already there doesn't seem to be much reason to
  #       update anything.
  updates = []
  for item in data:

    # sanitize any strings
    for (key, val) in item.items():
      if isinstance(val, str):
        sanitized = html.escape(val)
        if val != sanitized:
          item[key] = sanitized
          get_log().info("Client tried to send in HTML for key %s: '%s'",
            key, sanitized)

    # verify/fill in as necessary
    verified = False
    update = {}
    for k, v in item.items():
      if k == 'note':
        update[k] = v
        verified = True
      elif k == 'timestamp':
        update[k] = v
      else:
        if k == 'claimant' and v == '':
          v = g.user['cci']
        update['datum'] = k
        update['value'] = v
        verified = True

    if not verified:
      return xhr_error(400, "Update requests require note and/or key value")

    updates.append(update)

  try:
    case = Case.get(id)
    if not case:
      return xhr_error(404, f"Could not find case with ID {id}")
    for item in updates:
      get_log().debug("Updating case %d with datum = %s, value = %s, note = %s", id,
        item.get('datum', '<blank>'), item.get('value', '<blank>'), item.get('note', '<blank>'))
      case.update(item, g.user['cci'])
  except BadCall as e:
    return xhr_error(400, "Client error: %s", e)
  except AppException as e:
    return xhr_error(500, "Application error: %s", e)
  except Exception as e:
    return xhr_error(500, "Unexpected exception: %s", e)

  try:
    # TODO: Would be better to just return the updated reportable
    return jsonify(_reports_by_cluster(case.cluster))
  except Exception as e:
    return xhr_error(500, "Could not get update information: %s", str(e))

@bp.route('/cases/<int:id>/events/', methods=['GET'])
@login_required
def xhr_get_case_events(id):

  get_log().debug("Retrieving events for case %d", id)
  events = History.get_events(id)
  return jsonify(events), 200

# ---------------------------------------------------------------------------
#                                                          ROUTES - templates
# ---------------------------------------------------------------------------

@bp.route('/templates/', methods=['GET'])
@login_required
def xhr_get_templates():

  get_log().debug("In xhr_get_templates()")

  # TODO

@bp.route('/templates/<string:name>', methods=['GET'])
@login_required
def xhr_get_template(name):

  get_log().debug("In xhr_get_template(%s)", name)

  # get request data, if available
  if 'case_id' in request.args:
    # get case information
    case_id = int(request.args['case_id'])

    # if recipient specified
    recipient = request.args.get('recipient', None)

    # render template with burst and account information
    try:
      data = _render_template(name, case_id, recipient)
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
    case_id = int(request.form['case_id'])
    title = request.form['title']
    body = request.form['body']
    recipient = request.form['recipient']
    email = request.form['email']
  except KeyError:
    error = "Missing required request parameter"
    get_log().error(error)
    return jsonify({'error': error}), 400

  # get burst
  case = Case.get(case_id)
  if not case:
    return xhr_error(404, f"Could not find case with ID {id}")
  account = case.account

  get_log().debug("About to create ticket with title '%s', recipient %s, to e-mail %s",
    title, recipient, email)

  # create ticket via OTRS
  ticket = create_ticket(title, body, g.user['id'], recipient, email)
  if not ticket:
    error = "Unable to create ticket"
    get_log().error(error)
    return jsonify({'error': error}), 500
  get_log().info("Ticket created for case %d on account %s.  Details: %s",
     case_id, account, ticket)

  # register the ticket with the case candidate
  Case.set_ticket(case_id, ticket['ticket_id'], ticket['ticket_no'])

  return jsonify(dict({
    'case_id': case_id,
    'url': ticket_url(ticket['ticket_id'])
  }, **ticket))


# ---------------------------------------------------------------------------
#                                               ROUTES - site configuration
# ---------------------------------------------------------------------------
