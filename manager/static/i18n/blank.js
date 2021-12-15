// loading this instead of a real language file can help identify elements
// that still require translation

i18n_strings = {
    // basic reusable stuff
    "CANCEL": "C#####",
    "SUBMIT": "S#####",
    "REVERT": "R#####",
    "TITLE": "T####",
    "BODY": "B###",

    // used for accordion headers, like "Bursts candidates - reported 2021-11-22 03:42 a.m."
    "REPORT_HEADER": "$1 - ######## $2",

    // generic info
    "NO_REPORTS": "T#### ### ## ####### ####### ### #### #######.",

    // info and error alert titles
    "INFO": "I###",
    "ALERT": "A####",
    "ERROR": "E####",

    // info and error alert messages
    "RETRIEVING_CLUSTER_INFO": "R######### ####### ####...",
    "FAILED_TO_RETRIEVE_CLUSTER_INFO": "F##### ## ######## ####### ####",
    "RETRIEVING_CASE_REPORTS": "R######### #### ####### ### $1...",
    "FAILED_TO_RETRIEVE_CASE_REPORTS": "F##### ## ######## #### #######",
    "RETRIEVING_CASE_INFO": "R######### #### ####...",
    "FAILED_TO_RETRIEVE_CASE_INFO": "F##### ## ######## #### ####",
    "RETRIEVING_EVENTS": "R######### ######...",
    "FAILED_TO_RETRIEVE_EVENTS": "F##### ## ######## ######",
    "UPDATING": "U#######...",
    "UPDATE_FAILED": "F##### ## ######",
    "CREATING_NOTE": "C####### ####...",
    "FAILED_TO_CREATE_NOTE": "F##### ## ###### ####",
    "STEALING_CASE": "S####### ####",
    "FAILED_TO_STEAL_CASE": "F##### ## ##### ####",
    "CLAIMING_CASE": "C####### ####",
    "FAILED_TO_CLAIM_CASE": "F##### ## ##### ####",
    "RETRIEVING_TEMPLATE": "R######### ########...",
    "UNABLE_TO_RETRIEVE_TEMPLATE": "U##### ## ######## ######## ## #### $1",
    "CREATING_TICKET_FOR_USER": "C####### ###### ### #### $1...",
    "CREATION_OF_TICKET_FAILED": "C####### ## ###### ######",
    "LOADING_HISTORY": "L###### #######...",
    "RELEASING_CASE": "R######## ####",
    "FAILED_TO_RELEASE_CASE": "F##### ## ####### ####",
    "CASE_HISTORY": "C### #######",
    "REJECTING_BURST_CANDIDATE": "R######## ##### #########...",
    "REJECTING_BURST_CANDIDATE_FAILED": "R######## ##### ######### ######",
    "ACCEPTING_BURST_CANDIDATE": "A######## ##### #########...",
    "ACCEPTING_BURST_CANDIDATE_FAILED": "A######## ##### ######### ######",

    // application info
    "ABOUT": "#####",
    "ABOUT_CONTENT": `<p>##### (<b>D</b>######## for <b>R</b>#########
<b>U</b>#### <b>I</b>##### <b>D</b>############) ## # ### ###########
########## ### ######## ## ########### ##### ######## ## ### ######### ###
######## ############# #### #####.</p>

<p><a href='https://git.computecanada.ca/frak/burst/manager'>#### ###
######</a>.</p><p>###### <a
href='https://git.computecanada.ca/frak/burst/manager/-/issues'>###### ###
######</a> ### ### ####.</p>`,
    "VERSION": "#######: $1",

    // history modal and related strings
    "HISTORY": "H######",
    "EVENT_UPDATE": "U###### #### <strong>$1</strong> ## <strong>$2</strong>",
    "EVENT_CLEARED": "C###### (### <strong>$1</strong>)",
    "EVENT_SET": "S## ## <strong>$1</strong>",
    "HISTORY_TITLE": "U##### ## $1",
    "NOTE_TITLE": "N###",

    // action buttons.  "THING" is the action name and title on modal;
    // "THING_CONTENT" is the modal text description, "THING_SUBMIT" is the
    // label for the modal's submit button.
    "REJECT": "R#####",
    "REJECT_SUBMIT": "R#####",
    "REJECT_CONTENT": `B# ######### #### ##### ######### ### ### ##########
##'# ### ## ######## ### ########.`,
    "ACCEPT": "A#####",
    "ACCEPT_SUBMIT": "A#####",
    "ACCEPT_CONTENT": `B# ######### #### ##### ######### ### ### ########## ####
####### ## ######## ### ######## ###### ## #########.`,
    "NOTE": "N###",
    "NOTE_CONTENT": "T### #### #### ###### #### ## ### #### #######.",
    "NOTE_SUBMIT": "L#### ####",
    "STEAL": "S####",
    "STEAL_SUBMIT": "S####",
    "STEAL_CONTENT": `B# ######## #### #### ### ######## ### #### ###### ##
#### ### ######## ## #### ### ### ### #### ### ######## #####, ## #########.`,
    "CLAIM": "C####",
    "CLAIM_SUBMIT": "C####",
    "CLAIM_CONTENT": `B# ######## #### #### ### ######## ### #### ###### ##
#### ### ######## ## #### ### ### ### #### ### ######## #####, ## #########.`,
    "RELEASE": "R######",
    "RELEASE_SUBMIT": "R######",
    "RELEASE_CONTENT": `B# ######### #### #### ### #### ## ######### ## ##
####### ## ####### #######.  T### #### ### ###### ######### ## ### ##########
######.`,

    // ticket creation modal and related strings
    "CREATE_TICKET": "C##### ######",
    "CREATE_TICKET_CONTENT": `S### ##### ## ######## ##### ############# ## #
######### ##### #### ### #######'# PI, ##### ## ##### ########## #### ## ####
#######.`,
    "SELECT_TEMPLATE": "S##### #### #### ## ######## ### #### ## ########:",
    "SELECT_TEMPLATE_SHORT": "C##### ######## ####",
    "SELECT_TEMPLATE_EMPTY": "E####",
    "SELECT_RECIPIENT": "S##### #########:",
    "CREATE_TICKET_COMPOSE": "C######",
    "COMPOSE_MESSAGE": "C##### ######: C###### #######",
    "COMPOSE_MESSAGE_CONTENT": `<strong>N###</strong>: C######### #### ####
######### #### ###### # ###### ### #### ## ######## #-#### ## ### PI
########## #### #### #######, ## ####### ######### ## ########.`,
    "CREATE_TICKET_SELECT_TEMPLATE": "C##### ######: ###### ########",
    "AGREE_EMAIL": "A#### ## #### #-####",
    "NAME_PI": "#### $1 (PI)",

    "ACTION": "A#####",
    // ex. Claimed by Drew (2021-04-21 08:09 a.m.)
    "EVENT_HEADER": "#### $1 ## $2 ($3)",
}

