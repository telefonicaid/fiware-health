=============================
FIWARE Health - Sanity Checks
=============================

This is the code repository for the **FiHealth - Sanity Checks**, the FIWARE Ops tool
used to execute *sanity* test cases over each FIWARE federated node (regions)
to validate their capabilities and get the *Status* of them.

This sub-project is part of the **FiHealth** component, being a generic/configurable
tool that can be used over any OpenStack-based architecture.

Any feedback about this component is highly welcome, including bugs,
doc typos or things/features you think should be included or improved.
You can use `GitHub issues`_ to provide feedback or report defects.

Overall description
-------------------

The main objective of *Sanity Checks* is provide a way to know the *region Status*
of each federated node in FIWARE platform. To get this one, *Sanity Checks* engine
runs some tests against each node, testing its main features using a final-user
perspective (E2E testing). These set of test cases cover the main functionalities
for:

* Compute operations.
* Networking operations.
* Image management operations.
* Object storage operations.


Test case implementation has been performed using Python_ and its
testing__ framework.

__ `Python - Unittest`_


Build and Install
-----------------
The recommended procedure is to use a Jenkins platform for building
and running the *Sanity Checks*. We are providing all necessary scripts
to deploy, build and execute the runtime using a standard OpenStack
configuration properties and Jenkins' environment variables
for credentials management and environment configuration.

If you don't have a Jenkins platform for executing the *Sanity Checks*,
you can launch them from command-line through ``nosetests.sh`` script.

**Requirements**

* `Python 2.7`__ or newer
* pip_
* virtualenv_ or Vagrant__
* `D-Bus`_ running and configured on your system
* `dbus-python`_ (v0.84.0)
* `pygobject`_ (v2.20.0)

__ `Python - Downloads`_
__ `Vagrant - Downloads`_

The required python libs and their versions are specify in ``requirements.txt``
file.

You will need to provided the D-Bus system configuration and its external
libs in the given environment where tests will be executed. **D-Bus system, its
dependencies and installation are not managed by the project requirements file**.
Please, check `D-Bus`_ web page to know how to install it on your system and the
`dbus-python`_ tutorial to install and configure D-Bus python libs. To know how
to configure the required *bus* for *Sanity Checks* (**PhoneHome bus**) take a look at
the `phoneHome architecture <./doc/phonehome_architecture.rst>`_


**Using virtualenv** (recommended)

1. Create a virtual environment somewhere (``virtualenv $WORKON_HOME/venv``)
#. Activate the virtual environment (``source $WORKON_HOME/venv/bin/activate``)
#. Go to main folder in the *FiHealth - Sanity Checks* project (``$SANITYCHECK_PROJECT``)
#. Install the requirements for the test case execution in the virtual
   environment (``pip install -r requirements.txt --allow-all-external``)
#. Install D-Bus requirements for your system (*D-Bus* and *dbus-python*).


**Using Vagrant** (optional)

Instead of using virtualenv, you can use the provided Vagrantfile to deploy a
local VM using Vagrant_, that will provide all environment configurations for
launching test cases (except the D-Bus configuration).

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


**Using Jenkins' jobs** (recommended)

.. _Building and Installing on Jenkins:

The *Sanity Checks* engine has been designed to be executed over a Jenkins
platform. The script ``resources/scripts/jenkins.sh`` implements the logic
for installing, building and executing Sanity Checks. This script accept
two actions:

- ``prepare`` Sanity Check preparation process: Build and install.
- ``test`` Sanity Check execution for the given region (``$OS_REGION_NAME``)

::

    # ./resources/scripts/jenkins.sh --help
    # ./resources/scripts/jenkins.sh prepare


This script requires following environment configurations:

* ``JENKINS_HOME`` is the home path of Jenkins CI
  (available when executing jobs on Jenkins)
* ``JOB_URL`` is the full URL for this build job
  (available when executing jobs on Jenkins)
