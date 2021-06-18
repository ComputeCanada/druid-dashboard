# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=wrong-import-position,import-outside-toplevel
#
import re
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
#                                                       base Reporter class
# ---------------------------------------------------------------------------

class Reporter():
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

  def validate(self, data):
    """
    Check that provided data structure is valid for this type of report.

    Args:
      data: list of dicts describing current instances of potential account
            or job pain or other metrics, as appropriate for the type of
            report.

    Returns:
      True, if the data validates and the report can be registered
      False, otherwise
    """
