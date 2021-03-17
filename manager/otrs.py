# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#

# TODO: use this instead of Exception in get_otrs()--but wasn't
# getting caught
#from requests import HTTPError
import pyotrs
from flask import g, current_app
from manager.log import get_log


def get_otrs():
  """
  Note: Does not throw exception if OTRS cannot be contacted, because app
        should not depend on OTRS being up to function.  So client should
        check whether returned handle is None or not before attempting to
        use it.
  """
  if 'otrs' not in g:
    if current_app.config.get('OTRS_STUB'):
      client = current_app.config['OTRS_STUB']
    else:
      # get connection config
      try:
        url = current_app.config['OTRS_URL']
        user = current_app.config['OTRS_USERNAME']
        pw = current_app.config['OTRS_PASSWORD']
      except KeyError:
        # TODO: should throw exception; this is a configuration error
        get_log().error("OTRS configuration missing")
        client = None
      else:
        # create OTRS client object
        try:
          get_log().debug("Creating OTRS client session with url=%s, username=%s", url, user)
          client = pyotrs.Client(url, user, pw)

          # recommended but not functional (?)
          #if client.session_restore_or_create():
          if client.session_create():
            get_log().debug("Initialized OTRS client.")
          else:
            # TODO: get information about error?
            get_log().error("Unable to initialize OTRS client.")
            client = None
        #except HTTPError as e:
        except Exception as e:
          get_log().error("Unable to initialize OTRS client: %s", e)
          client = None
    g.otrs = client

  return g.otrs


def close_otrs(e=None):
  if 'otrs' in g:
    if e:
      get_log().info("Closing OTRS client in presence of error")
    else:
      get_log().debug("Closing OTRS client.")
    g.otrs.close()


def ticket_url(ticket_id):
  return "{}/otrs/index.pl?TicketID={}".format(
    current_app.config['OTRS_URL'],
    ticket_id)


def create_ticket(title, body, user, owner):

  try:
    queue = current_app.config['OTRS_QUEUE']
  except KeyError:
    # TODO: this should throw exception--default should be defined if nothing configured
    get_log().error("OTRS configuration missing")

  # create ticket object
  ticket = pyotrs.lib.Ticket.create_basic(
    Title=title,
    Queue=queue,
    CustomerUser=user,
    State=u"new",
    Priority=u"3 normal")
  if not ticket:
    get_log().error("Could not create ticket object")
    return None

  # set some information about the ticket
  ticket.fields['Owner'] = owner
  ticket.fields['Responsible'] = owner

  # create article
  article = pyotrs.lib.Article({
    'Subject': title,
    'Body': body,
    'ArticleType': 'email-external'
  })
  if not article:
    get_log().error("Could not create article object")
    return None

  # create ticket
  details = get_otrs().ticket_create(ticket, article)
  if not details:
    get_log().error("Could not create ticket")
    return None
  get_log().debug("Ticket created.  Details: %s", details)

  return {
    'ticket_id': details['TicketID'],
    'ticket_no': details['TicketNumber']
  }
