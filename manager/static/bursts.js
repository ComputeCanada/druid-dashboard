function rejectBurst(id, account) {

  var updates = [
    {
      'state': 'rejected',
      'note': $('#noteModalTextarea')[0].value
    }
  ];

  // process update
  updateCase(id, updates, {
    action: "Rejecting burst candidate...",
    error: "Failed to reject candidate"
  });
}

function acceptBurst(id, account) {

  var updates = [
    {
      'state': 'accepted',
      'note': $('#noteModalTextarea')[0].value
    }
  ];

  // process update
  updateCase(id, updates, {
    action: "Accepting burst candidate...",
    error: "Failed to accept candidate"
  });
}
