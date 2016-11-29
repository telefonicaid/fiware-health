
# How to use sanity-test with Docker

There are several options to use dockerfiles in this project:

- _"Develop phonehome server"_. See Section **1. Phonehome**.
- _"Run sanity-tests"_. See Section **2. Sanity-tests**.


You do not need to do all of them, just use only the solution for your operations.

You need to have docker in your machine. See the [documentation](https://docs.docker.com/installation/) on how to do this. Additionally, you can use the proper FIWARE Lab docker
functionality to deploy dockers image there. See the [documentation](https://docs.docker.com/installation/)


----
## 1. Phonehome

Docker allows you to deploy an instance of the phonehome server in order to develop/debug with the service connected to [dbus](https://www.freedesktop.org/wiki/Software/dbus/).
Follow these steps:

1. Download [fiware-health' source code](https://github.com/telefonicaid/fiware-health) from GitHub (`git clone https://github.com/telefonicaid/fiware-health.git`)
2. `cd fiware-health/fiware-region-sanity-tests`
3. Run `docker build -t phonehome .`
4. Run `docker run -p 8081:8081 -d phonehome`


----
## 2. Run sanity-tests

Docker allows you to deploy an instance of the testbed and launch/run the sanity-tests in order to develop/debug.
Follow these steps:

1. Download [fiware-health' source code](https://github.com/telefonicaid/fiware-health) from GitHub (`git clone https://github.com/telefonicaid/fiware-health.git`)
2. `cd fiware-health/fiware-region-sanity-tests/docker`
3. Run `docker build -t fiwarehealth .`
4. Export variables:

      unset OS_TENANT_ID
      unset OS_TENANT_NAME
      export OS_REGION_NAME=Valladolid
      export OS_USERNAME=idm
      export OS_PASSWORD=idm
      export OS_AUTH_URL='http://[ip or domain]:5000/v3'
      export OS_TENANT_NAME=idm
      export OS_USER_DOMAIN_NAME=default
      export OS_PROJECT_DOMAIN_NAME=default
      export OS_IDENTITY_API_VERSION=3
      export VM_IP='[phonehome_IP]'

5. Run `docker-compose up`
