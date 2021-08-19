# Case module: the foundation for reporting problem cases

Subclass the Case class to support a new type of reportable problem
metrics.  The original use case for this was burst candidates: accounts with
significant short-term need that can't be readily met by the resources
typically available without a RAC.

Use the CaseRegistry class to register new case classes so that the
application is aware of them: knows to query them for data to display on the
dashboard and can serve them appropriately via the REST API.

Helper functions provide some common functionality and may be of use to
subclasses.  If creating a utility function for a new subclass, consider
whether it may be of use to other case types.

[[_TOC_]]

## Module

### Functions

  

---

####  <code>dict_to_table(d)</code>

  

  
Given a dictionary, return a basic HTML table.

Turns the keys and values of the dictionary into a two-column table where
the keys are header cells (`TH`) and the values are regular cells (`TD`).
There is no header row and any complexity in the values are ignored (for
example there is no hierarchical tabling).
  

**Arguments**

* **`d`**: A dictionary.

  
**Returns**

A basic HTML table to display that dictionary in the simplest possible
way.

  

---

####  <code>json_to_table(str)</code>

  

  
Given a JSON string representing a dictionary, return an HTML table.

See `dict_to_table()` for more detail.
  

**Arguments**

* **`str`**: A JSON string representation of a dictionary.

  
**Returns**

A basic HTML table.

  

---

####  <code>just_job_id(jobid)</code>

  

  
Strip job ID to just the base ID, not including any array part.
  

**Arguments**

* **`jobid`**: Job identifier, optionally including array part.

  
**Returns**

Integer job identifier.

## Classes
    

###  Case

<code>class <b>Case</b>(id=None, record=None, cluster=None, epoch=None, summary=None)</code>

  

  
Base class for reportable metrics of concern.

The Case class defines methods or stubs necessary to support representing
and reporting potential problem cases.

Subclasses of this class implement a single instance of a reportable case.
For example, an instance of the OldJob class represents an account on a
cluster with really old jobs.  Tomorrow if that account still has really old
jobs, it'll be reported again (via the appropriate subclass of
`manager.reporter.Reporter`) but it will still be the same instance, though
some of the details may change.

Instances of these subclasses are represented in the database by a row in
each of two tables: the reportables table, which stores information common
to all types, and in a table specific to the subclass.

Additionally subclasses define methods for reporting and presenting problem
cases.

Subclasses must implement some methods and may override others, as
documented.  Methods implemented here merely as stubs will throw
`NotImplementedError` if called.

There are three modes for creating a Case object:

1.  Lookup by ID.  Specify the ID but NOT the record.
2.  Factory loading by specifying a database record (row).  Specify the
    record but not the ID.
3.  Creating a "new" Case specifying information about it.  Note that it
    may be that an existing case is found matching enough of the
    information to be effectively the same case.  Both `id` and `record`
    should not be set.

Subclasses will need to override this method but _must_ invoke the base
implementation via `super().__init__()` to ensure the entire object is
initialized and persisted.
  

**Arguments**

* **`id`**: Unique identifier for the case.
* **`record`**: Dictionary describing all the values for the case.  This is used
    to efficiently instantiate multiple objects from a multiple-row query,
    or other examples of factory loading.
* **`cluster`**: The cluster where this case occurred.
* **`epoch`**: The UNIX epoch (UTC) when this case was (last) reported.
* **`summary`**: A dictionary of arbitrary information supplied by the Detector
    which may be of use to analysts in addressing the case.

  

