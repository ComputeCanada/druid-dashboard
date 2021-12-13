function rejectBurst(id, account) {
  var updates = [
    {
      'state': 'rejected',
      'note': $('#noteModalTextarea')[0].value
    }
  ];

  // process update
  updateCase(id, updates, {
    action: i18n('REJECTING_BURST_CANDIDATE'),
    error: i18n('REJECTING_BURST_CANDIDATE_FAILED')
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
    action: i18n('ACCEPTING_BURST_CANDIDATE'),
    error: i18n('ACCEPTING_BURST_CANDIDATE_FAILED')
  });
}
