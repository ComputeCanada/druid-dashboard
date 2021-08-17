# Reportable class for implementing new types of problem metrics.

[[_TOC_]]

## Functions

    

####  dict_to_table: Given a dictionary, return a basic HTML table.

<code>def <b>dict_to_table</b>(d)</code>

  

  
Given a dictionary, return a basic HTML table.

Turns the keys and values of the dictionary into a two-column table where
the keys are header cells (`TH`) and the values are regular cells (`TD`).
There is no header row and any complexity in the values are ignored (for
example there is no hierarchical tabling).

**Arguments**

<dl>
  <dt>d</dt><dd>A dictionary.

</dd>
</dl>

**Returns**

  A basic HTML table to display that dictionary in the simplest possible
way.

  

    

####  json_to_table: Given a JSON string representing a dictionary, return an HTML table.

<code>def <b>json_to_table</b>(str)</code>

  

  
Given a JSON string representing a dictionary, return an HTML table.

See `dict_to_table()` for more detail.

**Arguments**

<dl>
  <dt>str</dt><dd>A JSON string representation of a dictionary.

</dd>
</dl>

**Returns**

  A basic HTML table.

  

## Classes
    

###  Reportable

<code>class <b>Reportable</b>(id=None, record=None, cluster=None, epoch=None, summary=None)</code>

  

  
A base class for reportable trouble metrics.

Subclasses of this class implement a single instance of a reportable case.
For example, an instance of the OldJob class represents an account on a
cluster with really old jobs.  Tomorrow if that account still has really old
jobs, it'll be reported again (via the appropriate subclass of
`manager.reporter.Reporter`) but it will still be the same instance, though
some of the details may change.

Instances of these subclasses are represented in the database by a row in
each of two tables: the reportables table, which stores information common
to all types, and in a table specific to the subclass.

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

<dl>
  <dt>id</dt><dd>Unique identifier for the case.</dd>
  <dt>record</dt><dd>Dictionary describing all the values for the case.  This is used
    to efficiently instantiate multiple objects from a multiple-row query,
    or other examples of factory loading.</dd>
  <dt>cluster</dt><dd>The cluster where this case occurred.</dd>
  <dt>epoch</dt><dd>The UNIX epoch (UTC) when this case was (last) reported.</dd>
  <dt>summary</dt><dd>A dictionary of arbitrary information supplied by the Detector
    which may be of use to analysts in addressing the case.

</dd>
</dl>

**Raises**

  `manager.exceptions.ResourceNotFound` if the ID (but no record) is
  supplied and no record with that ID can be found.
`manager.exceptions.BadCall` if a nonsensical combination of named
  arguments are supplied.

#### Subclasses
  * manager.burst.Burst
  * manager.oldjob.OldJob

#### Static methods

    

####  get: Find and load the appropriate Reportable object given the ID.

<code>def <b>get</b>(id)</code>

  

  
Find and load the appropriate Reportable object given the ID.

Reportable IDs are unique among all subclasses.  In the database, they are
stored in the common reportables table and referenced from the
subclass-specific table.

This implementation tries to instantiate each of the registered case
classes using the given ID.  This is not efficient or graceful.

**Arguments**

<dl>
  <dt>id</dt><dd>The numeric ID of the case.

</dd>
</dl>

**Returns**

  An instance of the appropriate case class with that ID, or None.

  

    

####  get_current: Get the current cases for this type of report.

<code>def <b>get_current</b>(cluster)</code>

  

  
Get the current cases for this type of report.

**Arguments**

<dl>
  <dt>cluster</dt><dd>The identifier for the cluster of interest.

</dd>
</dl>

**Returns**

  A list of appropriate reportable objects, or None.

  

    

####  set_ticket: Set the ticket information for a given case ID.

<code>def <b>set_ticket</b>(id, ticket_id, ticket_no)</code>

  

  
Set the ticket information for a given case ID.

This is a convenience function that avoids actually finding and
instantiating the matching case.

**Arguments**

<dl>
  <dt>id</dt><dd>The case ID.</dd>
  <dt>ticket_id</dt><dd>The OTRS ticket ID.</dd>
  <dt>ticket_no</dt><dd>The OTRS ticket number.

