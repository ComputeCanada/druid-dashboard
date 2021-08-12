---
description: |
    API documentation for modules: manager.reportable.

lang: en

classoption: oneside
geometry: margin=1in
papersize: a4

linkcolor: blue
links-as-notes: true
...


    
# Module `manager.reportable` {#manager.reportable}

Reportable class for implementing new types of problem metrics, and supporting
functions and variables.




    
## Functions


    
### Function `dict_to_table` {#manager.reportable.dict_to_table}




>     def dict_to_table(
>         d
>     )


Given a dictionary, return a basic HTML table.

Turns the keys and values of the dictionary into a two-column table where
the keys are header cells (<code>TH</code>) and the values are regular cells (<code>TD</code>).
There is no header row and any complexity in the values are ignored (for
example there is no hierarchical tabling).


Args
-----=
**```d```**
:   A dictionary.



Returns
-----=
A basic HTML table to display that dictionary in the simplest possible
way.

    
### Function `json_to_table` {#manager.reportable.json_to_table}




>     def json_to_table(
>         str
>     )


Given a JSON string representing a dictionary, return an HTML table.

See <code>[dict\_to\_table()](#manager.reportable.dict\_to\_table "manager.reportable.dict\_to\_table")</code> for more detail.


Args
-----=
**```str```**
:   A JSON string representation of a dictionary.



Returns
-----=
A basic HTML table.


    
## Classes


    
### Class `Reportable` {#manager.reportable.Reportable}




>     class Reportable(
>         id=None,
>         record=None,
>         cluster=None,
>         epoch=None,
>         summary=None
>     )


A base class for reportable trouble metrics.

Subclasses of this class implement a single instance of a reportable case.
For example, an instance of the OldJob class represents an account on a
cluster with really old jobs.  Tomorrow if that account still has really old
jobs, it'll be reported again (via the appropriate subclass of
<code>manager.reporter.Reporter</code>) but it will still be the same instance, though
some of the details may change.

Instances of these subclasses are represented in the database by a row in
each of two tables: the reportables table, which stores information common
to all types, and in a table specific to the subclass.

Subclasses must implement some methods and may override others, as
documented.  Methods implemented here merely as stubs will throw
<code>NotImplementedError</code> if called.

There are three modes for creating a Case object:

1.  Lookup by ID.  Specify the ID but NOT the record.
2.  Factory loading by specifying a database record (row).  Specify the
    record but not the ID.
3.  Creating a "new" Case specifying information about it.  Note that it
    may be that an existing case is found matching enough of the
    information to be effectively the same case.  Both <code>id</code> and <code>record</code>
    should not be set.

Subclasses will need to override this method but _must_ invoke the base
implementation via <code>super().\_\_init\_\_()</code> to ensure the entire object is
initialized and persisted.


Args
-----=
**```id```**
:   Unique identifier for the case.


**```record```**
:   Dictionary describing all the values for the case.  This is used
    to efficiently instantiate multiple objects from a multiple-row query,
    or other examples of factory loading.


**```cluster```**
:   The cluster where this case occurred.


**```epoch```**
:   The UNIX epoch (UTC) when this case was (last) reported.


**```summary```**
:   A dictionary of arbitrary information supplied by the Detector
    which may be of use to analysts in addressing the case.



Raises
-----=
<code>manager.exceptions.ResourceNotFound</code> if the ID (but no record) is
  supplied and no record with that ID can be found.
<code>manager.exceptions.BadCall</code> if a nonsensical combination of named
  arguments are supplied.



    
#### Descendants

