# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=raise-missing-from
#
import json
import requests
from manager.db import get_db
from manager.notifier import register_notifier, Notifier, SQL_GET_NOTIFIER

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
      # TODO: proper exception
      raise Exception("URL must be defined for Slack notifier")

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

    # TODO: check this and raise exception, then like log that or whatever?
    assert r.status_code == 200

#  def config_load(self):
#
#    # deserialize configurations
#    self._deserialize(defn)
#
#  def config_save(self):
#
#    # serialize configurations
#    defn = self._serialize()

# ---------------------------------------------------------------------------
#                                                     notifier registration
# ---------------------------------------------------------------------------

# register notifier on inclusion
register_notifier('Slack', SlackNotifier)
