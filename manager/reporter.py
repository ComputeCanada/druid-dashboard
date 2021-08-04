# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=wrong-import-position,import-outside-toplevel
#
import re
from flask_babel import _
from manager.log import get_log
from manager.exceptions import AppException

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
    get_log().debug("in ReporterRegistry::__new__")
    if cls._instance is not None:
      raise BaseException("You can't create two of me.  Use get_registry()")
    get_log().debug("New registry")
    cls._instance = super(ReporterRegistry, cls).__new__(cls)
    return cls._instance

  @classmethod
  def get_registry(cls):
    if cls._instance is None:
      cls._instance = cls()
    return cls._instance

  def __init__(self):
    get_log().debug("Initializing reporters...")
    self._reporters = {}

  def register(self, name, reporter):
    if name in self._reporters.keys():
      raise AppException("A reporter has already been registered with that name: {}".format(name))
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

  # subclasses should set this as desired.  Available to view client
  # TODO: need better name/description
  _applicable_actions = None

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
      { 'datum': 'summary',
        'searchable': True,
        'sortable': False,
        'type': 'text',
        'title': _('Summary')
      },
      { 'datum': 'claimant',
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

  #def init(self):
  #  """
  #  Does not a thing as yet
  #  """

  @classmethod
  def summarize_report(cls, cases):

    claimed = 0
    newbs = 0
    existing = 0

    for case in cases:
      if case.claimant is not None:
        claimed += 1
      if case.ticks > 1:
        existing += 1
      else:
        newbs += 1
    return f"There are {len(cases)} cases ({newbs} new and {existing} existing).  {claimed} are claimed."

  @classmethod
  def report(cls, cluster, epoch, data):
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

## I don't see any actual need for this, keeping it around until done
## implementation
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

  @classmethod
  def view(cls, criteria):
    """
    Return dict describing view of data reported.

    Args:
      criteria: dict of criteria for selecting data for view.

    Returns:
      Dict describing view of data reported, in the format:
      ```
      epoch: <seconds since epoch>
      results:
        - obj1.attribute1
        - obj1.attribute2
        - ..
        - obj2.attribute1
        - obj2.attribute2
        - ..
      ```
    """

    # 'cluster' required, 'pretty' optional, nothing else handled
    if set(criteria.keys()) - {'pretty'} != {'cluster'}:
      raise NotImplementedError

    records = cls.get_current(criteria['cluster'])
    if not records:
      return None
    epoch = records[0].epoch

    pretty = criteria.get('pretty', False)

    # serialize records individually so as to add attributes
    serialized = [
      rec.serialize(pretty=pretty) for rec in records
    ]

    return {
      'epoch': epoch,
      'actions': cls._applicable_actions,
      'results': serialized
    }
