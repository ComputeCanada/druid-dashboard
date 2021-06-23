/**
 * Make Toast component (requires Bootstrap) for alerts.
 *
 * @param {String} type "info", "alert", "error"
 * @param {String} message
 * @param {Object} options
 * @returns {Toast} Bootstrap Toast object.
 */
function makeToast(type, message, options) {
  // defaults
  var parentSelector = '#toast-container';
  var closeButtonHTML = '';
  var title = 'Message';
  var extraClasses = '';

  // check for optional overrides
  if (options.parent)
    parentSelector = options.parent
  if (!options.noClose)
    closeButtonHTML = '<button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>';

  // handle types
  switch (type) {
    case "info":
      title = "Info";
      extraClasses = 'bg-info';
      break;
    case "alert":
      title = "Alert";
      extraClasses = 'bg-warning';
      break;
    case "error":
      title = "Error";
      extraClasses = 'text-white bg-danger';
      break;
    default:
      break;
  }

  $(parentSelector).prepend(`
    <div class="toast ${extraClasses}" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="toast-header">
        <strong class="me-auto">${title}</strong>
        <small></small>
        ${closeButtonHTML}
      </div>
      <div class="toast-body">
        ${message}
      </div>
    </div>
  `);
  var toast = $(parentSelector).children().toArray()[0];
  return new bootstrap.Toast(toast, options);
}

// global for tracking toasts
var toasts = [];

function error(msg) {
  toast = makeToast("error", msg, {autohide: false});
  toast.show();
  toasts.push(toast);
  return toasts.length - 1;
}

function status(msg) {
  toast = makeToast("info", msg, {autohide: false, noClose: true});
  toast.show();
  toasts.push(toast);
  return toasts.length - 1;
}

function status_clear(id) {
  /* I would expect toasts[id].dispose() to replace the next three lines but
   * instead it always throws an exception that _element is NULL, which is
   * what removing the DOM element manually presumably does.
   */
  var parent = document.getElementById('toast-container');
  parent.removeChild(toasts[id]._element);
  toasts[id].hide();
  delete toasts[id];
}

