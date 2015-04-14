FIWARE PaaSManager Sanity Checks
================================

Configuration file
------------------

Some configuration is needed before test case execution. This configuration is
set in the ``resources/settings.json`` file:

- FIWARE Keystone endpoint.
- Valid FIWARE credentials for the configured *keystone_url*: User, Password and TenantId.

Instead of using configuration file, you can use environment variables (take a look to the example below).

All configuration values will be 'strings'.

**Environment configuration example with .json properties** ::

    {
        "environment": "fiware-lab",
        "credentials": {
            "keystone_url": "http://cloud.lab.fiware.org:4731/v2.0",
            "tenant_id": "",
            "tenant_name": "",
            "user": "",
            "password": "",
            "user_domain_name": "",
            "region_name": "Spain"
        }
    }

**Environment configuration using env vars**

You'll need to provide your OpenStack username and password. You can do this setting them as environment variables:

::

    OS_AUTH_URL=http://cloud.lab.fi-ware.org:4731/v2.0/
    OS_USERNAME=...
    OS_PASSWORD=...
    OS_TENANT_ID=...
    OS_TENANT_NAME=...
    OS_USER_DOMAIN_NAME=...

