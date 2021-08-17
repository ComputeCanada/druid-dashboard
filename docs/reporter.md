# Reporter and ReporterRegistry classes.

Subclass the Reporter class to support a new type of reportable problem
metrics.  The original use case for this was burst candidates: accounts with
significant short-term need that can't be readily met by the resources
typically available without a RAC.

Use the ReporterRegistry class to register new reporter classes so that the
application is aware of them: knows to query them for data to display on the
dashboard and can serve them appropriately via the REST API.

[[_TOC_]]

## Functions

    

####  just_job_id: Strip job ID to just the base ID, not including any array part.

<code>def <b>just_job_id</b>(jobid)</code>

  

  
Strip job ID to just the base ID, not including any array part.

**Arguments**

<dl>
  <dt>jobid</dt><dd>Job identifier, optionally including array part.

</dd>
</dl>

**Returns**

  Integer job identifier.

**Raises**

  `manager.exceptions.AppException` if the job ID does not match the
expected format.

  

## Classes
    

###  Reporter

<code>class <b>Reporter</b>()</code>

  

  
Base class for reporting metrics.

The Reporter class defines methods or stubs necessary to support a Detector
reporting potential problem cases of specific kind through the application's
API.

Subclasses must implement some methods and may override others, as
documented.  Methods implemented as stubs will throw `NotImplementedError`
if called.

#### Subclasses
  * manager.burst.Burst
  * manager.oldjob.OldJob

#### Static methods

    

####  describe: Describe report structure and semantics.

<code>def <b>describe</b>()</code>

  

  
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
_must_ override `Reporter.describe_me()` to describe the specifics of
that case and this method will combine the common and specific field
descriptions.

  

    

####  describe_me: Describe report structure and semantics specific to report type.

<code>def <b>describe_me</b>()</code>

  

  
Describe report structure and semantics specific to report type.

Subclasses should implement this to describe the table name, report title,
and the primary metric of the report type as well as columns specific to
and implemented by the subclass.  The Reporter class will call this method
from `Reporter.describe()` to generate the full report.

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

  

    

####  report: Report potential job and/or account issues.

<code>def <b>report</b>(cluster, epoch, data)</code>

  

  
Report potential job and/or account issues.

Subclasses must implement this to interpret reports coming through the API
from a Detector.  Those implementations should describe the expected
format of the `data` argument and should call `Reporter.summarize_report()`
to provide a summary as return value.

**Arguments**

<dl>
  <dt>cluster</dt><dd>The reporting cluster.</dd>
  <dt>epoch</dt><dd>Epoch of report (UTC).</dd>
  <dt>data</dt><dd>A list of dicts describing current instances of potential account
        or job pain or other metrics, as appropriate for the type of
        report.

</dd>
</dl>

**Returns**

  String describing summary of report.

  

    

####  summarize_report: Provide a brief, one-line summary of last report.

<code>def <b>summarize_report</b>(cases)</code>

  

  
Provide a brief, one-line summary of last report.

The intended use case for this summary is for notifications, such as to
Slack, when a report is received and interpreted.

Subclasses may override this method to provide additional information.

**Arguments**

<dl>
  <dt>cases</dt><dd>The list of cases (objects subclassed from Reportable class)
    created or updated from the last report.

</dd>
</dl>

**Returns**

  A string description of the last report.

  

    

####  view: Provide view to reported data.

<code>def <b>view</b>(criteria)</code>

  

  
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

<dl>
  <dt>criteria</dt><dd>Dict of criteria for selecting data for view.  In this
    implementation, `cluster` is required and `pretty` is optional.

    * `cluster`: (required) Cluster for which to provide data.
    * `pretty`: (optional, default False): provide display-friendly
      alternatives on some fields, if possible.

</dd>
</dl>

**Returns**

  None or a data structure conforming to the above.

**Raises**

  NotImplementedError: Criteria other than `pretty` or `cluster` were
  specified, indicating this should have been overridden by a subclass
  and were not.

  

      

    

###  ReporterRegistry

<code>class <b>ReporterRegistry</b>()</code>

  

  
Singular registry of reporters.

The application uses this registry to query available report types.
Subclasses of the Reporter class register so the application is aware of
them and knows to query and present different report types.

**Attributes**

<dl>
  <dt>reporters</dt><dd>Dict of report names to their classes.</dd>
</dl>

#### Static methods

    

####  get_registry: Return singular instance of registry.

<code>def <b>get_registry</b>()</code>

  

  
Return singular instance of registry.

  

#### Instance variables
        
<code>var <b>descriptions</b></code>

  

  
Dictionary of reporter name to the data description provided by the
reporter.

        
<code>var <b>reporters</b></code>

  

  
Dictionary of reporter name to class.

#### Methods

    

####  register: Register a Reporter implementation.

<code>def <b>register</b>(self, name, reporter)</code>

  

  
Register a Reporter implementation.

Reporters (subclasses of the `reporter.Reporter` class) must register
themselves so the application knows to query these classes.  A subclass of
the Reporter class must use this method at the end of its module file.

**Arguments**

<dl>
  <dt>name</dt><dd>The common name for the reporter type.  This name will be used,
    for example, when reporting via the API.  It is recommended it match
    the table name and be plural, for example, "bursts" or "oldjobs".</dd>
  <dt>reporter</dt><dd>The subclass.

</dd>
</dl>

**Raises**

  `manager.exceptions.AppException` if a reporter with that name has
  already by registered.

  

      

---
Generated by [pdoc 0.9.2](https://pdoc3.github.io/pdoc).
