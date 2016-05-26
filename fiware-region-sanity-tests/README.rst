===============================
 FIWARE Health - Sanity Checks
===============================

This is the code repository for **FIHealth - Sanity Checks**, a comprehensive
collection of *sanity* test cases over each region in `FIWARE Lab`_ in order
to validate the capabilities of the regions and get their *status*.

The sanity checks are one of the components of `FIHealth </README.rst>`_, which
is part of the `FIWARE Ops`_ suite of tools for the operation of FIWARE Lab.

This project is part of FIWARE_.

Any feedback on this documentation is highly welcome, including bugs, typos or
things you think should be included but aren't. You can use `github issues`__
to provide feedback.

__ `FIHealth - GitHub issues`_


Overall description
===================

The main objective of these *Sanity Checks* is to provide a way to know the
*region Status* of each federated node in FIWARE Lab. To do so, *Sanity Checks*
framework runs some tests against each node, testing its main features using a
final-user perspective (E2E testing). This collection of test cases cover these
main features:

- Compute operations.
- Networking operations.
- Image management operations.
- Object storage operations.

Test cases implementation relies on  Python_ and its testing__ framework.

__ `Python - Unittest`_


Build and Install
=================

The recommended procedure to run the checks is using `Jenkins CI`_ tool. We
provide all scripts needed to prepare the testing environment, configure *jobs*
and run the sanity checks using standard OpenStack configuration properties and
Jenkins environment variables for credentials management and configuration.

Alternatively, you can launch the sanity checks from command line using the
``sanity_checks`` script.


**Requirements**

* `Python 2.7`__ or newer
* `pip`_
* `virtualenv`_ or `Vagrant`__
* `D-Bus`_ running and configured on your system
* `dbus-python`_ (v0.84.0)
* `pygobject`_ (v2.20.0)

__ `Python - Downloads`_
__ `Vagrant - Downloads`_

As usual, ``requirements.txt`` file includes the required Python packages and
their versions.

Some sanity checks require inter-process communication, and Linux `D-Bus`_ is
used for that purpose. D-Bus system and its dependencies have to be previously
installed and configured in the testing environment. Please refer to the
`D-Bus documentation`__ for details and check `dbus-python`_ tutorial to
install and configure D-Bus Python libs. To configure the required *bus*
for *Sanity Checks* (**PhoneHome bus**), please take a look at the
`PhoneHome architecture <doc/phonehome_architecture.rst>`_.

__ `D-Bus`_


**Using virtualenv** (recommended)

1. Install D-Bus requirements for your system (*D-Bus* and *dbus-python*).

#. Create a virtual environment somewhere::

   $ virtualenv $WORKON_HOME/fiware-region-sanity-tests --system-site-packages

#. Activate the virtual environment::

   $ source $WORKON_HOME/fiware-region-sanity-tests/bin/activate

#. Go to main folder in the *FIHealth - Sanity Checks* project::

   $ cd fiware-health/fiware-region-sanity-tests

#. Install requirements for the test case execution in the virtual environment::

   $ pip install -r requirements.txt --allow-all-external


**Using Vagrant** (optional)

Instead of using ``virtualenv``, you can use Vagrant_ to deploy a local VM from
the given *Vagrantfile*, providing all environment configurations to launch the
test cases.

As a prerequisite, first download and install Vagrant (see Requirements). Then:

1. Go to the root folder of the project::

    $ cd fiware-health/fiware-region-sanity-tests

#. Launch a VM from the provided *Vagrantfile*::

    $ vagrant up

#. After Vagrant provision, your VM is properly configured to launch acceptance
   tests. You have to access the VM and change to the Vagrant directory mapping
   the testing workspace::

    $ vagrant ssh
    $ cd /vagrant

For more information about how to use Vagrant, please check `this document`__.

__ `Vagrant - Getting Started`_


Jenkins jobs
------------

Please use the `Jenkins CI Remote Access API`__ to submit the following files
to create the corresponding jobs:

- ``resources/jenkins/FIHealth-SanityCheck-0-SetUp.xml``
- ``resources/jenkins/FIHealth-SanityCheck-0-RestartTestServers.xml``
- ``resources/jenkins/FIHealth-SanityCheck-1-Flow.xml``
- ``resources/jenkins/FIHealth-SanityCheck-2-Exec-Region.xml``

__ `Jenkins CI - API`_


The following environment variables should be defined either in the global
configuration of Jenkins or as part of the jobs:

