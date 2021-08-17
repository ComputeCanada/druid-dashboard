# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=wrong-import-position,import-outside-toplevel
#
"""
Reporter and ReporterRegistry classes.

Subclass the Reporter class to support a new type of reportable problem
metrics.  The original use case for this was burst candidates: accounts with
significant short-term need that can't be readily met by the resources
typically available without a RAC.

Use the ReporterRegistry class to register new reporter classes so that the
application is aware of them: knows to query them for data to display on the
dashboard and can serve them appropriately via the REST API.
"""

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

  Args:
    jobid: Job identifier, optionally including array part.

  Returns:
    Integer job identifier.

  Raises:
    `manager.exceptions.AppException` if the job ID does not match the
    expected format.
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
  """
  Singular registry of reporters.

  The application uses this registry to query available report types.
  Subclasses of the Reporter class register so the application is aware of
  them and knows to query and present different report types.

  Attributes:
    reporters: Dict of report names to their classes.
  """

  _instance = None

  def __new__(cls):
    if cls._instance is not None:
      # TODO: Don't raise BaseException!
      raise BaseException("You can't create two of me.  Use get_registry()")
    cls._instance = super(ReporterRegistry, cls).__new__(cls)
    return cls._instance

  @classmethod
  def get_registry(cls):
    """Return singular instance of registry."""

    if cls._instance is None:
      cls._instance = cls()
    return cls._instance

  def __init__(self):
    self._reporters = {}

  def register(self, name, reporter):
    """
    Register a Reporter implementation.

    Reporters (subclasses of the `reporter.Reporter` class) must register
    themselves so the application knows to query these classes.  A subclass of
    the Reporter class must use this method at the end of its module file.

    Args:
      name: The common name for the reporter type.  This name will be used,
        for example, when reporting via the API.  It is recommended it match
        the table name and be plural, for example, "bursts" or "oldjobs".
      reporter: The subclass.

    Raises:
      `manager.exceptions.AppException` if a reporter with that name has
        already by registered.
    """
    if name in self._reporters.keys():
      raise AppException("A reporter has already been registered with that name: {}".format(name))
    self._reporters[name] = reporter
    get_log().info("Registered reporter for %s", name)

  @property
  def reporters(self):
    """Dictionary of reporter name to class."""
    return self._reporters

  @property
  def descriptions(self):
    """
    Dictionary of reporter name to the data description provided by the
    reporter.
    """

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
  """Base class for reporting metrics.

  The Reporter class defines methods or stubs necessary to support a Detector
  reporting potential problem cases of specific kind through the application's
  API.

  Subclasses must implement some methods and may override others, as
  documented.  Methods implemented as stubs will throw `NotImplementedError`
  if called.
  """

  @classmethod
  def describe(cls):
    """Describe report structure and semantics.

    The results of this method are used to meaningfully present the report data
    (provided by other methods).  For example, these descriptions can be used
    to inform UI templates what columns should appear in the report table on
    the Dashboard.

    The data returned has the following structure:
    ```
    {
      table: str,       # table name in database
      title: str,       # display title of report
      metric: str,      # primary metric of interest
      cols: [{          # ordered list of field descriptors
        datum: ..,      # name of reported data field
        title: ..,      # display label (such as for column header)
        searchable: .., # should column data be included in searches
        sortable: ..,   # should table be sortable on this column
        type: ..,       # type (text or number, used for display)
        help: ..        # help text, displayed when hovering over title
      }, ... ],
    }
    ```

    Returns:
      A data structure conforming to the above.

    Note:
      Subclasses _must not_ override this function.  Instead, subclasses
      _must_ override `Reporter.describe_me()` to describe the specifics of
      that case and this method will combine the common and specific field
      descriptions.
    """
    desc = cls.describe_me()
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
  def describe_me(cls):
    """Describe report structure and semantics specific to report type.

    Subclasses should implement this to describe the table name, report title,
    and the primary metric of the report type as well as columns specific to
    and implemented by the subclass.  The Reporter class will call this method
    from `Reporter.describe()` to generate the full report.

    All fields are required with the exception of `help`.

    The data returned has the following structure:
    ```
    {
      table: str,       # table name in database
      title: str,       # display title of report
      metric: str,      # primary metric of interest
      cols: [{          # ordered list of field descriptors
        datum: ..,      # name of reported data field
        title: ..,      # display label (such as for column header)
        searchable: .., # should column data be included in searches
        sortable: ..,   # should table be sortable on this column
        type: ..,       # type (text or number, used for display)
        help: ..        # help text, displayed when hovering over title
      }, ... ],
    }
    ```

    Returns:
      A data structure conforming to the above.
    """
    raise NotImplementedError

  @classmethod
  def summarize_report(cls, cases):
    """Provide a brief, one-line summary of last report.

    The intended use case for this summary is for notifications, such as to
    Slack, when a report is received and interpreted.

    Subclasses may override this method to provide additional information.

    Args:
      cases: The list of cases (objects subclassed from Reportable class)
        created or updated from the last report.

    Returns:
      A string description of the last report.
    """
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
    """Report potential job and/or account issues.

    Subclasses must implement this to interpret reports coming through the API
    from a Detector.  Those implementations should describe the expected
    format of the `data` argument and should call `Reporter.summarize_report()`
    to provide a summary as return value.

    Args:
      cluster: The reporting cluster.
      epoch: Epoch of report (UTC).
      data: A list of dicts describing current instances of potential account
            or job pain or other metrics, as appropriate for the type of
            report.

    Returns:
      String describing summary of report.
    """
    raise NotImplementedError

  @classmethod
  def view(cls, criteria):
    """Provide view to reported data.

    By default, provides current view of reported data.  Subclasses may
    override this to provide additional views.

    The view is described as follows:
    ```
    epoch: seconds since epoch
    results:
      - obj1.attribute1: ..
        obj1.attribute2: ..
        obj1.attribute2_pretty: ..
        obj1.attribute3: ..
        ...
      - obj2.attribute1: ..
        obj2.attribute2: ..
        obj2.attribute2_pretty: ..
        obj2.attribute3: ..
        ...
      ...
    ```

    Attributes suffixed with `_pretty` provide display versions of those
    attributes without, if appropriate and requested.

    Args:
      criteria: Dict of criteria for selecting data for view.  In this
        implementation, `cluster` is required and `pretty` is optional.

        * `cluster`: (required) Cluster for which to provide data.
        * `pretty`: (optional, default False): provide display-friendly
          alternatives on some fields, if possible.

    Returns:
      None or a data structure conforming to the above.

    Raises:
      NotImplementedError: Criteria other than `pretty` or `cluster` were
        specified, indicating this should have been overridden by a subclass
        and were not.
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
      'results': serialized
    }
