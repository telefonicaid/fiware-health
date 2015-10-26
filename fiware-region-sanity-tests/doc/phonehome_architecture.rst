=================================================
 FIHealth Sanity Checks | PhoneHome architecture
=================================================

This documentation describes the implemented *PhoneHome service* to support
some E2E tests from Sanity Checks


D-Bus and HTTP PhoneHome Service
================================

E2E tests
---------

Some E2E test cases have been implemented to check the connection in both
*Internet -> VM* and *VM -> Internet*.

**SSH and SNAT Test cases**:

- Test whether it is possible to deploy an instance, assign an allocated
  public IP and establish a SSH connection *(Internet -> VM)*
- Test whether it is possible to deploy an instance and connect to the
  internet (SNAT) without assigning a public IP *(VM -> Internet)*

In the latter case, ``cloud-init`` agent will try to send a request to the
``/phonehome*`` server resource of the *HTTP PhoneHome service*.

**Metadata Service test cases**:

- Test whether it is possible to deploy an instance and check that metadata
  service is working properly.

This checks if the OpenStack metadata service is working and sends the retrieved
metadata back to the ``/metadata*`` server resource of the PhoneHome service to
check whether they are correct or not.


Components
----------

E2E tests require two different components:

- A HTTP/D-Bus PhoneHome server, that is launched as a service in the same host
  where tests are executed (with a public IP).
- A D-Bus client used by test implementation to wait for PhoneHome requests
  through the HTTP PhoneHome server.

D-Bus technology is used to communicate the test executor (``nose`` process) and
the HTTP PhoneHome server that is receiving the requests from deployed VMs.


**HTTP PhoneHome server**

The HTTP PhoneHome server waits for *POST HTTP requests* from the VMs. This
service exposes a D-Bus object (D-Bus server) to be used by tests to wait for
requests.

**PhoneHome requests**

When a request is received, HTTP PhoneHome server will inform all connected
tests, through the exposed object, about the event (broadcasting). This signal
contains the hostname of the VM (the one received in the HTTP POST body or that
included in the HTTP headers).

Server is waiting in two different resources:

- **/phonehome** to receive the hostname of the VM in the HTTP POST body.
- **/metadata** to receive the metadata information in the HTTP POST body.

If the server receives a HTTP POST to the second resource, hostname should be
included into the Hostname header. This signal will be take into account by
tests that are waiting for a signal with the hostname value in; the other tests
will ignore it and will keep on listening for new signals with the correct data
(correct hostname) to them.


D-Bus configuration for Sanity Checks
=====================================

The implemented D-Bus service uses the *System Bus* for communicating processes.
The bus name used by tests is **org.fiware.fihealth**. Additional configuration
is needed in ``/etc/dbus-1/system.conf`` to setup the access policies:

::

    <policy>
        ...
        <!-- Holes must be punched in service configuration files for
               name ownership and sending method calls -->
        <allow own="org.fiware.fihealth"/>
        ...
        <!-- Allow anyone to talk to the message bus -->
        <allow send_destination="org.fiware.fihealth"/>
    </policy>
