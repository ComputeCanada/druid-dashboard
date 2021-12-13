i18n_strings = {
    // basic reusable stuff
    "CANCEL": "Cancel",
    "SUBMIT": "Submit",
    "REVERT": "Revert",
    "TITLE": "Title",
    "BODY": "Body",

    // used for accordion headers, like "Bursts candidates - reported 2021-11-22 03:42 a.m."
    "REPORT_HEADER": "$1 - reported $2",

    // generic info
    "NO_REPORTS": "There are no current reports for this cluster.",

    // info and error alert titles
    "INFO": "Info",
    "ALERT": "Alert",
    "ERROR": "Error",

    // info and error alert messages
    "RETRIEVING_CLUSTER_INFO": "Retrieving cluster info...",
    "FAILED_TO_RETRIEVE_CLUSTER_INFO": "Failed to retrieve cluster info",
    "RETRIEVING_CASE_REPORTS": "Retrieving case reports for $1...",
    "FAILED_TO_RETRIEVE_CASE_REPORTS": "Failed to retrieve case reports",
    "RETRIEVING_CASE_INFO": "Retrieving case info...",
    "FAILED_TO_RETRIEVE_CASE_INFO": "Failed to retrieve case info",
    "RETRIEVING_EVENTS": "Retrieving events...",
    "FAILED_TO_RETRIEVE_EVENTS": "Failed to retrieve events",
    "UPDATING": "Updating...",
    "UPDATE_FAILED": "Failed to update",
    "CREATING_NOTE": "Creating note...",
    "FAILED_TO_CREATE_NOTE": "Failed to create note",
    "STEALING_CASE": "Stealing case",
    "FAILED_TO_STEAL_CASE": "Failed to steal case",
    "CLAIMING_CASE": "Claiming case",
    "FAILED_TO_CLAIM_CASE": "Failed to claim case",
    "RETRIEVING_TEMPLATE": "Retrieving template...",
    "UNABLE_TO_RETRIEVE_TEMPLATE": "Unable to retrieve template of type $1",
    "CREATING_TICKET_FOR_USER": "Creating ticket for user $1...",
    "CREATION_OF_TICKET_FAILED": "Creation of ticket failed",
    "LOADING_HISTORY": "Loading history...",
    "RELEASING_CASE": "Releasing case",
    "FAILED_TO_RELEASE_CASE": "Failed to release case",
    "CASE_HISTORY": "Case history",
    "REJECTING_BURST_CANDIDATE": "Rejecting burst candidate...",
    "REJECTING_BURST_CANDIDATE_FAILED": "Rejecting burst candidate failed",
    "ACCEPTING_BURST_CANDIDATE": "Accepting burst candidate...",
    "ACCEPTING_BURST_CANDIDATE_FAILED": "Accepting burst candidate failed",

    // application info
    "ABOUT": "About",
    "ABOUT_CONTENT": `<p>Druid (<b>D</b>ashboard for <b>R</b>esearcher
<b>U</b>sage <b>I</b>ssues <b>D</b>etermination) is a web application
supporting the analysis of problematic usage patterns in our resources and
followup communication with users.</p>

<p><a href='https://git.computecanada.ca/frak/burst/manager'>View the
source</a>.</p><p>Please <a
href='https://git.computecanada.ca/frak/burst/manager/-/issues'>report any
issues</a> you may find.</p>`,
    "VERSION": "Version: $1",

    // history modal and related strings
    "HISTORY": "History",
    "EVENT_UPDATE": "Updated from <strong>$1</strong> to <strong>$2</strong>",
    "EVENT_CLEARED": "Cleared (was <strong>$1</strong>)",
    "EVENT_SET": "Set to <strong>$1</strong>",
    "HISTORY_TITLE": "Update to $1",
    "NOTE_TITLE": "Note",

    // action buttons.  "THING" is the action name and title on modal;
    // "THING_CONTENT" is the modal text description, "THING_SUBMIT" is the
    // label for the modal's submit button.
    "REJECT": "Reject",
    "REJECT_SUBMIT": "Reject",
    "REJECT_CONTENT": `By rejecting this burst candidate you are indicating
it's not of interest for bursting.`,
    "ACCEPT": "Accept",
    "ACCEPT_SUBMIT": "Accept",
    "ACCEPT_CONTENT": `By accepting this burst candidate you are confirming this
account is eligible for elevated access to resources.`,
    "NOTE": "Note",
    "NOTE_CONTENT": "This note will become part of the case history.",
    "NOTE_SUBMIT": "Leave note",
    "STEAL": "Steal",
    "STEAL_SUBMIT": "Steal",
    "STEAL_CONTENT": `By stealing this case you indicate you will follow up
with the analysis of this job set and with the research group, as necessary.`,
    "CLAIM": "Claim",
    "CLAIM_SUBMIT": "Claim",
    "CLAIM_CONTENT": `By claiming this case you indicate you will follow up
with the analysis of this job set and with the research group, as necessary.`,
    "RELEASE": "Release",
    "RELEASE_SUBMIT": "Release",
    "RELEASE_CONTENT": `By releasing this case you make it available to be
claimed by another analyst.  This does not affect ownership of the associated
ticket.`,

    // ticket creation modal and related strings
    "CREATE_TICKET": "Create ticket",
    "CREATE_TICKET_CONTENT": `Some types of outreach allow specification of a
recipient other than the account's PI, based on those submitting jobs to this
account.`,
    "SELECT_TEMPLATE": "Select what sort of outreach you want to initiate:",
    "SELECT_TEMPLATE_SHORT": "Choose outreach type",
    "SELECT_TEMPLATE_EMPTY": "Empty",
    "SELECT_RECIPIENT": "Select recipient:",
    "CREATE_TICKET_COMPOSE": "Compose",
    "COMPOSE_MESSAGE": "Create ticket: Compose message",
    "COMPOSE_MESSAGE_CONTENT": `<strong>Note</strong>: Continuing with this
operation will create a ticket and send an outgoing e-mail to the PI
associated with this account, or another recipient as selected.`,
    "CREATE_TICKET_SELECT_TEMPLATE": "Create ticket: select template",
    "AGREE_EMAIL": "Agree to send e-mail",
    "NAME_PI": "$1 (PI)", 

    "ACTION": "Action",
    // ex. Claimed by Drew (2021-04-21 08:09 a.m.)
    "EVENT_HEADER": "$1 by $2 ($3)",
    
}
