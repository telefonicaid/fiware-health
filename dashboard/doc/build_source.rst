=======================
 Building from sources
=======================

This component needs no compilation, as it is a server written in Node.js, so
the basic procedure consists basically on installing the ``node`` interpreter,
getting the sources and installing the required dependencies (assuming you
don't run commands as root, we use ``sudo`` for those commands that require
some special privileges):


CentOS 6.x
==========

- Install an updated ``node`` interpreter::

    $ curl -sL https://rpm.nodesource.com/setup | sudo bash -
    $ sudo yum install -y nodejs

- Install development tools::

    $ sudo yum install -y gcc-c++ make rpm-build redhat-rpm-config
    $ sudo npm install -g grunt-cli

- Get the source code from GitHub::

    $ sudo yum install -y git
    $ git clone https://github.com/telefonicaid/fiware-health

- Install dependencies::

    $ cd fiware-health/dashboard
    $ npm install

- (Optional but highly recommended) check coding style, run unit tests and
  get coverage::

    $ grunt lint test coverage

- At this point, we are ready to run the server manually::

    $ ./dashboard

- Alternatively, we could create a package for this component, install it and
  then run the ``fihealth_dashboard`` service::

    $ cd fiware-health/dashboard
    $ tools/build/package.sh
    $ sudo rpm -i fiware-fihealth-dashboard-X.Y.Z-1.noarch.rpm
    $ sudo service fihealth_dashboard start


Other distributions
===================

Again, the steps are the same as in CentOS. We only have to pay attention to
the way to install ``node`` (see NodeSource_ for details) and to the possible
different package names of the development tools.


.. REFERENCES

.. _NodeSource: https://github.com/nodesource/distributions