- **FIHEALTH_WORKSPACE**: The absolute path of Jenkins job workspace
- **FIHEALTH_HTDOCS**: The absolute path where to publish HTML reports
- **FIHEALTH_ADAPTER_URL**: The endpoint of NGSI Adapter
- **FIHEALTH_CB_URL**: The endpoint of Context Broker
- **WORKON_HOME**: The optional base path for virtualenv
- **OS_REGION_NAME**: The optional region to restrict tests to
- **OS_AUTH_URL**: The URL of OpenStack Identity Service for authentication
- **OS_USERNAME**: The username for authentication
- **OS_PASSWORD**: The password for authentication
- **OS_USER_ID**: The user identifier for authentication
- **OS_TENANT_ID**: The tenant identifier for authentication
- **OS_TENANT_NAME**: The tenant name for authentication
- **OS_USER_DOMAIN_NAME**: (Only in Identity v3) The user domain name for
  authentication
- **OS_PROJECT_DOMAIN_NAME**: (Only in Identity v3) The project domain name for
  authentication


Running
=======

Prerequisites
-------------

Some tests need a HTTP server waiting for requests from deployed VMs to check
network connectivity (part of the E2E behaviour). Before executing tests, you
will have to ensure the **HTTP PhoneHome server** is running.

This PhoneHome server requires a listen endpoint as parameter:

- The host:port where server listens to must be accessible from the internet.
- Endpoint should be configured in the ``phonehome_endpoint`` property of the
  configuration file or in ``$TEST_PHONEHOME_ENDPOINT`` environment variable;
  otherwise, the related tests will be skipped.

To launch the PhoneHome server manually::

  $ source $WORKON_HOME/fiware-region-sanity-tests/bin/activate
  $ cd $FIHEALTH_WORKSPACE/fiware-region-sanity-tests
  $ export TEST_PHONEHOME_ENDPOINT=http://<host>:<port>
  $ PYTHONPATH=. python commons/http_phonehome_server.py

Alternatively, server may be restarted just running ("Build now" option) the
job ``FIHealth-SanityCheck-0-RestartTestServers`` from Jenkins GUI.

The PhoneHome server is managed independently of the *Sanity Checks* runtime.
To know more about it and the underlying D-Bus architecture, please take a
look at the `PhoneHome architecture <doc/phonehome_architecture.rst>`_.


**Running Sanity Checks from command line**

- Go to the root folder of the project and edit ``etc/settings.json`` (or set
  environment variables, see above).
- Run ``./sanity_checks``. This command will execute Sanity Checks (defined
  as TestCases under ``tests/`` folder) in all the regions:

  * It is possible to provide a list of regions as argument to restrict the
    execution to them.
  * Verbose logging may be enabled by adding ``--verbose`` option.

  Examples::

  $ ./sanity_checks
  $ ./sanity_checks --verbose Region2 Region7 Region8


**Running Sanity Checks from Jenkins**

Jobs submitted during `installation <#Jenkins jobs>`_ run the script found at
``resources/scripts/jenkins.sh`` to perform one of these actions:

- ``setup`` as a required step prior running the tests (this performs some
  preparation tasks that are common to subsequent test executions)
- ``exec``: the actual Sanity Check execution for a single region (given by the
  environment variable ``$OS_REGION_NAME``)


Configuration file
------------------

Some configuration is needed before test execution (Sanity Checks execution).
This may come from the file ``etc/settings.json``:

- ``credentials``: data needed for authorization

  * ``keystone_url`` is the OpenStack auth URL
  * ``username`` is the OpenStack username
  * ``password`` is the OpenStack password
  * ``user_id`` is the OpentSack user_id
  * ``tenant_id`` is the OpentSack tenant_id
  * ``tenant_name`` is the OpenStack tenant_name
  * ``user_domain_name`` is the OpenStack user_domain_name (Identity v3)
  * ``project_domain_name`` is the OpenStack project_domain_name (Identity v3)

- ``test_configuration``: other configuration values

  * ``phonehome_endpoint`` is the PhoneHome Server endpoint (see above)
  * ``glance_configuration`` includes configuration related to Glance checks
  * ``swift_configuration`` includes configuration related to Swift checks
  * ``openstack_metadata_service_url`` is the OpenStack Metadata Service

Apart from the former data, it is also possible to provide some per-region
configuration values under ``region_configuration``:

