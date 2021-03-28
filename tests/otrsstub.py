# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
class OtrsStub():

  def __init__(self):

    # net ticket ID
    self._nextID = 1

  def ticket_create(self, ticket, article):

    # assign ticket number
    ticket_id = self._nextID
    self._nextID += 1

    return {
      'ticket_id': ticket_id,
      'ticket_no': "0{}".format(ticket_id),
      'ding dong': 'merrily on high',
      'ticket_misc': {
        'ticket': ticket.fields,
        'article': article.fields
      }
    }