* ``FIHEALTH_WORKSPACE`` is the absolute path of Jenkins job workspace
  (should be defined in the job or Jenkins global configuration)
* ``FIHEALTH_HTDOCS`` is the absolute path where to publish HTML
  (should be defined in the job or Jenkins global configuration)
* ``FIHEALTH_ADAPTER_URL`` is the endpoint of NGSI Adapter
  (should be defined in the job or Jenkins global configuration)
* ``FIHEALTH_CB_URL`` is the endpoint of ContextBroker
  (should be defined in the job or Jenkins global configuration)
* ``WORKON_HOME`` is the optional base path for virtualenv
  (should be defined in the job or Jenkins global configuration)
* ``OS_REGION_NAME`` is the optional region to restrict tests to
  (should be defined in the job or Jenkins global configuration)
* ``OS_AUTH_URL`` is the OpenStack auth_url
  (should be defined in the job or Jenkins global configuration)
* ``OS_USERNAME`` is the OpenStack username
  (should be defined in the job or Jenkins global configuration)
* ``OS_PASSWORD`` is the OpenStack password
  (should be defined in the job or Jenkins global configuration)
* ``OS_TENANT_ID`` is the OpenStack tenant_id
  (should be defined in the job or Jenkins global configuration)
* ``OS_TENANT_NAME`` is the OpenStack tenant_name
  (should be defined in the job or Jenkins global configuration)
