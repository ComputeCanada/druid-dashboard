# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=raise-missing-from
#
import json
import requests
from manager.db import get_db
from manager.log import get_log
from manager.notifier import register_notifier, Notifier, SQL_GET_NOTIFIER
from manager.exceptions import BadCall

# used for displaying configuration form
definition = {
  'url': 255,
  'from': 64,
  'emoji': 32
}

# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------

def get_slack_notifier(name):

  # retrieve notifier with that name
  db = get_db()
  res = db.execute(SQL_GET_NOTIFIER, (name,)).fetchone()

  # get configuration
  defn = json.loads(res['config'])

  return SlackNotifier(name, config=defn)

# ---------------------------------------------------------------------------
#                                                       SlackNotifier class
# ---------------------------------------------------------------------------

class SlackNotifier(Notifier):

  def _config(self, config):

    try:
      self._url = config['url']
    except KeyError:
      raise BadCall("URL must be defined for Slack notifier")

    self._from = config.get('from')
    self._emoji = config.get('emoji')

  def notify(self, message):

    data = {
      'text': message
    }

    if self._from:
      data['username'] = self._from
    if self._emoji:
      data['icon_emoji'] = self._emoji

    r = requests.post(self._url, data=json.dumps(data))
    if r.status_code == 200:
      get_log().info("Sent Slack notification")
    else:
      get_log().error("Sending Slack notification failed")
      get_log().debug("url=%s, from=%s, emoji=%s, message=%s",
        self._url, self._from, self._emoji, message)

# ---------------------------------------------------------------------------
#                                                     notifier registration
# ---------------------------------------------------------------------------

# register notifier on inclusion
register_notifier('Slack', SlackNotifier)
