===================================
FIWARE Health - Region Sanity Tests
===================================

This project contains **sanity checks** for being executed over each FIWARE
region to test some of their capabilities and the global Region Status.

Test case implementation has been performed using Python_ and its
testing__ framework.

__ `Python - Unittest`_


Test environment
----------------

**Prerequisites**

- `Python 2.7`__ or newer
- pip_
- virtualenv_ or Vagrant__
- `D-Bus`_ running and configured on your system
- `dbus-python`_ (v0.84.0)
- `pygobject`_ (v2.20.0)

__ `Python - Downloads`_
__ `Vagrant - Downloads`_


You will need to provided the D-Bus system configuration and these external
libs in the given environment where tests will be executed. **D-Bus and its
dependencies are not managed by the project requirements file**.


**Test case execution using virtualenv**

1. Create a virtual environment somewhere (``virtualenv $WORKON_HOME/venv``)
#. Activate the virtual environment (``source $WORKON_HOME/venv/bin/activate``)
#. Go to main folder in the test project
#. Install the requirements for the test case execution in the virtual
   environment (``pip install -r requirements.txt --allow-all-external``)
#. Install D-Bus requirements.

**Test case execution using Vagrant (optional)**

Instead of using virtualenv, you can use the provided Vagrantfile to deploy a
local VM using Vagrant_, that will provide all environment configurations for
launching test cases.

1. Download and install Vagrant
#. Go to main folder in the test project
#. Execute ``vagrant up`` to launch a VM based on Vagrantfile provided.
#. After Vagrant provision, your VM is properly configured to launch the
   Sanity Check. You have to access to the VM using ``vagrant ssh`` and change
   to ``/vagrant`` directory that will have mounted your test project workspace.
#. Install D-Bus requirements.

If you need more information about how to use Vagrant, you can see the
`getting started section`__ of Vagrant documentation.

__ `Vagrant - Getting Started`_


Test Algorithm
--------------

::

  For each FIWARE Region:
    Check authorization by first getting a token
    Init OpenStack REST Clients
    Release pre-existing test resources
    For each Test Case:
        SetUp TestCase
        Execute TestCase
        Clean all resources used during tests
  Generate TestReports



Test Cases of Region Sanity Tests
---------------------------------

**Base Test Cases**

These Test Cases will be common for all federated regions.

* Test whether region has flavors.
* Test whether region has images.
* Test whether region has 'cloud-init-aware' images (suitable for blueprints).
* Test whether region has the image used for testing.
* Test creation of a new security group with rules.
* Test creation of a new keypair.
* Test allocation of a public IP.

**Regions with an OpenStack network service**

* Test whether it is possible to create a new network with subnets
* Test whether there are external networks configured in the region
* Test whether it is possible to create a new router without setting the gateway
* Test whether it is possible to create a new router with a default gateway
* Test whether it is possible to create a new router without external gateway
  and link new network port
* Test whether it is possible to deploy an instance with a new network
* Test whether it is possible to deploy an instance with a new network
  and custom metadata
* Test whether it is possible to deploy an instance with a new network
  and new keypair
* Test whether it is possible to deploy an instance with a new network
  and new security group
* Test whether it is possible to deploy an instance with a new network
  and all params
* Test whether it is possible to deploy an instance with a new network
  and assign an allocated public IP
* Test whether it is possible to deploy an instance, assign an allocated
  public IP and establish a SSH connection
* Test whether it is possible to deploy an instance with a new network
  and connect to INTERNET (SNAT) without assigning a public IP
* Test whether it is possible to deploy an instance with new network
 and check that metadata service is working properly (PhoneHome service)

**Regions without an OpenStack network service**

* Test whether it is possible to deploy an instance with custom metadata
* Test whether it is possible to deploy an instance with new keypair
* Test whether it is possible to deploy an instance with new security group
* Test whether it is possible to deploy an instance with all params
* Test whether it is possible to deploy an instance and assign an allocated
  public IP
* Test whether it is possible to deploy an instance, assign an allocated
  public IP and establish a SSH connection
* Test whether it is possible to deploy an instance and connect to INTERNET
  (SNAT) without assigning a public IP
* Test whether it is possible to deploy an instance and check that metadata service
         is working properly (PhoneHome service)

**Regions with Object Storage service**

* Test whether it is possible to create a new container into the object storage.
* Test whether it is possible to delete a container.
* Test whether it is possible to upload a text file and download it.
* Test whether it is possible to delete an object from a container.
* Test whether it is possible to upload a big file and download it (More than 5Mb).


Configuration
-------------

Some configuration is needed before test execution. This configuration may come
from the file ``resources/settings.json`` or from the following environment
variables (which override values from such file):

* ``credentials``: data needed for authorization

  - ``OS_AUTH_URL``
  - ``OS_USERNAME``
  - ``OS_PASSWORD``
  - ``OS_TENANT_ID``
  - ``OS_TENANT_NAME``
  - ``OS_USER_DOMAIN_NAME``

* ``test_configuration``: other configuration values

  - ``TEST_PHONEHOME_ENDPOINT``

Apart from the former data, it is also possible to provide some per-region
configuration values under ``region_configuration``:

* ``external_network_name`` is the network for external floating IP addresses
* ``test_flavor`` let us customize the flavor of instances launched in tests


