function requestClusters() {
  status_id = status("Retrieving cluster info...")
  $.ajax({
    url: '/xhr/clusters/',
    method: 'GET',
    success: function(clusters, status, jqXHR) {
      status_clear(status_id);
      displayClusters(clusters, status, jqXHR);
    },
    error: function() {
      status_clear(status_id);
      error("Failed to retrieve cluster list");
    }
  });
}

function displayClusters(clusters, stats, jqXHR) {
  // sort cluster list by proper name
  var clusters_sorted = clusters.sort(function(a, b) {
    return a['name'].localeCompare(b['name']);
  });

  // create cluster lookup
  clusters.forEach(function(cluster) {
    cluster_lookup[cluster['id']] = cluster['name'];
  });

  // initialize preferences
  initializeClusterPreferences(clusters_sorted, report_specs);

  // get tab parent containers
  var tabsContainer = document.getElementById('tabs_container');
  var panesContainer = document.getElementById('panes_container');

  // create tabs for each cluster and add to parent container
  for (var i=0; i < clusters_sorted.length; i++) {
    var cluster = clusters_sorted[i];
    var cluster_id = cluster['id'];
    var cluster_name = cluster['name'];

    var tab_id = cluster_id + '-tab';
    var pane_id = cluster_id + '-pane';

    // add cluster tab
    var tab = document.createElement('li');
    tab.className = 'nav-item';
    tab.setAttribute('role', 'presentation');
    tab.innerHTML = `
      <button class='nav-link' id='${tab_id}' data-bs-toggle='tab'
        data-bs-target='#${pane_id}' role='tab' data-cluster='${cluster_id}'
        aria-controls='${cluster_id}' aria-selected='false'
      >${cluster_name}</button>`;
    tabsContainer.appendChild(tab);

    // add cluster pane
    var pane = document.createElement('div');
    pane.className = 'tab-pane fade';
    pane.setAttribute('id', pane_id);
    pane.setAttribute('role', 'tabpanel');
    pane.setAttribute('aria-labelled-by', tab_id);
    pane.innerHTML = `
      <div class='accordion' id='${cluster_id}_accordions'>
      </div>`;
    panesContainer.appendChild(pane);
  }

  // create listeners
  var triggerTabList = [].slice.call(document.querySelectorAll('#tabs_container button'))
  triggerTabList.forEach(function (triggerEl) {
    var tabTrigger = new bootstrap.Tab(triggerEl)

    triggerEl.addEventListener('click', function (event) {
      event.preventDefault();
      tabTrigger.show();
      setActiveCluster(event.target.dataset.cluster);
    });
  });

  // display cluster tab from preferences
  activeCluster = getActiveCluster();
  var activeTabId = `${activeCluster}-tab`;
  var activeTab = document.getElementById(activeTabId);
  activeTab.classList.add('active');
  activeTab.setAttribute('aria-selected', 'true');

  var activePaneId = `${activeCluster}-pane`;
  var activePane = document.getElementById(activePaneId);
  activePane.classList.add('show');
  activePane.classList.add('active');

  // request reports for each cluster, beginning with active cluster
  requestReports(activeCluster);
  clusters.forEach(function(cluster) {
    if (cluster['id'] !== activeCluster) {
      requestReports(cluster['id']);
    }
  });
}


function requestReports(cluster) {
  var status_id = status(`Retrieving reports for ${cluster_lookup[cluster]}...`);
  $.ajax({
    url: `/xhr/cases/?cluster=${cluster}`,
    method: 'GET',
    success: function(reports, status, jqXHR) {
      status_clear(status_id);
      displayReports(reports, status, jqXHR);
    },
    error: function() {
      status_clear(status_id);
      error("Failed to retrieve burst reports");
    }
  });
}

function makeTableBlank(cluster, report) {
  var header = `
            <table id='${report}_table_${cluster}' class='bursts' style='width: 100%'>
              <thead>`;
  var rows = "";
  report_specs[report].cols.forEach(function(colspec, index, array) {
    var classes = "";
    var titlespec = "";

    if (!colspec['searchable']) {
      classes += " nosearch";
    }
    if (!colspec['sortable']) {
      classes += " nosort";
    }
    if (colspec['type'] == "number") {
      classes += " number";
    }
    if (colspec['help']) {
      titlespec = `title='${colspec['help']}'`
    } 
    rows += `
                  <th class='${ classes }' ${titlespec}>${ colspec['title'] }</th>`;
  });

  return header + rows + `
                </tr>
              </thead>
              <tbody>
              </tbody>
            </table>
  `;
}


function createReportTable(cluster, report, results) {

  // get ordering from preferences
  var ordering = getReportSortOrder(cluster, report);

  // create and populate the table
  $(`#collapse-${cluster}-${report}`).html(`
      <div class="accordion-body">
        ${makeTableBlank(cluster, report)}
      </div>`);
  populateReportTable(cluster, report, results, [ordering]);

  // set up ordering update handler
  $(`#${report}_table_${cluster}`).on('order.dt', function(event) {
    var order = $(event.target).DataTable().order();
    setReportSortOrder(cluster, report, order);
  });
}


