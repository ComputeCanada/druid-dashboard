# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
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
from manager.exceptions import ImpossibleException, ResourceNotFound, BadCall, AppException
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

    # I cannot figure out how to respond in such a way that indicates error, except
    # not to respond at all.  Have not tried using 4xx HTTP response status because
    # that is not necessarily appropriate
    #return jsonify({'status': 'error'}), 200
    return None

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
#                                                          ROUTES - tickets
# ---------------------------------------------------------------------------

@bp.route('/tickets/', methods=['POST'])
@login_required
def xhr_create_ticket():

  # get request data
  try:
    burst_id = int(request.form['burst_id'])
    account = request.form['account']
    template = request.form['template']
  except KeyError:
    error = "Missing required request parameter"
    get_log().error(error)
    return jsonify({'error': error}), 400

  submitters = request.form.getlist('submitters')

  # populate objects we'll need
  burst = Burst(id=burst_id)
  burst_info = burst.info

  # initialize
  ldap = get_ldap()

  # look up project
  project = ldap.get_project(account)
  if not project:
    error = "Could not find project {}".format(account)
    get_log().error(error)
    return jsonify({'error': error}), 500

  # look up PI
  pi = ldap.get_person_by_cci(project['ccResponsible'], ['ccPrimaryEmail'])
  if not pi:
    error = "Could not lookup PI {} for project {}".format(project['ccResponsible'], project)
    get_log().error(error)
    return jsonify({'error': error}), 500

  # extract PI information
  try:
    languages = [ pi['preferredLanguage'] ]
    pi_uid = pi['uid']
    pi_email = pi['ccPrimaryEmail'][0]
  except KeyError as e:
    error = "Incomplete information for PI {} for account {}.  Info: {}".format(project['ccResponsible'], account, pi)
    get_log().error(error)
    return jsonify({'error': error}), 500

  # lookup e-mails for the users
  CCs = []
  for user in submitters:
    userrec = ldap.get_person(user, ['ccPrimaryEmail'])
    if not userrec:
      get_log().error("Burst record lists job submitter not found in LDAP: %s", user)
      # TODO: flash user of error
    else:
      try:
        CCs.append(userrec['ccPrimaryEmail'][0])
      except KeyError:
        get_log().error("Could not retrieve ccPrimaryEmail for user %s; continuing without", user)
      else:
        l = userrec['preferredLanguage']
        if l not in languages:
          languages.append(l)

  # determine templates to use
  title_template = template + " title"

  # set up values for template substitutions
  template_values = dict({
    'piName': pi['givenName'],
    'analyst': session['givenName'],
  }, **burst_info)

  # build title and body from templates
  try:
    if len(languages) > 1:
      title = "{} / {}".format(
        Template(title_template, languages[0]).render(values=template_values),
        Template(title_template, languages[1]).render(values=template_values)
      )
      body = "{}\n{}\n{}\n{}".format(
        Template("other language follows", languages[1]).render(),
        Template(template, languages[0]).render(values=template_values),
        Template("separator").render(),
        Template(template, languages[1]).render(values=template_values)
      )
    else:
      title = Template(title_template, languages[0]).render(values=template_values)
      body = Template(template, languages[0]).render(values=template_values)
  except ResourceNotFound as e:
    error = "Could not find template: {}".format(e)
    get_log().error(error)
    return jsonify({'error': error}), 500

  get_log().debug("About to create ticket with title '%s', PI %s, to e-mail %s",
    title, pi_uid, pi_email)

  # create ticket via OTRS
  ticket = create_ticket(title, body, g.user['id'], pi_uid, pi_email, CCs=CCs)
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