**Configuration example** ::

    {
        "environment": "fiware-lab",
        "credentials": {
            "keystone_url": "http://cloud.lab.fiware.org:4731/v2.0/",
            "tenant_id": "00000000000000000000000000000",
            "tenant_name": "MyTenantName",
            "user": "MyUser",
            "password": "MyPassword"
        },
        "test_configuration": {
            "phonehome_endpoint": "http://LocalHostPublicAddress:SomePort"
        },
        "region_configuration": {
            "external_network_name": {
                "Region1": "public-ext-net-01",
                "Region2": "my-ext-net",
                ...
            },
            "test_flavor": {
                "RegionN": "tiny"
            }
        },
        "key_test_cases": ["test_allocate_ip", "test_deploy_instance"]
    }


Tests execution
---------------

* Go to the root folder of the project.
* Run ``nosetests.sh``. This command will execute all sanity tests in all
  regions found under ``tests/regions/`` folder:

  - It is possible to provide a list of regions as argument to restrict the
    execution to them
  - Verbose logging may be enabled by adding ``--verbose`` option

::

  $ ./nosetests.sh
  $ ./nosetests.sh --verbose Region2 Region7 Region8

* Results of tests execution are written to a xUnit file ``test_results.xml``
  (basename may be changed using ``--output-name`` command line option), and
  additionally an HTML report ``test_results.html`` (or the same basename as
  the former) is generated from the given template (or the default found at
  ``resources/templates/`` folder).

* The script ``commons/result_analyzer.py`` is invoked to create a summary
  report ``test_results.txt``. It will analyze the status of each region using
  the *key_test_cases* information configured in the ``settings.json`` file:
  a region is considered "OK" if all its test cases with names matching the
  regular expressions defined in this property have been PASSED.


Test data storage
-----------------

Results included in summary report ``test_results.txt`` can be published through
a `Context Broker`_ (and therefore stored in a database). To do that, a request
to the `NGSI Adapter`_ adaptation layer will be issued, which in turn extracts
attributes from the report and invokes Context Broker.

Such extraction is done by a custom parser ``resources/parsers/sanity_tests.js``
provided as part of this component, which has to be installed together with the
rest of standard parsers bundled in NGSI Adapter package.


D-Bus and HTTP PhoneHome Service for E2E tests
---------------------------------------------

Some E2E test cases have been implemented to check the connection in both
*Internet -> VM* and *VM -> Internet*.
These test cases are:

* Test whether it is possible to deploy an instance, assign an allocated
  public IP and establish a SSH connection *(Internet -> VM)*
* Test whether it is possible to deploy an instance
  and connect to INTERNET (SNAT) without assigning a public IP *(VM -> Internet)*

The later will try to execute a *PhoneHome request* (executed by Cloud-Init in the VM)
to the *HTTP PhoneHome service* running in the configured HOST:PORT
(*phonehome_endpoint* configuration). If this value is not set, this test will be skipped.

There is another test implemented:

* Test whether it is possible to deploy an instance and check that metadata service is working properly.

This test is checking if openstack metadata services is working. These tests get the metadata information about
the VM deployed and return to the HTTP phonehome server.

Those test cases should return the information to the HTTP phonehome server and each one return that information
to a different path.
First test cases, are expected to attack "/phonehome" path.
The last test is expected to attack "/metadata" path.

The test uses two components:

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
Server is waiting in two different resources.
 /phonehome to receive the hostname of the VM in the HTTP POST body.
 /metadata to receive the metadata information in the HTTP POST body.

If the server receives a HTTP POST to the second resource, hostname should be included into the Hostname header.
This signal will be take into account by
tests that are waiting for a signal with the hostname value in ; the other tests will ignore it and will keep on
listening for new signals with the correct data (correct hostname) to them.


**D-Bus configuration**

The implemented D-Bus service uses the *System Bus* for communicating processes.
The bus name used by tests is *org.fiware.fihealth*.
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


**Launch HTTP PhoneHome server**

Before executing SNAT test you will have to launch the HTTP PhoneHome service like this:

::

   # export TEST_PHONEHOME_ENDPOINT
   # python ./commons/http_phonehome_server.py

.. REFERENCES

.. _Python: http://www.python.org/
.. _Python - Downloads: https://www.python.org/downloads/
.. _Python - Unittest: https://docs.python.org/2/library/unittest.html
.. _Vagrant: https://www.vagrantup.com/
.. _Vagrant - Downloads: https://www.vagrantup.com/downloads.html
.. _Vagrant - Getting Started: https://docs.vagrantup.com/v2/getting-started/index.html
.. _virtualenv: https://pypi.python.org/pypi/virtualenv
.. _pip: https://pypi.python.org/pypi/pip
.. _NGSI Adapter: https://github.com/telefonicaid/fiware-monitoring/tree/master/ngsi_adapter
.. _Context Broker: http://catalogue.fiware.org/enablers/publishsubscribe-context-broker-orion-context-broker
.. _D-Bus: http://www.freedesktop.org/wiki/Software/dbus/
.. _dbus-python: http://dbus.freedesktop.org/doc/dbus-python/doc/tutorial.html
.. _pygobject: http://www.pygtk.org/
