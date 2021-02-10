# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
from manager.notifier import get_notifiers

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

# TODO: will need query for "get notifiers associated with this type of event"

# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------

# this is where events are stored
events = {}

def register_event(type, cls):
  events[type] = cls

def report(event):

  notifiers = get_notifiers()
  if notifiers:
    for notifier in notifiers:
      notifier.notify("We got an event: {}".format(event))

# ---------------------------------------------------------------------------
#                                                               Event class
# ---------------------------------------------------------------------------

class Event():

  def __init__(self, message):

    self._message = message

  def __str__(self):
    return "{}: {}".format(self.__class__.__name__, self._message)


class BurstReportReceived(Event):

  pass
