===============================================
FiHealth Sanity Checks | PhoneHome architecture
===============================================

This documentation describes the implemented *PhoneHome service* to support
some E2E tests from Sanity Checks



D-Bus and HTTP PhoneHome Service for E2E tests
----------------------------------------------

Some E2E test cases have been implemented to check the connection in both
*Internet -> VM* and *VM -> Internet*.

SSH and SNAT Test cases:

* Test whether it is possible to deploy an instance, assign an allocated
  public IP and establish a SSH connection *(Internet -> VM)*
* Test whether it is possible to deploy an instance
  and connect to INTERNET (SNAT) without assigning a public IP *(VM -> Internet)*

The latter will try to execute a *PhoneHome request* (executed by Cloud-Init in the VM)
to the *HTTP PhoneHome service* running in the configured HOST:PORT
(*phonehome_endpoint* configuration). If this value is not set, this test will be skipped.

Metadata Service test cases:

* Test whether it is possible to deploy an instance and check that metadata service is working properly.

This test checks if the OpenStack metadata service is working and sends the retrieved
metadata back to the PhoneHome server to check whether they are correct or not.

These test cases should return the information to the HTTP phonehome server
using different URIs different path.

- First test cases send requests to *$TEST_PHONEHOME_ENDPOINT/phonehome* server resource.
- The last test (metadata) sends requests to *$TEST_PHONEHOME_ENDPOINT/metadata* server resource.

These E2E test use two components:

- A HTTP/D-Bus PhoneHome server, that is launched as a service in the same host where test is executed (with public IP).
- A D-Bus client used by test implementation to wait for PhoneHome requests through the HTTP PhoneHome server.

The implemented PhoneHome service uses the D-Bus system technology to communicate the
test execution and the HTTP PhoneHome server that is receiving the PhoneHome request from
deployed VMs.


**HTTP PhoneHome server**

The HTTP PhoneHome server waits for *POST HTTP requests* from VMs.
This service publishes a D-Bus object (D-Bus server) to be used by tests to wait for
PhoneHome requests.

When a request is received, HTTP PhoneHome server will inform all connected tests , through the published object,
about the event (broadcasting). This signal contains the
hostname of the VM (the one received in the HTTP POST body or the one received in the HTTP Header).

Server is waiting in two different resources:

- **/phonehome** to receive the hostname of the VM in the HTTP POST body.
- **/metadata** to receive the metadata information in the HTTP POST body.

If the server receives a HTTP POST to the second resource, hostname should be included into the Hostname header.
This signal will be take into account by
tests that are waiting for a signal with the hostname value in ; the other tests will ignore it and will keep on
listening for new signals with the correct data (correct hostname) to them.



D-Bus configuration for SanityChecks
------------------------------------

The implemented D-Bus service uses the *System Bus* for communicating processes.
The bus name used by tests is **org.fiware.fihealth**.
Additional configuration is needed in ``/etc/dbus-1/system.conf`` to setup the access policies:

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


