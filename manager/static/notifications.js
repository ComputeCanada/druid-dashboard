// NOTIFICATIONS
// This mechanism adapted from
// https://developer.mozilla.org/en-US/docs/Web/API/Notifications_API/Using_the_Notifications_API

function handleNoNotifications(msg) {
  console.log("No notifications: " + msg);

  // show "refresh <stuff>" link
  var link = document.getElementById("refresh_content_link");
  link.style.display = "block";
}

function handlePermission(permission) {

  // make sure Chrome stores the information
  if (!('permission' in Notification)) {
    Notification.permission = permission;
  }

  if (Notification.permission === 'denied' || Notification.permission === 'default') {
    handleNoNotifications("Denied by user.");
  } else {
    // set up notifications listener
    var targetContainer = document.getElementById("notification");
    var eventSource = new EventSource("/notifications");

    eventSource.onmessage = function(e) {

      // "refresh" notification needs no other processing, just refresh
      if (e.data != "refresh") {
        // if window is in focus or notifications are disabled
        if (document.hasFocus() || Notification.permission != "granted") {
          // TODO: really mixing jQuery and vanilla JS here
          $("#notification").show();
          targetContainer.innerHTML = e.data;
        }
        else {
          var notification = new Notification(e.data)
          notification.onshow = function() { setTimeout(notification.close, 15000) }
        }
      }
      refresh_content();
    };
  }
}

function checkNotificationPromise() {
  try {
    Notification.requestPermission().then();
  } catch(e) {
    return false;
  }
  return true;
}

// set up notifications...
// first check if browser supports them
if (!('Notification' in window)) {
  handleNoNotifications("Browser does not suppoert");
} else {
  if (checkNotificationPromise()) {
    Notification.requestPermission().then((permission) => {
      handlePermission(permission);
    })
  } else {
    Notification.requestPermission(function(permission) {
      handlePermission(permission);
    });
  }
}
