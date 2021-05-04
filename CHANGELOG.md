# Changelog

## v0.3 (2021-05-03) Improve UI

Added:
* Burst candidate actions Steal, Release
* State transitions
* Configurable application tag
* Notes count in dashboard
* Input sanitization

Updated:
* Improved notes formatting (replacing successive line breaks with paragraph
  markers; no longer styles as preformatted)
* Fix ordering and cleanup of toasts (on-dash notifications)
* Frontend (Javascript) code simplifications

## v0.2 (2021-04-29) Improve container deployment

Added:
* Container images now use uWSGI app server
* Docker Compose file for (almost) full stack testing now available
* Support CSS and application title overrides in environment (to assist with
  differentiating development, production, etc. instances)

Removed:
* Unused notifications mechanism disabled.

Fixed:
* Properly reports lack of burst reports.

## v0.1 (2021-04-25) Initial Pilot release.


## v0.0 (2020-12-04) Empty app reusing SAW prototype with SAW-specific code removed.


