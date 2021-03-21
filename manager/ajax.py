# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#

from flask import Blueprint, jsonify, request, g
from flask_babel import _

from manager.auth import login_required, admin_required
from manager.log import get_log
from manager.ldap import get_ldap
from manager.otrs import create_ticket, ticket_url
from manager.apikey import get_apikeys, add_apikey, delete_apikey
from manager.component import get_components, add_component, delete_component
from manager.burst import get_bursts, update_burst_states, State, set_ticket
from manager.exceptions import ImpossibleException


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
        if burstObj.state == State.CLAIMED:
          cci = burst['claimant']
          person = ldap.get_person_by_cci(burst['claimant'])
          if not person:
            get_log().error("Could not find name for cci '%s'", burst['claimant'])
            prettyname = cci
          else:
            prettyname = person['givenName']
          burst['claimant_pretty'] = prettyname

        # add ticket URL there's a ticket
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
    get_log.error("Exception in deleting API key: %s", e)

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
  data = request.get_json()
  update_burst_states(data)
  return jsonify(_bursts_by_cluster())

# ---------------------------------------------------------------------------
#                                                          ROUTES - tickets
# ---------------------------------------------------------------------------

@bp.route('/tickets/', methods=['POST'])
@login_required
def xhr_create_ticket():

  # get request data
  burst_id = request.form['burst_id']
  account = request.form['account']
  submitters = request.form.get('submitters', [])

  # lookup PI's username
  ldap = get_ldap()
  project = ldap.get_project(account)
  if not project:
    raise Exception("TODO: better handling of missing project")
  pi = ldap.get_person_by_cci(project['ccResponsible'])

  # lookup e-mails for the users
  CCs = []
  for user in submitters:
    userrec = ldap.get_person(user)
    if not userrec:
      get_log().error("Burst record lists job submitter not found in LDAP: %s", user)
    else:
      CCs.append(userrec['ccPrimaryEmail'])

  # TODO: store template in database
  body = "We've noticed you've got a potential burst happening.  Yo."

  # create ticket via OTRS
  deets = create_ticket('Potential for bursting', body, g.user['id'], pi['uid'], CCs=CCs)
  if not deets:
    get_log().error("Could not create ticket")
    return jsonify({'error': 'dang'}), 500
  get_log().debug("Ticket created.  Deets: %s", deets)

  # register the ticket with the burst candidate
  set_ticket(burst_id, deets['ticket_id'], deets['ticket_no'])

  return jsonify({
    'burst_id': burst_id,
    'ticket_id': deets['ticket_id'],
    'ticket_no': deets['ticket_no'],
    'url': ticket_url(deets['ticket_id'])
  })

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