- ``external_network_name`` is the network for external floating IP addresses
- ``shared_network_name`` is the shared network to use in E2E tests
- ``test_object_storage`` enables object storage tests, if true
- ``test_flavor`` specifies the flavor of instances launched in tests
- ``test_image`` specifies the base image of instances launched in tests

Finally, in order to calculate the global status of a region, these properties
are required:

- ``key_test_cases`` is a list of patterns to be matched with the name
  of test cases considered mandatory (i.e. their result must be "PASSED").
- ``opt_test_cases`` is a list of patterns to be matched with the name
  of test cases considered optional (i.e. they may fail).


**Sanity Checks configuration example** ::

    {
        "environment": "fiware-lab",
        "credentials": {
            "keystone_url": "http://cloud.lab.fiware.org:4731/v3/",
            "user_id": "00000000000000000000000000000",
            "tenant_id": "00000000000000000000000000000",
            "tenant_name": "MyTenantName",
            "user_domain_name": "MyUserDomainName",
            "project_domain_name": "MyProjectDomainName",
            "username": "MyUser",
            "password": "MyPassword"
        },
        "test_configuration": {
            "phonehome_endpoint": "http://LocalHostPublicAddress:SomePort",
            "glance_configuration": {
                "required_images": [ "base_image1", "base_image2" ]
            },
            "swift_configuration": {
                "big_file_url_1": "http://RemotePublicAddress1/File1.dat",
                "big_file_url_2": "http://RemotePublicAddress2/File2.dat"
            },
            "openstack_metadata_service_url": "http://169.254.169.254/openstack/latest/meta_data.json"
        },
        "key_test_cases": [
            "test_(.*)"
        ],
        "opt_test_cases": [
            "test_.*container.*"
        ],
        "region_configuration": {
            "RegionWithNetworkAndStorage": {
                "external_network_name": "my-ext-net1",
                "shared_network_name": "my-shared-net1",
                "test_object_storage": true
            },
            "RegionWithoutNetwork": {
                "external_network_name": "my-ext-net1",
                "test_object_storage": true
            },
            "RegionWithCustomImageNoStorage": {
                "external_network_name": "public-ext-net-02",
                "shared_network_name": "my-shared-net-02",
                "test_image": "base_image"
            },
            "RegionWithCustomFlavor": {
                "external_network_name": "public-ext-net-01",
                "shared_network_name": "node-int-net-01",
                "test_flavor": "tiny"
            }
        }
    }


Results of Sanity Check executions
----------------------------------

Results of tests execution are written to a xUnit file ``test_results.xml``
(basename may be changed using ``--output-name`` command line option), and
additionally an HTML report ``test_results.html`` (or the same basename as
the former) is generated from the given template (or the default found at
``resources/templates/`` folder).

Additionally, a log file is written with all logged info in a
Sanity Check execution, based on its handlers configuration
(`etc/logging_sanitychecks.conf`). When test cases involve VM
launching, just before deleting the VM, *FIHealth Sanity Checks*
tries to get the Nova Console-Log of that VM and it writes
the content in a new file `test_novaconsole_{region_name}_{server_id}.log`.
If the Console-Log is empty, it was impossible to be retrieved or
the log level is set tu *DEBUG*, the file is not generated.

The script ``commons/result_analyzer.py`` is invoked to create a summary
report ``test_results.txt``. It will analyze the status of each region using
the *key_test_cases* and *opt_test_cases* information configured in the
``etc/settings.json`` file.

Take a look at `Sanity Status and Data Storage documentation
<doc/publish_status_and_test_data.rst>`_ to know more about *Sanity and Test
Status* and the Context Broker integration with *FIHealth - Sanity Checks*


Testing
=======

This component itself is a set of test cases, so testing it does not apply.


Advanced topics
===============

- `More about implemented test cases <doc/test_cases.rst>`_
- `PhoneHome architecture <doc/phonehome_architecture.rst>`_
- `Publishing of region sanity status and tests data <doc/publish_status_and_test_data.rst>`_


.. REFERENCES

.. _FIWARE: http://www.fiware.org/
.. _FIWARE Lab: https://www.fiware.org/lab/
.. _FIWARE Ops: https://www.fiware.org/fiware-operations/
.. _FIHealth - GitHub issues: https://github.com/telefonicaid/fiware-health/issues/new
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
.. _Jenkins CI: https://jenkins-ci.org/
.. _Jenkins CI - API: https://wiki.jenkins-ci.org/display/JENKINS/Remote+access+API