#### Subclasses
  * [Burst](docs/burst.md#Burst)
  * [OldJob](docs/oldjob.md#OldJob)

  

---

####  static <code>describe()</code>

  

  
Describe report structure and semantics.

The results of this method are used to meaningfully present the report data
(provided by other methods).  For example, these descriptions can be used
to inform UI templates what columns should appear in the report table on
the Dashboard.

The data returned has the following structure:
```
{
  table: str,       # table name in database
  title: str,       # display title of report
  metric: str,      # primary metric of interest
  cols: [{          # ordered list of field descriptors
    datum: ..,      # name of reported data field
    title: ..,      # display label (such as for column header)
    searchable: .., # should column data be included in searches
    sortable: ..,   # should table be sortable on this column
    type: ..,       # type (text or number, used for display)
    help: ..        # help text, displayed when hovering over title
  }, ... ],
}
```
  

**Returns**

A data structure conforming to the above.

**Note**

Subclasses _must not_ override this function.  Instead, subclasses
_must_ override `Case.describe_me()` to describe the specifics of
that case and this method will combine the common and specific field
descriptions.

  

---

####  static <code>describe_me()</code>

  

  
Describe report structure and semantics specific to case type.

Subclasses should implement this to describe the table name, report title,
and the primary metric of the case type as well as columns specific to
and implemented by the subclass.  The Case class will call this method
from `Case.describe()` to generate the full report.

All fields are required with the exception of `help`.

The data returned has the following structure:
```
{
  table: str,       # table name in database
  title: str,       # display title of report
  metric: str,      # primary metric of interest
  cols: [{          # ordered list of field descriptors
    datum: ..,      # name of reported data field
    title: ..,      # display label (such as for column header)
    searchable: .., # should column data be included in searches
    sortable: ..,   # should table be sortable on this column
    type: ..,       # type (text or number, used for display)
    help: ..        # help text, displayed when hovering over title
  }, ... ],
}
```
  

**Returns**

A data structure conforming to the above.

  

---

####  static <code>get(id)</code>

  

  
Find and load the appropriate Case object given the ID.

Case IDs are unique among all subclasses.  In the database, they are
stored in the common reportables table and referenced from the
subclass-specific table.

This implementation tries to instantiate each of the registered case
classes using the given ID.  This is not efficient or graceful.
  

**Arguments**

* **`id`**: The numeric ID of the case.

  
**Returns**

An instance of the appropriate case class with that ID, or None.

  

---

####  static <code>get_current(cluster)</code>

  

  
Get the current cases for this type of report.
  

**Arguments**

* **`cluster`**: The identifier for the cluster of interest.

  
**Returns**

A list of appropriate case objects, or None.

  

---

####  static <code>report(cluster, epoch, data)</code>

  

  
Report potential job and/or account issues.

Subclasses must implement this to interpret reports coming through the API
from a Detector.  Those implementations should describe the expected
format of the `data` argument and should call `Case.summarize_report()`
to provide a summary as return value.
  

**Arguments**

* **`cluster`**: The reporting cluster.
* **`epoch`**: Epoch of report (UTC).
* **`data`**: A list of dicts describing current instances of potential account
        or job pain or other metrics, as appropriate for the type of
        report.

  
**Returns**

String describing summary of report.

  

---

####  static <code>set_ticket(id, ticket_id, ticket_no)</code>

  

  
Set the ticket information for a given case ID.

This is a convenience function that avoids actually finding and
instantiating the matching case.
  

**Arguments**

* **`id`**: The case ID.
* **`ticket_id`**: The OTRS ticket ID.
* **`ticket_no`**: The OTRS ticket number.

  
**Notes**

The ticket ID and number are confusing and meaningful only to OTRS.
The Dude abides.

  

---

####  static <code>summarize_report(cases)</code>

  

  
Provide a brief, one-line summary of last report.

The intended use case for this summary is for notifications, such as to
Slack, when a report is received and interpreted.

Subclasses may override this method to provide additional information.
  

**Arguments**

* **`cases`**: The list of cases created or updated from the last report.

  
**Returns**

A string description of the last report.

  

---

####  static <code>view(criteria)</code>

  

  
Provide view to reported data.

By default, provides current view of reported data.  Subclasses may
override this to provide additional views.

The view is described as follows:
```
epoch: seconds since epoch
results:
  - obj1.attribute1: ..
    obj1.attribute2: ..
    obj1.attribute2_pretty: ..
    obj1.attribute3: ..
    ...
  - obj2.attribute1: ..
    obj2.attribute2: ..
    obj2.attribute2_pretty: ..
    obj2.attribute3: ..
    ...
  ...
```

Attributes suffixed with `_pretty` provide display versions of those
attributes without, if appropriate and requested.
  

**Arguments**

* **`criteria`**: Dict of criteria for selecting data for view.  In this
  implementation, `cluster` is required and `pretty` is optional.
    * `cluster`: (required) Cluster for which to provide data.
    * `pretty`: (optional, default False): provide display-friendly
      alternatives on some fields, if possible.

  
**Returns**

None or a data structure conforming to the above.

**Raises**

* **`NotImplementedError`**: Criteria other than `pretty` or `cluster` were
    specified, indicating this method should have been overridden by a
    subclass and was not.
  

  

---

####  <code>find_existing_query(self)</code>

  

  
Returns partial query and terms to complete the SQL_FIND_EXISTING query.
Essentially, query and terms are used to complete the WHERE clause begun
with `WHERE cluster = ? AND`.

Subclasses MUST implement this to enable detection of when a reported
record matches one already in the database.
  

**Returns**

A tuple (query, terms, cols) where:
  - `query` (string) completes the WHERE clauses in SQL_FIND_EXISTING,
  - `terms` (list) lists the search terms in the query, and
  - `cols` (list) lists the columns included in the selection.

  

---

####  <code>insert_new(self)</code>

  

  
Subclasses must implement this method to insert a new record in their
associated table.  This method is called by the base class after the base
record has been created in the "reportables" table and an ID is available
as `self._id`, which the subclass can use in the database to link records
in its table to the reportables table.
  

  

---

####  <code>serialize(self, pretty=False, options=None)</code>

  

  
Provide a dictionary representation of self.

By default, simply returns a dictionary of attributes with leading
underscores removed.  If `pretty` is specified, the dictionary may be
augmented with prettified versions of some attributes, depending on the
implementation.  In the base implementation, prettification includes:

* `claimant_pretty` is included if the value for `claimant` is found in
  LDAP and will be set to the person's given name.
* `ticket` is included if `ticket_id` is set and becomes an HTML anchor
  element for that ticket.
* `summary_pretty` is included if `summary` is set,
  `options['skip_summary_prettification']` is either unset or false, and
  is populated with an HTML table interpretation of the summary attribute.

In general, prettified attributes should compliment, not replace, the
originals, and the consumer may choose.

Subclasses may override this to provide their own prettification, and must
must call `super().serialize(...)` appropriately to ensure full
representation.  See existing subclasses for examples.
  

**Arguments**

* **`pretty`**: if True, prettify some fields
* **`options`**: optional dictionary of options

  
**Returns**

A dictionary representation of the case.

  

---

####  <code>update(self, update, who)</code>

  

  
Updates the appropriate record for a new note, change to claimant, etc.
Subclasses can implement this to intercept the change, such as to make a
value database-friendly, but should pass the execution back to the super
class which will execute the SQL statement.

A history record is created for the update.
  

**Arguments**

* **`update`**: A dict with `note` and/or `datum` and `value` defined describing
    the update.
* **`who`**: The CCI of the individual carrying out the change, that is, the
    logged-in user.
  

  

---

####  <code>update_existing(self)</code>

  

  
Handle updates to existing records.  This is called on initialization
to handle existing cases, as partially defined by subclasses (see
`find_existing_query()`).  Updates are also handled by subclass (see
`update_existing_me()`).

At this point this is called, self should be initialized with the
details provided, but this may need to be appropriately adjusted with
data from the matching case in the database.
  

**Returns**

A boolean indicating whether there was a record to update.

  

---

####  <code>update_existing_me(self, rec)</code>

  

  
Updates the subclass's partial record of an existing case.  Subclasses
must implement this to write to the database the appropriate values of
a case's latest report.
  

---

#### Variables

  
    
* `claimant` - The analyst that has signalled they will pursue this case.
    
* `cluster` - The cluster where this case originated.
    
* `contact` - Contact information for this potential issue.

  This can depend on the type of issue: a PI is responsible for use of the
account, so the PI should be the contact for questions of resource
allocation.  For a misconfigured job, the submitting user is probably more
appropriate.
    
* `epoch` - The most recent UNIX epoch (UTC) this case was reported.
    
* `id` - The numerical identifier of this case, assigned by the database as an
auto-incrementing sequence.
    
* `info` - Some information about this case, used for passing on to templates.
    
* `notes` - Notes associated with this case.
    
* `ticket_id` - The primary ticket identifier.  Numeric.
    
* `ticket_no` - The other primary ticket identifier.  Looks numeric.  Is not the same as
`ticket_id`.  Actually a string.
    
* `ticks` - The number of reports including this case.

      

---
    

###  CaseRegistry

<code>class <b>CaseRegistry</b>()</code>

  

  
Singular registry of case classes.

The application uses this registry to query available case types.
Subclasses of the Case class register so the application is aware of
them and knows to query and present different case types.

Basic usage:

```
# register class with reporter registry
registry.register('bursts', Burst)
```
  

**Attributes**

* **`reporters`**: Dict of case names to their classes.
  

  

---

####  static <code>get_registry()</code>

  

  
Return singular instance of registry.
  

  

---

####  <code>register(self, name, reporter)</code>

  

  
Register a Case implementation.

Subclasses of the `Case` class must register themselves so the application
knows to query these classes.  A subclass of the Case class must use this
method at the end of its module file.
  

**Arguments**

* **`name`**: The common name for the reporter type.  This name will be used,
    for example, when reporting via the API.  It is recommended it match
    the table name and be plural, for example, "bursts" or "oldjobs".
* **`reporter`**: The subclass.

  

---

#### Variables

  
    
* `descriptions` - Dictionary of reporter name to the data description provided by the
reporter.
    
* `reporters` - Dictionary of reporter name to class.

      

---

---
Generated by [pdoc 0.9.2](https://pdoc3.github.io/pdoc).
