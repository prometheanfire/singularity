# Copyright (C) 2012 by Alex Brandt <alunduil@alunduil.com>
#
# singularity is freely distributable under the terms of an MIT-style license.
# See COPYING or http://www.opensource.org/licenses/mit-license.php.

import logging
import os
import re

from singularity.configurators import SingularityConfigurator

logger = logging.getLogger(__name__) # pylint: disable=C0103

class HostsConfigurator(SingularityConfigurator):
    @property
    def hosts_path(self): # pylint: disable=R0201,C0111
        return os.path.join(os.path.sep, "etc", "hosts")

    def runnable(self, configuration):
        """True if configurator can run on this system and in this context.

        ### Arguments

        Argument      | Description
        --------      | -----------
        configuration | Configuration items to be applied (dict)

        ### Description

        We should be able to run if the following conditions are true:
        * An /etc/hosts file is writable
        * We recieved the hostname
        * The hostname entries don't already exist

        """

        if "hostname" not in configuration:
            logger.info("Not passed a hostname")
            return False

        if not os.access(self.hosts_path, os.W_OK):
            logger.info("Can't write to %s", self.hosts_path)
            return False

        with open(self.hosts_path, "r") as hosts:
            lines = hosts.read()
            if re.search(r"127\.0\.0\.1.*?{0}".format(configuration["hostname"]), lines) and re.search(r"::1.*?{0}".format(configuration["hostname"]), lines): # pylint: disable=C0301
                logger.info("Hostname already present.")
                return False

        logger.info("HostsConfigurator is runnable!")
        return True

    def content(self, configuration):
        """Generated content of this configurator as a dictionary.
        
        ### Arguments

        Argument      | Description
        --------      | -----------
        configuration | Configuration settings to be applied by this configurator (dict)

        ### Description

        Add the hostname to the local host entries (127.0.0.1 and ::1).

        """

        lines = []

        with open(self.hosts_path, "r") as hosts:
            for line in hosts:
                line = line.strip()

                # TODO Remove names from previous images somehow?

                if re.search(r"127\.0\.0\.1.*?(?!{0})".format(configuration["hostname"]), line): # pylint: disable=C0301
                    lines.append(line + " " + configuration["hostname"])
                elif re.search(r"::1.*?(?!{0})".format(configuration["hostname"]), line): # pylint: disable=C0301
                    lines.append(line + " " + configuration["hostname"])
                else:
                    lines.append(line)
        
        return { self.hosts_path: lines }

