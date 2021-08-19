# 

[[_TOC_]]

## Module

### Functions

  

---

####  <code>make_graphs_links(cluster, account, resource)</code>

  

  

  

  

---

####  <code>prettify_summary(original)</code>

  

  

  

## Classes
    

###  Burst

<code>class <b>Burst</b>(id=None, record=None, cluster=None, epoch=None, account=None, resource=CPU, pain=None, jobrange=None, submitters=None, state=PENDING, summary=None, other=None)</code>

  

  
Represents a burst candidate.
  

**Arguments**

* **`id`**: Unique identifier for the case.
* **`record`**: Dictionary describing all the values for the case.  This is used
    to efficiently instantiate multiple objects from a multiple-row query,
    or other examples of factory loading.
* **`cluster`**: The cluster where this case occurred.
* **`epoch`**: The UNIX epoch (UTC) when this case was (last) reported.
* **`summary`**: A dictionary of arbitrary information supplied by the Detector
    which may be of use to analysts in addressing the case.

  
**Attributes**

* **`_id`**: id
* **`_cluster`**: cluster ID referencing entry in cluster table
* **`_account`**: account name (such as 'def-dleske-ab')
* **`_resource`**: resource type (type burst.Resource)
* **`_pain`**: pain metric used as initial indicator of burst candidacy
* **`_jobrange`**: tuple of first and last job IDs in burst
* **`_submitters`**: submitters associated with the jobs
* **`_state`**: state of burst (type burst.State)
  # Common Reportables stuff
* **`_summary`**: summary information about burst and jobs (JSON)
* **`_epoch`**: epoch timestamp of last report
* **`_ticks`**: number of times reported
* **`_claimant`**: analyst following up
* **`_ticket_id`**: associated ticket's ID
* **`_ticket_no`**: associated ticket's number

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

  

#### Ancestors
  * [Case](docs/case.md#Case)

  

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

####  static <code>report(cluster, epoch, data)</code>

  

  
Report potential job and/or account issues.
  

**Arguments**

* **`cluster`**: reporting cluster
* **`epoch`**: epoch of report (UTC)
* **`data`**: list of dicts describing current instances of potential account
        or job pain or other metrics, as appropriate for the type of
        report.

  
**Returns**

String describing summary of report.

  

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

  

  
Return dict describing view of data reported.
  

**Arguments**

* **`criteria`**: dict of criteria for selecting data for view.  Accepted by the
            Burst class are `cluster` and `view`.

  
**Returns**

Dict describing view of data reported, formatted depending on the
requested view.  For basic cluster view, in the format:
```
epoch: <seconds since epoch>
results:
  - obj1.attribute1
  - obj1.attribute2
  - ..
  - obj2.attribute1
  - obj2.attribute2
  - ..
```
For "adjustor" view:
```
```

  

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

####  <code>update_existing_me(self, rec)</code>

  

  
Updates the subclass's partial record of an existing case.  Subclasses
must implement this to write to the database the appropriate values of
a case's latest report.
  

---

#### Variables

  
    
* `account`
    
* `contact` - Return contact information for this potential issue.  This can depend on
the type of issue: a PI is responsible for use of the account, so the PI
should be the contact for questions of resource allocation.  For a
misconfigured job, the submitting user is probably more appropriate.

  Returns: username of contact.
    
* `info` - Some information about this case, used for passing on to templates.
    
* `resource`
    
* `state`
    
* `submitters`

      

---
    

###  Resource

<code>class <b>Resource</b>(*args)</code>

  

  
An enumeration.
  

#### Ancestors
  * [DbEnum](docs/db.md#DbEnum)
  * [Enum](docs/Enum.md)

---

#### Variables

  
    
* static `CPU`
    
* static `GPU`

      

---
    

###  State

<code>class <b>State</b>(*args)</code>

  

  
An enumeration.
  

#### Ancestors
  * [DbEnum](docs/db.md#DbEnum)
  * [Enum](docs/Enum.md)

---

#### Variables

  
    
* static `ACCEPTED`
    
* static `PENDING`
    
* static `REJECTED`

      

---

---
Generated by [pdoc 0.9.2](https://pdoc3.github.io/pdoc).
