===================================
FIWARE Health - Region Sanity Tests
===================================

This project contains **sanity checks** for being executed over each FIWARE
region to test some of their capabilities and the global Region Status.

Test case implementation has been performed using Python_ and its
`unit testing`__ framework.

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
    Init OpenStack REST Clients
    For each Test Case:
        SetUp TestCase
        Execute TestCase
        Clean all generated test data
  Generate TestReports



Test Cases or the Regions Sanity Check
--------------------------------------

**Base TestCases**

This Test Cases will be common for all federated regions.

- Test 01: Check if the Region has flavors.
- Test 02: Check if the Region has images.
- Test 03: Check if the Region has images with 'init' in the name.
- Test 04: Check if the Region has the BASE_IMAGE_NAME used for testing.
- Test 05: Check if it is possible to create a new Security Group with rules.
- Test 06: Check if it is possible to create a new Keypair.
- Test 07: Allocate a public IP

**Regions with an OpenStack network service**

- Test 08: Check if it is possible to create a new Network with subnets
- Test 09: Check if there are external networks configured in the Region
- Test 10: Check if it is possible to create a new Router without setting the Gateway
- Test 11: Check if it is possible to create a new Router, with a default Gateway
- Test 12: Check if it is possible to deploy a new Instance: Name, FlavorID, ImageID, new NetworkID
- Test 13: Check if it is possible to deploy a new Instance: Name, FlavorID, ImageID, new NetworkID, Metadatas
- Test 14: Check if it is possible to deploy a new Instance: Name, FlavorID, ImageID, new NetworkID, new Keypair
- Test 15: Check if it is possible to deploy a new Instance: Name, FlavorID, ImageID, new NetworkID, new Sec. Group
- Test 16: Check if it is possible to deploy a new Instance: Name, FlavorID, ImageID, NetworkID, Sec. Group, keypair, metadata

**Regions without an OpenStack network service**

- Test 17: Check if it is possible to deploy a new Instance: Name, FlavorID, ImageID, Metadatas
- Test 18: Check if it is possible to deploy a new Instance: Name, FlavorID, ImageID, new Keypair
- Test 19: Check if it is possible to deploy a new Instance: Name, FlavorID, ImageID, new Sec. Group
- Test 20: Check if it is possible to deploy a new Instance: Name, FlavorID, ImageID, Sec. Group, keypair, metadata


Configuration file
------------------

Some configuration is needed before test case execution. This configuration is
set in the ``resources/settings.json`` file:

- FIWARE Keystone endpoint.
- Valid FIWARE credentials for the configured *keystone_url*: User, Password and TenantId.
- Some configuration about each region: External Network name

All configuration values will be 'strings'.

**Environment configuration example** ::

    {
        "environment": "fiware-lab",
        "credentials": {
            "keystone_url": "http://cloud.lab.fiware.org:4731/v2.0/",
            "tenant_id": "00000000000000000000000000000",
            "tenant_name": "myTenantName",
            "user": "MyUser",
            "password": "MyPassword"
        },
        "region_configuration": {
            "external_network_name": {
                "Spain": "net8300",
                "Trento": "ext-net",
                "Lannion": "public-ext-net-02",
                "Waterford": "public-ext-net-01",
                "Berlin": "ext-net-federation",
                "Prague": "default",
                "Mexico": "ext-net",
                "PiraeusN": "public-ext-net-1",
                "PiraeusU": "public-ext-net-1",
                "Zurich": "public-ext-net-1",
                "Karlskrona": "public-ext-net-01",
                "Volos": "public-ext-net-01",
                "Budapest": "publicRange",
                "Stockholm": "public-ext-net-01",
                "SophiaAntipolis": "net04_ext",
                "Poznan": "public_L3_v4",
                "Gent": "Public-Net",
                "Crete": "net04_ext"
            }
        },
        "key_test_cases": ["test_allocate_ip", "test_deploy_instance"]
    }


Tests execution
---------------

- Go to the main test folder of the project if not already on it or.
- Run ``launch_tests.sh``. This command will execute all Sanity Tests.
  You can run ``nosetests`` command to use more specific test configurations.
  For instance:

::

  nosetests tests/regions --exe \
            --with-xunit --xunit-file=test_results.xml \
            --with-html --html-report=test_results.html \
            --html-report-template=resources/templates/test_report_template.html -v


**'Result Analyzer' script**

You can use the script ``commons/result_analyzer.py`` to create a summary report
of the xUnit test result file (xml). This script will print on screen the result
for each test case and will analyze the "Region Status" using the
*key_test_cases* information configured in the ``settings.json`` file:
one region is "working" if all test cases defined in this property have
been PASSED.

::

  python commons/results_analyzer.py test_results.xml


.. REFERENCES

.. _Python: http://www.python.org/
.. _Python - Downloads: https://www.python.org/downloads/
.. _Python - Unittest: https://docs.python.org/2/library/unittest.html
.. _Vagrant: https://www.vagrantup.com/
.. _Vagrant - Downloads: https://www.vagrantup.com/downloads.html
.. _Vagrant - Getting Started: https://docs.vagrantup.com/v2/getting-started/index.html
.. _virtualenv: https://pypi.python.org/pypi/virtualenv
.. _pip: https://pypi.python.org/pypi/pip
