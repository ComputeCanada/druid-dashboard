# Static resources employed by application

Static Javascript, CSS, and media produced by third parties are an important
component of the application, but do not belong in the application's source
control, nor are they included in the containerized builds of the application.
Instead, they are intended to be available externally.

To maintain control on versioning, and more imporantly to guard against
unavailability be it temporary or permanent, these resources are served from a
vanilla webserver operated by the project team or maintainers.

The location of this webserver is controlled by the `STATIC_RESOURCE_URI`
configuration variable (prepended with `BEAM_` if specified as an environment
variable or expressed as `static_resource_uri` in a configuration file).

Test deployments may use the container specified by `Dockerfile.resources` to
experiment with updated versions of third-party libraries, or to allow for
development and testing where access to the Internet is unreliable or
unavailable.

This directory is empty (except for this file) in source repositories but in
local workspaces should contain the listed resources in order to build the
container mentioned above, if desired.

## External resources used by the application

* [jQuery](https://jquery.com/)
* [Bootstrap](https://getbootstrap.com/)
* [DataTables](https://www.datatables.net/)
* [js-cookie](https://github.com/js-cookie/js-cookie)

Originally the application referenced URIs which would point to symlinks on
the resource webserver; these would then be symlinks to the desired version.
In the future the application will reference specific versions so there is
tighter control and better understanding about what the application uses.
