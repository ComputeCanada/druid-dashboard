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

function copy_to_clipboard(el) {
  el.focus();
  el.select();
  try {
    let successful = document.execCommand('copy');
    let msg = successful ? 'successful' : 'unsuccessful';
  } catch (err) {
  }
}

/**
 * Determine preferred language from user agent.
 *
 * @param supported {Array} List of language codes supported by the
 *   application, ordered by preference.
 * @returns {String} The two-character major language code.
 */
function preferred_language(supportedLanguages) {

  // if primary language defined by browser is supported, use that
  if (navigator.language.slice(0,2) in supported) {
    return(navigator.language.slice(0,2));
  }

  // navigator.languages is experimental, though widely supported
  // https://developer.mozilla.org/en-US/docs/Web/API/Navigator/languages
  for (var i = 0; i < navigator.languages.length; i++) {
    if (supported.includes(navigator.languages[i].slice(0,2))) {
      return(navigator.languages[i].slice(0,2));
    }
  }

  // best we can do is to assume English: in 2001, 86% of Canadians understand
  // English and 32% understand French
  // https://en.wikipedia.org/wiki/Languages_of_Canada, "Bilingualism and
  // multilingualism vs English-French bilingualism"
  return('en'); }

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
