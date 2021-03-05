function generate_api_key() {
  ar = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q',
        'R','S','T','U','V','W','X','Y','Z','a','b','c','d','e','f','g','h',
        'i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y',
        'z','0','1','2','3','4','5','6','7','8','9','+','/'];
  ba = []
  for (let i=0; i<64; i++) {
    ba[i] = ar[Math.floor(Math.random() * 64)];
  }
  bs = ba.join('');
  return(bs);
}

function get_form_values(form) {
  let elements = form.elements;
  let arr = {};
  for (let i=0; i<elements.length; i++) {
    let item = elements.item(i);
    arr[item.name] = item.value;
  }
  return arr;
}

/**
 * Determine preferred language from user agent.
 *
 * @returns {String} The two-character major language code.
 */
function preferred_language() {
  for (var i = 0; i < navigator.languages.length; i++) {
    if (['en', 'fr'].includes(navigator.languages[i])) {
      return(navigator.languages[i]);
    }
  }
  return('en');
}


function epoch_to_local_time(epoch) {
  // epochs in Javascript are milliseconds but we're using seconds
  var d = new Date(epoch * 1000);
  return(d.toLocaleString());
}

/* --------------------------------------------------------------------------
                                                       bootstrap helpers
-------------------------------------------------------------------------- */

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

  $(parentSelector).append(`
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
  var toast = $('#toast-container').children().toArray()[0];
  return new bootstrap.Toast(toast, options);
}