</dd>
</dl>

**Raises**

  DatabaseException if the execution fails.

**Notes**

  The ticket ID and number are confusing and meaningful only to OTRS.
The Dude abides.

  

#### Instance variables
        
<code>var <b>claimant</b></code>

  

  
The analyst that has signalled they will pursue this case.

        
<code>var <b>cluster</b></code>

  

  
The cluster where this case originated.

        
<code>var <b>contact</b></code>

  

  
Contact information for this potential issue.

This can depend on the type of issue: a PI is responsible for use of the
account, so the PI should be the contact for questions of resource
allocation.  For a misconfigured job, the submitting user is probably more
appropriate.

        
<code>var <b>epoch</b></code>

  

  
The most recent UNIX epoch (UTC) this case was reported.

        
<code>var <b>id</b></code>

  

  
The numerical identifier of this case, assigned by the database as an
auto-incrementing sequence.

        
<code>var <b>info</b></code>

  

  
Some information about this case, used for passing on to templates.

        
<code>var <b>notes</b></code>

  

  
Notes associated with this case.

        
<code>var <b>ticket_id</b></code>

  

  
The primary ticket identifier.  Numeric.

        
<code>var <b>ticket_no</b></code>

  

  
The other primary ticket identifier.  Looks numeric.  Is not the same as
`ticket_id`.  Actually a string.

        
<code>var <b>ticks</b></code>

  

  
The number of reports including this case.

#### Methods

    

####  find_existing_query: Returns partial query and terms to complete the SQL_FIND_EXISTING query.
Essentially, query and terms are used to complete the WHERE clause begun
with `WHERE cluster = ? AND`.

<code>def <b>find_existing_query</b>(self)</code>

  

  
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

  

    

####  insert_new: Subclasses must implement this method to insert a new record in their
associated table.  This method is called by the base class after the base
record has been created in the "reportables" table and an ID is available
as `self._id`, which the subclass can use in the database to link records
in its table to the reportables table.

<code>def <b>insert_new</b>(self)</code>

  

  
Subclasses must implement this method to insert a new record in their
associated table.  This method is called by the base class after the base
record has been created in the "reportables" table and an ID is available
as `self._id`, which the subclass can use in the database to link records
in its table to the reportables table.

  

    

####  serialize: Provide a dictionary representation of self.

<code>def <b>serialize</b>(self, pretty=False, options=None)</code>

  

  
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

<dl>
  <dt>pretty</dt><dd>if True, prettify some fields</dd>
  <dt>options</dt><dd>optional dictionary of options

</dd>
</dl>

**Returns**

  A dictionary representation of the case.

  

    

####  update: Updates the appropriate record for a new note, change to claimant, etc.
Subclasses can implement this to intercept the change, such as to make a
value database-friendly, but should pass the execution back to the super
class which will execute the SQL statement.

<code>def <b>update</b>(self, update, who)</code>

  

  
Updates the appropriate record for a new note, change to claimant, etc.
Subclasses can implement this to intercept the change, such as to make a
value database-friendly, but should pass the execution back to the super
class which will execute the SQL statement.

A history record is created for the update.

**Arguments**

<dl>
  <dt>update</dt><dd>A dict with `note` and/or `datum` and `value` defined describing
    the update.</dd>
  <dt>who</dt><dd>The CCI of the individual carrying out the change, that is, the
    logged-in user.</dd>
</dl>

  

    

####  update_existing: Handle updates to existing records.  This is called on initialization
to handle existing cases, as partially defined by subclasses (see
`find_exsiting_query()`).  Updates are also handled by subclass (see
`_update_existing_sub()`).

<code>def <b>update_existing</b>(self)</code>

  

  
Handle updates to existing records.  This is called on initialization
to handle existing cases, as partially defined by subclasses (see
`find_exsiting_query()`).  Updates are also handled by subclass (see
`_update_existing_sub()`).

At this point this is called, self should be initialized with the
details provided, but this may need to be appropriately adjusted with
data from the matching case in the database.

Returns: boolean indicating whether there was a record to update

  

      

---
Generated by [pdoc 0.9.2](https://pdoc3.github.io/pdoc).
