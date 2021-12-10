// inspired in part by https://codeburst.io/translating-your-website-in-pure-javascript-98b9fa4ce427
"use strict"

class I18n {
  constructor(languages) {

    this._lang = null;
    if (languages.includes(navigator.language.substr(0,2))) {
      this._lang = navigator.language.substr(0,2);
      this._langFull = navigator.language;
    }
    else {
      // navigator.languages is experimental, though widely supported
      // https://developer.mozilla.org/en-US/docs/Web/API/Navigator/languages
      for (var i = 0; i < navigator.languages.length; i++) {
        if (languages.includes(navigator.languages[i].substr(0,2))) {
          this._lang = navigator.languages[i].substr(0,2);
          this._langFull = navigator.languages[i];
          console.log(`Chose ${this._lang} as language from navigator.languages`);
          break;
        }
      }
    }

    if (!this._lang) {
      // best we can do is to assume Canadian English
      this._lang = 'en';
      this._langFull = 'en_CA';
    }

    // find all translatable elements
    this._elements = document.querySelectorAll("[data-i18n]");
  }

  load() {
    fetch(`/static/i18n/${this._lang}.json`)
      .then((res) => res.json())
      .then((strings) => {
        this.translate_static(strings);
        this._strings = strings;
      })
      .catch(() => {
        console.error(`Could not load ${this._lang}.json.`);
      }
    );
  }

  translate_static(translations) {
    this._elements.forEach((element) => {
      var name = element.dataset.i18n;
      var text = translations[name];
      if (text) {
        element.innerHTML = text;
      } else {
        element.innerHTML = "NOT DEFINED";
      }
    });
  }

  translate() {
    var message = arguments[0];
    console.log(`Let's find a translation for ${message}`);
    var translation = this._strings[message];
    if (!translation) {
      return("NOT DEFINED");
    }

    var args = arguments;
    function replacer(match, offset, string) {
      console.log(`match = ${match}, offset = ${offset}, string = ${string}`);
      return args[offset];
    }
    if (arguments.length > 1) {
      return translation.replaceAll(/\$(\d+)/g, replacer);
    }

    return translation;
  }
}
