# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
class OtrsStub():

  def __init__(self):

    # net ticket ID
    self._nextID = 1

  # pylint: disable=no-self-use
  def close(self):
    print("Closing OTRS (stub)")

  def ticket_create(self, ticket, article):

    # assign ticket number
    ticket_id = self._nextID
    self._nextID += 1

    return {
      'TicketID': ticket_id,
      'TicketNumber': "0{}".format(ticket_id),
      'ding dong': 'merrily on high',
      'ticket_misc': {
        'ticket': ticket.fields,
        'article': article.fields
      }
    }

  # pylint: disable=no-self-use,unused-argument
  def ticket_update(self, ticket, **kwargs):
    print("Updating ticket (not really)")
