===================================
FiHealth Sanity Checks | Test cases
===================================

This section describes some aspects about the implemented
test cases for FIWARE Health Sanity Checks.



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



Test Cases of Sanity Check
--------------------------

**Base Test Cases**

These Test Cases will be common for all federated regions.

* Test whether region has flavors.
* Test whether region has images.
* Test whether region has all required base images (as specified in settings).
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
  and connect to the internet (SNAT) without assigning a public IP
* Test whether it is possible to deploy an instance using the existing shared
  network and connect to the internet (SNAT) without assigning a public IP
* Test whether it is possible to deploy an instance with a new network
  and check that metadata service is working properly (PhoneHome service)
* Test whether it is possible to deploy an instance using the exiting shared
  network and check that metadata service is working properly

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
