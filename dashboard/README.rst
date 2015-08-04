=============================================
FIWARE Health - Sanity Check Status Dashboard
=============================================


Overview page with a summary of the status of the regions in FIWARE Lab, with
links to reports showing detailed information about the problems found.


Installation
============

Dashboard is distributed as a CentOS (.rpm) package. Assuming FIWARE package
repositories are configured, just use the proper tool (such as ``yum``) to
install ``fiware-fihealth-dashboard`` package. The RPM package has two dependencies, python and python-pip (must be installed manually). These distributions are currently supported:

-  CentOS 6.3/6.5

During installation process, Node.js engine version is checked and package
dependencies are resolved using ``npm`` tool. Upon successful installation,
a Linux service ``fihealth_dashboard`` is created.

`Mailman`_ and `mailman-api`_ are installed as dependencies of this component,
given that notifications are sent via mailing lists. After checking the values
for configuration options in file ``{installation_path}/config/dashboard.yml``,
some configuration steps are required after installation:

-  Customize subscription message by editing file
   ``{mailman-lib-path}/templates/en/subscribeack.txt``

.. code::

   Welcome to the %(real_name)s@%(host_name)s mailing list!
   %(welcome)s
   To unsubscribe, please visit http://%(host_name)s/.

-  Set mail host at ``{mailman-lib-path}/Mailman/mm_cfg.py``:

.. code::

   DEFAULT_URL_HOST   = 'myhost.mydomain.tld'
   DEFAULT_EMAIL_HOST = 'myhost.mydomain.tld'
   DEFAULT_HOST_NAME  = 'myhost.mydomain.tld'

-  Set mail transport agent (many supported, but `Postfix`_ recommended) at
   ``{mailman-lib-path}/Mailman/mm_cfg.py`` (some further configuration steps
   could be required: please follow directions at `Mailman documentation`__):

   __ `Mailman - Set up your mail server`_

.. code::

   MTA = 'Postfix'

   # These variables describe the program to use for regenerating the aliases.db
   # and virtual-mailman.db files, respectively, from the associated plain text
   # files.  The file being updated will be appended to this string (with a
   # separating space), so it must be appropriate for os.system().
   POSTFIX_ALIAS_CMD = '/usr/sbin/postalias'
   POSTFIX_MAP_CMD = '/usr/sbin/postmap'

-  Configure message footer at ``{mailman-lib-path}/Mailman/mm_cfg.py``:

.. code::

   # These format strings will be expanded w.r.t. the dictionary for the
   # mailing list instance.
   DEFAULT_MSG_FOOTER = """_______________________________________________
   Fi-Health Sanity Checks
   http://%(host_name)s/
   """

-  Create the mailing lists and subscribe to Context Broker:

.. code::

   $ cd {installation_path}/bin
   $ setup


Usage
=====

Dashboard runs as a standalone web server listening for requests at the given
endpoint. Once installed, there are two ways of starting the server: manually
from the command line or as a system service. It is not recommended to mix both
ways (e.g. start it manually but using the service scripts to stop it).


From the command line
---------------------

Simply type:

.. code::

   $ cd {installation_path}/bin
   $ dashboard

You can use command line arguments, e.g. to specify the listen port:

.. code::

   $ dashboard --listen-port=8081

Help for command line options:

.. code::

   $ dashboard --help


As system service
-----------------

Use the ``fihealth_dashboard`` service:

.. code::

   $ sudo service fihealth_dashboard start
   $ sudo service fihealth_dashboard stop
   $ service fihealth_dashboard status


Configuration options
---------------------

Some of the options can be overriden from the command line, but as a general
rule the use of ``dashboard.yml`` configuration file is preferrable.


Changelog
=========

Version 1.0.0

-  New overview and details pages.
-  IdM authentication.
-  Mail notifications in subscriptions to status changes.


License
=======

\(c) 2015 Telefónica I+D, Apache License 2.0


.. REFERENCES

.. _mailman-api: http://mailman-api.readthedocs.org/en/stable/
.. _Mailman: http://www.gnu.org/software/mailman/
.. _Mailman - Set up your mail server: http://www.gnu.org/software/mailman/mailman-install/mail-server.html
.. _Postfix: http://www.postfix.org/
