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

function timestamp_to_local_time(timestamp) {
  var d = new Date(timestamp);
  return(d.toLocaleString());
}

/**
 * Extract numerical ID from DOM ID such as "burst_234".
 *
 * @param id {String} ID string of format "text_number"
 * @returns {Integer} the number part, as a number.
 */
function numerical_part(id) {
  var re = /^[a-zA-Z]*_([0-9]+)$/
  return Number(id.match(re)[1]);
}
