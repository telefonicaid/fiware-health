====================================
FIWARE Health - Nagios Configuration
====================================

This project contains the configuration files needed to monitor FIWARE Lab
infrastructure using Nagios_ and NRPE_.


File hierarchy
--------------

**/nagios/\***

- Files to configure main Nagios Core server
- ``fiware-lab/`` contains object definitions for FIWARE Lab itself
- ``fiware-catalogue/`` contains definitions to check catalogue__ global
  instances

__ `FIWARE Catalogue`_


**/cloud/\***

- Files to configure NRPE Agent needed to remotely monitor the Cloud Portal
  host


**/pegasus/\***

- Files to configure NRPE Agent needed to remotely monitor the PaaS Manager
  (Pegasus) host


**/saggita/\***

- Files to configure NRPE Agent needed to remotely monitor the SDC (Saggita)
  host


Installation
------------

Files are located at their usual path in target hosts (i.e. ``/nagios/etc``
denotes the ``/etc`` directory in *nagios* host). In any case, please check
the directories of your local installation.

Additionally, some values need to be provided in order to complete the
configuration using the files installed. They can be distinguished by the
use of angle brackets (``<`` and ``>``). This command may help to find them:

::

    grep --recursive --include=*.cfg '<.*>' .


Prior starting Nagios, don't forget to check all configuration files:

::

    nagios --verify-config /etc/nagios/nagios.cfg


.. REFERENCES

.. _Nagios: http://www.nagios.org/
.. _NRPE: http://exchange.nagios.org/directory/Addons/Monitoring-Agents/NRPE--2D-Nagios-Remote-Plugin-Executor/details
.. _FIWARE Catalogue: http://catalogue.fiware.org/