function displayReports(reports, status, jqXHR) {

  var cluster = reports['cluster'];

  // get main accordion container
  var accordionParent = document.getElementById(`${cluster}_accordions`);

  // get just reports by filtering out 'cluster'
  var report_names = Object.keys(reports).filter(function(item) {
    return item !== 'cluster'
  });

  // check if there are reports
  if (report_names.length == 0) {
    accordionParent.innerHTML = "<p>{{ _('There are no current reports for this cluster.') }}</p>";
  }
  else {
    for (var i=0; i < report_names.length; i++) {

      var report = report_names[i];

      // TODO: i18n
      var title = `${report_specs[report].title} - reported ${epoch_to_local_time(reports[report]['epoch'])}`;

      // create accordian for this
      var accordion = document.createElement('div');
      accordion.innerHTML = `<div class="accordion-item">
        <h2 class="accordion-header" id="heading-${cluster}-${report}">
          <button id="collapse-button-${cluster}-${report}"
            class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
            data-bs-target="#collapse-${cluster}-${report}" aria-expanded="false"
            aria-controls="collapse-${cluster}-${report}"
          >
            ${title}
          </button>
        </h2>
        <div id="collapse-${cluster}-${report}" class="accordion-collapse collapse"
          aria-labelledby="heading-${cluster}-${report}" data-bs-parent="#${cluster}_accordions"
          data-ccf-report='${report}' data-ccf-cluster='${cluster}'
        >
        </div>
      </div>`;

      // add to parent and so to the DOM
      accordionParent.appendChild(accordion);

      // create and populate report table
      createReportTable(cluster, report, reports[report]['results']);
    }

    // determine which report should be expanded by default
    var expanded = getActiveReport(cluster);
    if (!expanded || report_names.indexOf(expanded) == -1) {
      // TODO: should we flag this to user?
      //error(`Resetting preferred report because report ${expanded} does not exist for cluster ${cluster_lookup[cluster]}`);
      expanded = report_names[0];
      setActiveReport(cluster, expanded);
    }

    // expand that cluster's accordion
    // There are two ways to do this: send a button-click message to the
    // accordion button, or manipulate the classes of the accordion button
    // and the accordioned division.  The latter eliminates the animation,
    // which is too much fancy for a basic page load
    //$(`#collapse-button-${expanded}`).click();
    $(`#collapse-button-${cluster}-${expanded}`).removeClass('collapsed');
    $(`#collapse-${cluster}-${expanded}`).addClass('show');

    // add listener for saving user's preference
    accordionParent.addEventListener('show.bs.collapse', function(event) {
      var thisCluster = event.target.dataset.ccfCluster;
      var defaultReport = event.target.dataset.ccfReport;
      setActiveReport(thisCluster, defaultReport);
    });
  }
}

function refreshReports(reports) {

  /* TODO:
   * This should check whether there are additional clusters and/or reports
   * than existed previously by checking contents of prefs, and if updates
   * do not match what's there, create default prefs for new stuff, and update
   * UI components to match changes (add and remove cluster tabs; add and
   * remove report accordions)
   *
   * ...maybe.  This is called after updating reports with notes, ticket, etc.
   * and so might well be limited.
   */

  // we don't go by active tab in case there's a race condition
  var cluster = reports['cluster'];

  // get main accordion container
  var accordionParent = document.getElementById(`${cluster}_accordions`);

  // get just reports by filtering out 'cluster'
  var report_names = Object.keys(reports).filter(function(item) {
    return item !== 'cluster'
  });

  // check if there are reports
  if (report_names.length == 0) {
    // TODO: remove accordions and data tables and paste a message of some kind
    // or does this just mean there aren't any updates for this report
  }
  else {
    for (var i=0; i < report_names.length; i++) {
      var report = report_names[i];
      createReportTable(cluster, report, reports[report]['results']);
    }
  }
}

function populateReportTable(cluster, report, data, ordering) {

  // build array of column definitions of the format {"name": name}
  var columnNames = report_specs[report]['cols'].map(function(x) {
    return { "name": x['datum'] };
  }).concat([
    { "name": "id" },
  ]);
  var idRowIdx = columnNames.length - 1;

  $(`#${report}_table_${cluster}`).dataTable({
    "autoWidth": false,
    "data": renderTableData(data, report_specs[report]['metric'], columnNames),
    "columnDefs": [
      { searchable: false, targets: 'nosearch' },
      { orderable: false, targets: 'nosort' },
      { className: 'number', targets: 'number' },
      { visible: false, targets: [idRowIdx] }
    ],
    columns: columnNames,
    order: getReportSortOrder(cluster, report),
    rowId: function(row) { return cluster + "_" + report + "_" + row[idRowIdx] }
  });
}

function makeSummaryTable(summary) {
  var summaryHTML = '';
  for (key in summary) {
    summaryHTML += `<tr><th>${key}</th><td>${summary[key]}</td></tr>`;
  }
  return `<table class='not-table'>${summaryHTML}</table>`;
}

// view data provided by reporter subclass
// TODO: render action menu based on available actions from Reporter subclass
function renderTableData(bursts, metric, columnNames) {

  var name, prettified;

  bycols = [];
  for (var i=0, ien=bursts.length; i<ien; i++) {

    bycols[i] = columnNames.map(function(column) {
      name = column['name'];
      prettified = column['name'] + '_pretty';
      if (name == 'summary') {
        if (bursts[i][prettified] != null) {
          return makeSummaryTable(bursts[i][prettified]);
        } else {
          return makeSummaryTable(bursts[i][name]);
        }
      } else if (bursts[i][prettified] != null) {
        return bursts[i][prettified];
      } else if (name == 'action') {
        return renderActionMenu(bursts[i]);
      } else if (bursts[i][name] == null) {
        return '-';
      }
      return bursts[i][name];
    });
  }

  return bycols;
}
