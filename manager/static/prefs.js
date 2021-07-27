// get user preferences
var prefsJSON = Cookies.get("prefs", { 'SameSite': 'strict' });
if (prefsJSON) {
  var prefs = JSON.parse(prefsJSON);
}
else {
  var prefs = {};
}

function initializeClusterPreferences(clusters, report_specs) {
  /* prefs:
   *   cluster: graham
   *   clusters:
   *     graham:
   *       expanded: job age
   *       sorting:
   *         bursts: [3, 'desc']
   *         job age: [4, 'desc']
   *     cedar:
   *       expanded: bursts
   *       sorting:
   *         bursts: [3, 'desc']
   */
  // trouble metric index lookup
  var troubleIndices = {};
  Object.keys(report_specs).forEach(function(report_name, i1, a1) {
    troubleIndices[report_name] = report_specs[report_name]['cols'].findIndex(function(x) {
      return report_specs[report_name]['metric'] == x['datum'];
    });
  });

  // initialize/validate active cluster preference
  var activeValid = false;
  var activeCluster = prefs['cluster'];
  if (activeCluster) {
    // check that preferred active cluster is still valid (listed)
    clusters.forEach(function(x) {
      if (activeCluster == x['id']) {
        activeValid = true;
        return;
      }
    });
  }
  if (!activeValid) {
    prefs['cluster'] = clusters[0]['id'];
  }

  // make sure each cluster is properly represented
  if (!prefs['clusters']) {
    prefs['clusters'] = {};
  }
  clusters.forEach(function(cluster) {
    var clusterID = cluster['id'];

    // initialize cluster prefs if necessary
    if (!prefs['clusters'][clusterID]) {
      prefs['clusters'][clusterID] = {'sorting':  {}};
    }

    // ensure each report has a sorting value
    Object.keys(troubleIndices).forEach(function(report_name, i1, a1) {
      if (!prefs['clusters'][clusterID]['sorting'][report_name]) {
        var troubleIdx = troubleIndices[report_name];
        prefs['clusters'][clusterID]['sorting'][report_name] = [troubleIdx, 'desc'];
      }
    });
  });

  // we don't write the prefs to cookie yet because it'll get updated by other
  // stuff shortly, so it's okay to just leave in memory
}

function updatePreferences() {
  var prefsJSON = JSON.stringify(prefs);
  Cookies.set('prefs', prefsJSON, { 'SameSite': 'strict' });
}

function getActiveCluster() {
  return prefs['cluster'];
}

function setActiveCluster(clusterID) {
  prefs['cluster'] = clusterID;
  updatePreferences();
}

function getActiveReport(clusterID) {
  return prefs['clusters'][clusterID]['expanded'];
}

function setActiveReport(clusterID, reportName) {
  prefs['clusters'][clusterID]['expanded'] = reportName;
  updatePreferences();
}

function getReportSortOrder(clusterID, reportName) {
  return prefs['clusters'][clusterID]['sorting'][reportName];
}

function setReportSortOrder(clusterID, reportName, order) {
  prefs['clusters'][clusterID]['sorting'][reportName] = order;
  updatePreferences();
}
