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

__ `Python - Downloads`_
__ `Vagrant - Downloads`_


**Test case execution using virtualenv**

1. Create a virtual environment somewhere (``virtualenv $WORKON_HOME/venv``)
#. Activate the virtual environment (``source $WORKON_HOME/venv/bin/activate``)
#. Go to main folder in the test project
#. Install the requirements for the test case execution in the virtual
   environment (``pip install -r requirements.txt --allow-all-external``)


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
* Test whether it is possible to deploy and instance, assign an allocated
  public IP and establish a SSH connection
* Test whether it is possible to deploy an instance with a new network
  and connect to INTERNET (SNAT) without assigning a public IP

**Regions without an OpenStack network service**

* Test whether it is possible to deploy an instance with custom metadata
* Test whether it is possible to deploy an instance with new keypair
* Test whether it is possible to deploy an instance with new security group
* Test whether it is possible to deploy an instance with all params
* Test whether it is possible to deploy and instance and assign an allocated
  public IP
* Test whether it is possible to deploy and instance, assign an allocated
  public IP and establish a SSH connection
* Test whether it is possible to deploy an instance and connect to INTERNET
  (SNAT) without assigning a public IP


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
  one region is "working" if all test cases defined in this property have
  been PASSED.


.. REFERENCES

.. _Python: http://www.python.org/
.. _Python - Downloads: https://www.python.org/downloads/
.. _Python - Unittest: https://docs.python.org/2/library/unittest.html
.. _Vagrant: https://www.vagrantup.com/
.. _Vagrant - Downloads: https://www.vagrantup.com/downloads.html
.. _Vagrant - Getting Started: https://docs.vagrantup.com/v2/getting-started/index.html
.. _virtualenv: https://pypi.python.org/pypi/virtualenv
.. _pip: https://pypi.python.org/pypi/pip
