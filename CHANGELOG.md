# Changelog

## v0.6 (2021-10-20) Generalization beyond bursting

Generalized to support different usage pain metrics.

Added:
* Case class, of which bursts are now a subclass.
* AJAX calls for cluster and component management.
* API documentation for developers of new Case subclasses.
* Limited unit testing.

Changed:
* Overhauled testing to rely more heavily on seed data and less on the success
  of previous tests.
* Simplified upgrade testing to support only specific upgrades using seed data
  appropriate for the source schema version.
* Retire SQLite schema upgrades and associated testing.
* Templates now use variables embedded `{like_this}` rather than `%this_way%`.
* API now at version 2.  Detectors must report slightly differently.
* Depersonalized test data (ex. use "pi1" instead of "dleske") and normalized
  LDAP stub data and LDAP test container.

Updated:
* Documentation (particularly in development and testing). 

## v0.5 (2021-05-13) Allow tickets to non-PI submitters

Added:
* Tickets for some types of issues can be created with one of the submitters
  instead of the PI.

Updated:
* Submitters are now properly updated on burst reports.

## v0.4 (2021-05-07) Two-step ticket creation

Added:
* Ticket creation now split into two steps and allows editing of title and text
  before sending.
* Configurable alternative location for externally sourced static resources.
* Event notification testing.

Updated:
* Use toast notifications for all status and errors instead of flash area.
* Use upper-right corner consistently for notifications.
* Use application tag in event notifications.

Fixed:
* Toast notifications properly handling multiple concurrent messages.
* Problem with partially loaded Burst objects appearing in report
  notifications.
* No longer displaying "undefined" in event history for unset fields.

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
