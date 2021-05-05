# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=wrong-import-position,import-outside-toplevel
#
from flask import current_app
from .notifier import get_notifiers
from .ldap import get_ldap
from .log import get_log

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

# TODO: will need query for "get notifiers associated with this type of event"

# ---------------------------------------------------------------------------
#                                                        base Event classes
# ---------------------------------------------------------------------------

class Event():

  def __init__(self, id=None, timestamp=None):
    self._id = id
    self._timestamp = timestamp

  def __str__(self):
    return "{}: {}".format(self.__class__.__name__, self._message)

  # pylint: disable=no-self-use
  def notifiable(self):
    return False

  @property
  def id(self):
    if self._id is None:
      raise Exception('TODO: proper exception (there is no ID defined on this object; was it just created?')
    return self._id

  @property
  def timestamp(self):
    return self._timestamp

  def serialize(self):
    d = {
      key.lstrip('_'): val
      for (key, val) in self.__dict__.items()
    }
    d['type'] = self.__class__.__name__
    return d

class BurstReportReceived(Event):

  def __init__(self, message):
    self._message = message
    super().__init__()

  def notifiable(self):
    return True


class BurstEvent(Event):

  def __init__(self, id=None, burstID=None, analyst=None, timestamp=None):
    self._burstID = burstID
    self._analyst = analyst
    if analyst:
      self._analyst_pretty = get_ldap().get_person_by_cci(analyst)['givenName']
    super().__init__(id, timestamp)


class BurstUpdate(BurstEvent):

  def __init__(self, id=None, burstID=None, timestamp=None, burstReportID=None, jobRange=None,
      summary=None):
    self._burstReportID = burstReportID
    self._jobRange = jobRange
    self._summary = summary
    super().__init__(id, burstID, None, timestamp)
    raise "Not ready to use this yet"

# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------

# import subclasses
from . import note
from . import actions

# this is where events are stored
events = {}

def register_event(type, cls):
  events[type] = cls

def report(event):

  get_log().debug("In report(%s)", event)

  if not event.notifiable():
    return

  notifiers = get_notifiers()
  if notifiers:
    for notifier in notifiers:
      notifier.notify("{}: {}".format(current_app.config['APPLICATION_TAG'], event))

def get_burst_events(burstID):

  # get all notes with burst_id == burstID
  notes = note.get_by_burst(burstID) or []

  # get all actions with burst_id == burstID
  updates = actions.get_by_burst(burstID) or []

  # sort combined events by timestamp
  events = sorted(notes + updates, key=lambda x : x.timestamp)

  return events
