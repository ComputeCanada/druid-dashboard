# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import re
#from manager.db import get_db
#from manager.log import get_log

_re = r'%(?P<var>\w+)%'
_rec = re.compile(_re)

# pylint: disable=line-too-long
_stubs = {
  "other language follows": {
    "en": "\n(La version française de ce message suit.)\n",
    "fr": "\n(The English language version of this message follows.)\n"
  },
  "separator": "\n--------------------------------------\n",
  "intro title": {
    "en": "NOTICE: Your computations may be eligible for prioritised execution",
    "fr": "AVIS: Vos calculs peuvent être éligibles pour une exécution prioritaire"
  },
  "intro": {
    "en": "Hello %PREFERRED_NAME%,\n\nOngoing analysis of queued jobs on %CLUSTER% has shown that your project has a quantity of jobs that would benefit from a temporary escalation in priority.  Please let us know by replying to this message if you are interested.\n\nBest regards,\n%ANALYST%",
    "fr": "Bonjour %PREFERRED_NAME%,\n\nAnalyse en cours des travaux en attente sur %CLUSTER% a montré que votre projet comporte une quantité d'emplois bénéficier d'une escalade temporaire en priorité. S'il vous plaît laissez-nous savoir par répondre à ce message si vous êtes intéressé.\n\nMeilleures salutations,\n%ANALYST%"
  }
}

class Template:

  def __init__(self, name, language=None):
    if language:
      self._content = _stubs[name][language]
    else:
      self._content = _stubs[name]

  def render(self, values=None):
    values = values or {}
    return re.sub(
      _rec,
      lambda x: values.get(x['var'], "<<UNDEFINED('{}')>>".format(x['var'])),
      self._content
    )