* [manager.burst.Burst](#manager.burst.Burst)
* [manager.oldjob.OldJob](#manager.oldjob.OldJob)



    
#### Instance variables


    
##### Variable `claimant` {#manager.reportable.Reportable.claimant}






    
##### Variable `cluster` {#manager.reportable.Reportable.cluster}






    
##### Variable `contact` {#manager.reportable.Reportable.contact}




Return contact information for this potential issue.  This can depend on
the type of issue: a PI is responsible for use of the account, so the PI
should be the contact for questions of resource allocation.  For a
misconfigured job, the submitting user is probably more appropriate.

Returns: username of contact.

    
##### Variable `epoch` {#manager.reportable.Reportable.epoch}






    
##### Variable `id` {#manager.reportable.Reportable.id}






    
##### Variable `info` {#manager.reportable.Reportable.info}






    
##### Variable `notes` {#manager.reportable.Reportable.notes}






    
##### Variable `ticket_id` {#manager.reportable.Reportable.ticket_id}






    
##### Variable `ticket_no` {#manager.reportable.Reportable.ticket_no}






    
##### Variable `ticks` {#manager.reportable.Reportable.ticks}







    
#### Static methods


    
##### `Method get` {#manager.reportable.Reportable.get}




>     def get(
>         id
>     )


Find and load the appropriate Reportable object given the ID.

Reportable IDs are unique among all subclasses.  In the database, they are
stored in the common reportables table and referenced from the
subclass-specific table.

This implementation tries to instantiate each of the registered case
classes using the given ID.  This is not efficient or graceful.


Args
-----=
**```id```**
:   The numeric ID of the case.



Returns
-----=
An instance of the appropriate case class with that ID, or None.

    
##### `Method get_current` {#manager.reportable.Reportable.get_current}




>     def get_current(
>         cluster
>     )


Get the current cases for this type of report.


Args
-----=
**```cluster```**
:   The identifier for the cluster of interest.



Returns
-----=
A list of appropriate reportable objects, or None.

    
##### `Method set_ticket` {#manager.reportable.Reportable.set_ticket}




>     def set_ticket(
>         id,
>         ticket_id,
>         ticket_no
>     )


Set the ticket information for a given case ID.

This is a convenience function that avoids actually finding and
instantiating the matching case.


Args
-----=
**```id```**
:   The case ID.


**```ticket_id```**
:   The OTRS ticket ID.


**```ticket_no```**
:   The OTRS ticket number.



Raises
-----=
DatabaseException if the execution fails.

Notes
-----=
The ticket ID and number are confusing and meaningful only to OTRS.
The Dude abides.


    
#### Methods


    
##### Method `find_existing_query` {#manager.reportable.Reportable.find_existing_query}




>     def find_existing_query(
>         self
>     )


Returns partial query and terms to complete the SQL_FIND_EXISTING query.
Essentially, query and terms are used to complete the WHERE clause begun
with `WHERE cluster = ? AND`.

Subclasses MUST implement this to enable detection of when a reported
record matches one already in the database.


Returns
-----=
A tuple (query, terms, cols) where:

  - <code>query</code> (string) completes the WHERE clauses in SQL_FIND_EXISTING,
  - <code>terms</code> (list) lists the search terms in the query, and
  - <code>cols</code> (list) lists the columns included in the selection.

    
##### Method `insert_new` {#manager.reportable.Reportable.insert_new}




>     def insert_new(
>         self
>     )


Subclasses must implement this method to insert a new record in their
associated table.  This method is called by the base class after the base
record has been created in the "reportables" table and an ID is available
as <code>self.\_id</code>, which the subclass can use in the database to link records
in its table to the reportables table.

    
##### Method `serialize` {#manager.reportable.Reportable.serialize}




>     def serialize(
>         self,
>         pretty=False,
>         options=None
>     )




    
##### Method `update` {#manager.reportable.Reportable.update}




>     def update(
>         self,
>         update,
>         who
>     )


Updates the appropriate record for a new note, change to claimant, etc.
Subclasses can implement this to intercept the change, such as to make a
value database-friendly, but should pass the execution back to the super
class which will execute the SQL statement.

A history record is created for the update.


Args
-----=
**```update```**
:   A dict with <code>note</code> and/or <code>datum</code> and <code>value</code> defined describing
    the update.


**```who```**
:   The CCI of the individual carrying out the change, that is, the
    logged-in user.



    
##### Method `update_existing` {#manager.reportable.Reportable.update_existing}




>     def update_existing(
>         self
>     )


Handle updates to existing records.  This is called on initialization
to handle existing cases, as partially defined by subclasses (see
<code>find\_exsiting\_query()</code>).  Updates are also handled by subclass (see
<code>\_update\_existing\_sub()</code>).

At this point this is called, self should be initialized with the
details provided, but this may need to be appropriately adjusted with
data from the matching case in the database.

Returns: boolean indicating whether there was a record to update


-----
Generated by *pdoc* 0.9.2 (<https://pdoc3.github.io>).
