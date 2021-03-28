# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import json

# ---------------------------------------------------------------------------
#                                                                      ajax
# ---------------------------------------------------------------------------

def test_get_bursts_xhr(client):
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 200

  response = client.get('/xhr/bursts/')
  assert response.status_code == 200
  interpreted = json.loads(response.data.decode('utf-8'))
  assert interpreted['testcluster']['bursts'][0]['epoch'] == interpreted['testcluster']['epoch']
  del interpreted['testcluster']['bursts'][0]['epoch']
  del interpreted['testcluster']['epoch']
  print(interpreted)
  assert interpreted == {
    "testcluster": {
      "bursts": [
        {"account":"def-dleske-aa","claimant":None,"cluster":"testcluster",
          "id":12,"jobrange":[1005,2015],"pain":1.2, "state":"unclaimed",
          "state_pretty":"Unclaimed","summary":"{}","ticks":1,"resource":"cpu",
          "resource_pretty":"CPU","ticket_id":None, "ticket_no":None,
          "ticket_href":None}
      ],
    },
    "testcluster2": {
      "bursts": [
        {"account":"def-aaa-aa","claimant":None,"cluster":"testcluster2",
          "epoch":25,"id":8,"jobrange":[15,25],"pain":2.5,"state":"unclaimed",
          "state_pretty":"Unclaimed","summary":None,"ticks":0,"resource":"cpu",
          "resource_pretty":"CPU","ticket_id":None, "ticket_no":None,
          "ticket_href":None},
        {"account":"def-bbb-aa","claimant":None,"cluster":"testcluster2",
          "epoch":25,"id":9,"jobrange":[16,26],"pain":2.5,"state":"unclaimed",
          "state_pretty":"Unclaimed","summary":None,"ticks":0,"resource":"cpu",
          "resource_pretty":"CPU","ticket_id":None, "ticket_no":None,
          "ticket_href":None},
        {"account":"def-ccc-aa","claimant":None,"cluster":"testcluster2",
          "epoch":25,"id":10,"jobrange":[17,27],"pain":2.5,"state":"unclaimed",
          "state_pretty":"Unclaimed","summary":None,"ticks":0,"resource":"cpu",
          "resource_pretty":"CPU","ticket_id":None, "ticket_no":None,
          "ticket_href":None}
      ],
      "epoch":25
    }
  }


def test_update_bursts_xhr(client):
  data = {'12': 'claimed'}
  response = client.patch('/xhr/bursts/', json=data, environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  interpreted = json.loads(response.data.decode('utf-8'))
  del interpreted['testcluster']['bursts'][0]['epoch']
  del interpreted['testcluster']['epoch']
  print(interpreted)
  assert interpreted == {
    "testcluster": {
      "bursts": [
        {
          "account":"def-dleske-aa",
          "claimant":'tst-003',
          "claimant_pretty":'User 1',
          "cluster":"testcluster",
          "resource":"cpu",
          "resource_pretty": "CPU",
          "id":12,
          "jobrange":[1005,2015],
          "pain":1.2,
          "state":"claimed",
          "state_pretty": "Claimed",
          "summary": "{}",
          "ticket_id": None,
          "ticket_no": None,
          "ticket_href":None,
          "ticks": 1
        }
      ],
    },
    "testcluster2": {
      "bursts": [
        {"account":"def-aaa-aa","claimant":None,"cluster":"testcluster2",
          "epoch":25,"id":8,"jobrange":[15,25],"pain":2.5,"state":"unclaimed",
          "state_pretty":"Unclaimed","summary":None,"ticks":0,"resource":"cpu",
          "resource_pretty":"CPU","ticket_id":None, "ticket_no":None,
          "ticket_href":None},
        {"account":"def-bbb-aa","claimant":None,"cluster":"testcluster2",
          "epoch":25,"id":9,"jobrange":[16,26],"pain":2.5,"state":"unclaimed",
          "state_pretty":"Unclaimed","summary":None,"ticks":0,"resource":"cpu",
          "resource_pretty":"CPU","ticket_id":None, "ticket_no":None,
          "ticket_href":None},
        {"account":"def-ccc-aa","claimant":None,"cluster":"testcluster2",
          "epoch":25,"id":10,"jobrange":[17,27],"pain":2.5,"state":"unclaimed",
          "state_pretty":"Unclaimed","summary":None,"ticks":0,"resource":"cpu",
          "resource_pretty":"CPU","ticket_id":None, "ticket_no":None,
          "ticket_href":None}
      ],
      "epoch":25
    }
  }