* ``OS_USER_DOMAIN_NAME`` is the OpenStack user_domain_name (to
  replace the former if Identity API v3 (should be defined in the
  job or Jenkins global configuration)


The full Jenkins' job configuration to build and install the
*Fi-Health Sanity Checks* component has been exported as XML to this file
``resources/jenkins/FiHealth-SanityCheck-0-SetUp.xml``. Environment variables
are not in this XML because they have been defined as part of the Global Jenkins
Configuration.



Running
-------

**Launch HTTP PhoneHome server**

Some tests need a HTTP server waiting for requests from deployed VMs to check
the E2E behaviour. Before executing these tests you will
have to launch the implemented **HTTP PhoneHome service** like this:

::

   # export TEST_PHONEHOME_ENDPOINT
   # python commons/http_phonehome_server.py

If ``$TEST_PHONEHOME_ENDPOINT`` is not configured or this value is not set in
the configuration file, the related tests will be skipped.

The host where PhoneHome service is running must be accessible
from deployed VMs. This endpoint should be configured in the
``phonehome_endpoint`` property of configuration file or
``$TEST_PHONEHOME_ENDPOINT`` env variable to be used by Sanity Checks.

The PhoneHome server is managed independently of the *Sanity Checks* runtime.

To know more about the D-Bus architecture and the HTTP PhoneHome service,
please take a look at the
`PhoneHome architecture documentation <./doc/phonehome_architecture.rst>`_


**Running SanityChecks from main script**

* Go to the root folder of the project and configure the ``resources/settings.json``
  and/or export env variables (see `Configuration`_).
* Run ``./nosetests.sh``. This command will execute all
  Sanity Checks in all nodes found under ``tests/regions/`` folder:

  - It is possible to provide a list of regions as argument to restrict the
    execution to them.
  - Verbose logging may be enabled by adding ``--verbose`` option.

::

  # ./nosetests.sh --help
  # ./nosetests.sh
  # ./nosetests.sh --verbose Region2 Region7 Region8


**Running SanityChecks from Jenkins' job**

After `Building and Installing on Jenkins`_ the *FiHealth Sanity Checks*
component, we can create another job to execute it. This job must launch
the ``jenkins.sh`` script (with all required configuration), but
passing by params the action *test*:

::

    # export OS_REGION_NAME="Region0"
    # ./resources/scripts/jenkins.sh test


The full Jenkins' job configuration to run *Fi-Health Sanity Checks* has been exported
as XML to this file ``resources/jenkins/FiHealth-SanityCheck-2-Exec-Region.xml``.
Environment variables are not in this XML because they have been defined as part
of the Global Jenkins Configuration.



Configuration
-------------

Some configuration is needed before test execution (Sanity Checks execution).
This configuration may come from the file ``resources/settings.json`` or from
the following environment variables (which override values from such file):

* ``credentials``: data needed for authorization

  - ``OS_AUTH_URL`` is the OpenStack auth URL
  - ``OS_USERNAME`` is the OpenStack username
  - ``OS_PASSWORD`` is the OpenStack password
  - ``OS_TENANT_ID`` is the OpentSack tenant_id
  - ``OS_TENANT_NAME`` is the OpenStack tenant_name
  - ``OS_USER_DOMAIN_NAME`` is the OpenStack user_domain_name (to
    replace the former if Identity API v3

* ``test_configuration``: other configuration values

  - ``TEST_PHONEHOME_ENDPOINT`` is the PhoneHome Server endpoint to be used
    in some E2E tests. See the `PhoneHome architecture <./doc/phonehome_architecture.rst>`_

Apart from the former data, it is also possible to provide some per-region
configuration values under ``region_configuration``:

* ``external_network_name`` is the network for external floating IP addresses
* ``test_flavor`` let us customize the flavor of instances launched in tests

As we have mention above, it is needed to specify these properties:

* ``key_test_cases`` is a list of patterns to be matched with the name
  of test cases to consider them mandatorily PASSED.
* ``opt_test_cases`` is a list of patterns to be matched with the name
  of test cases to consider some of the key test cases as optional.



**Sanity Checks configuration example** ::

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
        "key_test_cases": [ "test_(.*)" ],
        "opt_test_cases": [ "test_.*container.*" ]
    }



Results of Sanity Check executions
----------------------------------

Results of tests execution are written to a xUnit file ``test_results.xml``
(basename may be changed using ``--output-name`` command line option), and
additionally an HTML report ``test_results.html`` (or the same basename as
the former) is generated from the given template (or the default found at
``resources/templates/`` folder).

The script ``commons/result_analyzer.py`` is invoked to create a summary
report ``test_results.txt``. It will analyze the status of each region using
the *key_test_cases* and *opt_test_cases* information configured in the
``resources/settings.json`` file.

Take a look at
`Sanity Status and Data Storage documentation <./doc/status_and_data_storage.rst>`_
to know more about *Sanity and Test Status* and the Context Broker integration
with *FiHealth - Sanity Checks*



Testing
-------

This component is an amount of test cases itself. We are not providing
test cases to check the implemented test cases. We are validating them
running the Sanity Checks on a Jenkins platform against an OpenStack
platform for testing/developer purposes.



Advanced topics
---------------

* `More about implemented test cases <./doc/test_cases.rst>`_
* `PhoneHome architecture <./doc/phonehome_architecture.rst>`_
* `Region Status (Sanity Status) and test data storage <./doc/status_and_data_storage.rst>`_



.. REFERENCES

.. _GitHub issues: https://github.com/telefonicaid/fiware-health/issues
.. _Python: http://www.python.org/
.. _Python - Downloads: https://www.python.org/downloads/
.. _Python - Unittest: https://docs.python.org/2/library/unittest.html
.. _Vagrant: https://www.vagrantup.com/
.. _Vagrant - Downloads: https://www.vagrantup.com/downloads.html
.. _Vagrant - Getting Started: https://docs.vagrantup.com/v2/getting-started/index.html
.. _virtualenv: https://pypi.python.org/pypi/virtualenv
.. _pip: https://pypi.python.org/pypi/pip
.. _D-Bus: http://www.freedesktop.org/wiki/Software/dbus/
.. _dbus-python: http://dbus.freedesktop.org/doc/dbus-python/doc/tutorial.html
.. _pygobject: http://www.pygtk.org/
