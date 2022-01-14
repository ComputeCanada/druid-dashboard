
class Preferences {
  constructor(cookie_name) {
    this._cookie = cookie_name;
    var prefsJSON = Cookies.get(cookie_name, { 'SameSite': 'strict' });
    if (prefsJSON) {
      this._prefs = JSON.parse(prefsJSON);
    } 
    else {
      this._prefs = {};
    }
  }

  write() {
    var prefsJSON = JSON.stringify(this._prefs);
    Cookies.set(this._cookie, prefsJSON, { 'SameSite': 'strict' });
  }
  
}

class AdminPreferences extends Preferences {
  getActiveTab() {
    return this._prefs['activeTab'] || 'authz';
  }

  setActiveTab(tab_id) {
    this._prefs['activeTab'] = tab_id;
    this.write();
  }
}

const admin_prefs = new AdminPreferences("admin_prefs");
