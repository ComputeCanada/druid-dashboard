# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=wrong-import-position,import-outside-toplevel
#
import re
from flask_babel import _
from manager.ldap import get_ldap
from manager.log import get_log
from manager.exceptions import AppException
from manager.otrs import ticket_url

# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------

# regular expression to match job array IDs and allow extraction of just ID
__job_id_re = re.compile(r'^(\d+)')

def just_job_id(jobid):
  """
  Strip job ID to just the base ID, not including any array part.
  """
  if isinstance(jobid, int):
    return jobid
  match = __job_id_re.match(jobid)
  if not match:
    raise AppException(
      "Could not parse job ID ('{}') to extract base ID".format(jobid)
    )
  return match.groups()[0]

# ---------------------------------------------------------------------------
#                                                         Reporter registry
# ---------------------------------------------------------------------------

class ReporterRegistry:

  _instance = None

  def __new__(cls):
    if cls._instance:
      # TODO: better exception
      raise Exception("You can't create multiples of these!")
    cls._instance = super(ReporterRegistry, cls).__new__(cls)
    return cls._instance

  def __init__(self):
    self._reporters = {}

  def register(self, name, reporter):
    if name in self._reporters.keys():
      # TODO: better exception
      raise BaseException("A reporter has already been registered with that name: {}".format(name))
    self._reporters[name] = reporter
    get_log().info("Registered reporter for %s", name)

  @property
  def reporters(self):
    return self._reporters

  @property
  def descriptions(self):
    descriptions = {}
    for name, reporter in self._reporters.items():
      descriptions[name] = reporter.describe()
    return descriptions

# create global reporter registry
registry = ReporterRegistry()

# ---------------------------------------------------------------------------
#                                                       base Reporter class
# ---------------------------------------------------------------------------

class Reporter:
  """
  Base class for reporting metrics.  Subclasses must implement documented
  methods.

  Class documentation should describe report structure.
  """

  @classmethod
  def describe(cls):
    """
    Describe this type of report for presentation or other purposes.  For
    example, to inform UI templates what columns should appear in the report
    table on the Dashboard.

    Returns: A data structure as follows:
      {
        table: str,       # table name in database
        title: str,       # display title of report
        metric: str,      # primary metric of interest
        cols: [(          # ordered list of field descriptors
          datum,          # name of reported data field
          label           # display label
        ), ... ],
      }
    """
    desc = cls._describe()
    desc['cols'].insert(0,
      { 'datum': 'ticks',
        'searchable': False,
        'sortable': True,
        'type': 'number',
        'title': "<img src='static/icons/ticks.svg' height='18' width='20' " \
                 "alt='Times reported' title='Times reported'/>",
      }
    )
    desc['cols'].extend([
      { 'datum': 'state',
        'searchable': True,
        'sortable': True,
        'type': 'text',
        'title': _('State')
      },
      { 'datum': 'analyst',
        'searchable': True,
        'sortable': True,
        'type': 'text',
        'title': _('Analyst')
      },
      { 'datum': 'ticket',
        'searchable': True,
        'sortable': True,
        'type': 'text',
        'title': _('Ticket')
      },
      { 'datum': 'notes',
        'searchable': False,
        'sortable': True,
        'type': 'text',
        'title': _('Notes')
      },
      { 'datum': 'action',
        'searchable': False,
        'sortable': False,
        'type': 'text',
        'title': _('Action')
      }
    ])

    return desc

  @classmethod
  def _describe(cls):
    """
    Subclasses should implement this
    """
    raise NotImplementedError

  def init(self):
    """
    Does not a thing as yet
    """

  def report(self, cluster, epoch, data):
    """
    Report potential job and/or account issues.

    Args:
      cluster: reporting cluster
      epoch: epoch of report (UTC)
      data: list of dicts describing current instances of potential account
            or job pain or other metrics, as appropriate for the type of
            report.

    Returns:
      String describing summary of report.
    """
    raise NotImplementedError

#  def validate(self, data):
#    """
#    Check that provided data structure is valid for this type of report.
#
#    Args:
#      data: list of dicts describing current instances of potential account
#            or job pain or other metrics, as appropriate for the type of
#            report.
#
#    Returns:
#      True, if the data validates and the report can be registered
#      False, otherwise
#    """
#    raise NotImplementedError

  def view(self, criteria):
    """
    Return dict describing view of data reported.

    Args:
      criteria: dict of criteria for selecting data for view.

    Returns:
      Dict describing view of data reported.
    """

    if list(criteria.keys()) != ['cluster']:
      raise NotImplementedError

    ldap = get_ldap()

    records = self.__class__.get_current(criteria['cluster'])
    if not records:
      return None
    epoch = records[0].epoch

    # serialize records individually so as to add attributes
    serialized = []
    for record in records:
      row = record.serialize()

      # add claimant's name
      cci = row['claimant']
      if cci:
        person = ldap.get_person_by_cci(cci)
        if not person:
          get_log().error("Could not find name for cci '%s'", row['claimant'])
        else:
          row['claimant_pretty'] = person['givenname']

      # add ticket URL if there's a ticket
      if record.ticket_id:
        row['ticket_href'] = "<a href='{}' target='_ticket'>{}</a>".format(
          ticket_url(record.ticket_id), record.ticket_no)
      else:
        row['ticket_href'] = None

      # add any prettified fields
      row['state_pretty'] = _(str(record.state))
      row['resource_pretty'] = _(str(record.resource))

      serialized.append(row)

    return { 'epoch': epoch, 'results': serialized }
