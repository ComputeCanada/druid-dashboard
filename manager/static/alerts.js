// globals for tracking toasts
var toasts = [];

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
  var parentContainerId = 'toast-container';
  var closeButtonHTML = '';
  var title = 'Message';
  var extraClasses = '';

  // check for optional overrides
  if (options.parentContainerId)
    parentContainerId = options.parentContainerId;
  if (!options.noClose)
    closeButtonHTML = '<button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>';

  // handle types
  switch (type) {
    case "info":
      title = i18n("INFO"),
      extraClasses = 'bg-info';
      break;
    case "alert":
      title = i18n("ALERT");
      extraClasses = 'bg-warning';
      break;
    case "error":
      title = i18n("ERROR");
      extraClasses = 'text-white bg-danger';
      break;
    default:
      break;
  }

  // get parent container
  var parentContainer = document.getElementById(parentContainerId);

  // create toast element
  var toastEl = document.createElement('div');
  toastEl.className = `toast ${extraClasses}`;
  toastEl.setAttribute('role', 'alert');
  toastEl.setAttribute('aria-live', 'assertive');
  toastEl.setAttribute('aria-atomic', 'true');
  toastEl.innerHTML = `
      <div class="toast-header">
        <strong class="me-auto">${title}</strong>
        <small></small>
        ${closeButtonHTML}
      </div>
      <div class="toast-body">
        ${message}
      </div>`;
  parentContainer.insertBefore(toastEl, parentContainer.firstChild);
  
  var toast = new bootstrap.Toast(toastEl, options);
  toast.show();

  // add to toasts array.  Index in array is retained even when elements are
  // deleted, and length never decreases.
  toasts.push(toast);
  return toasts.length - 1;
}

function error(msg) {
  return makeToast("error", msg, {autohide: false});
}

function warning(msg) {
  return makeToast("alert", msg, {autohide: false});
}

function status(msg) {
  return makeToast("info", msg, {autohide: false, noClose: true});
}

function status_clear(id) {
  /* I would expect toasts[id].dispose() to replace the next three lines but
   * instead it always throws an exception that _element is NULL, which is
   * what removing the DOM element manually presumably does.
   */
  var parent = document.getElementById('toast-container');
  parent.removeChild(toasts[id]._element);
  toasts[id].hide();

  // this removes the element from the array, leaving an empty slot and
  // without actually shortening the array, so other elements' indices remain
  // unchanged
  delete toasts[id];
}
