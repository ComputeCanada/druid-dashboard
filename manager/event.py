# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
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

class ReportReceived(Event):

  def __init__(self, message):
    self._message = message
    super().__init__()

  def notifiable(self):
    return True


class CaseEvent(Event):

  def __init__(self, id=None, caseID=None, analyst=None, timestamp=None):
    self._caseID = caseID
    self._analyst = analyst
    if analyst:
      self._analyst_pretty = get_ldap().get_person_by_cci(analyst)['givenName']
    super().__init__(id, timestamp)


class CaseUpdate(CaseEvent):

  def __init__(self, id=None, caseID=None, timestamp=None, caseReportID=None, jobRange=None,
      summary=None):
    self._caseReportID = caseReportID
    self._jobRange = jobRange
    self._summary = summary
    super().__init__(id, caseID, None, timestamp)
    raise "Not ready to use this yet"

# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------

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
