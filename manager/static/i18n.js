"use strict"

function i18n() {
  //return i18n_strings[i18n_key];
  var message = arguments[0];
  var translation = i18n_strings[message];
  if (!translation) {
    return(`"${message}" NOT DEFINED`);
  }

  var args = arguments;
  function replacer(match, offset, string) {
    return args[offset];
  }
  if (arguments.length > 1) {
    return translation.replaceAll(/\$(\d+)/g, replacer);
  }

  return translation;
}

// convenience alias for familiarity
var _ = i18n;

function i18n_static() {
  // find all translatable elements
  var elements = document.querySelectorAll("[data-i18n]");

  elements.forEach((element) => {
    var name = element.dataset.i18n;
    var text = i18n_strings[name];
    if (text) {
      element.innerHTML = text;
    } else {
      element.innerHTML = `"${name}" NOT DEFINED`;
    }
  });
}
