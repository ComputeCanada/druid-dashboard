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

