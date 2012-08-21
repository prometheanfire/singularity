# Copyright (C) 2012 by Alex Brandt <alunduil@alunduil.com>
#
# singularity is freely distributable under the terms of an MIT-style license.
# See COPYING or http://www.opensource.org/licenses/mit-license.php.

import logging
import os

from singularity.parameters import SingularityParameters
from singularity.cache import SingularityCache
from singularity.configurators.features import FeaturesConfigurator

logger = logging.getLogger("console") # pylint: disable=C0103

class SingularityApplicator(object):
    def __call__(self, actions = None):
        """Apply an existing configuration to the system.

        ### Description

        Checks for an existing set of configuration items in the cache
        directory (defaults to /var/cache/singularity) and replaces the
        corresponding items in the filesystem.

        """

        if not actions:
            actions = [SingularityParameters()["action"]]

        if "all" in actions:
            actions = set(FeaturesConfigurator({})["message"].split(','))
        else:
            actions = set(actions)

        logger.debug("Actions specified: %s", actions)
        logger.debug("Allowed functions: %s", SingularityParameters()["main.functions"].split(","))

        actions &= set([ func.strip() for func in SingularityParameters()["main.functions"].split(",") ]) # pylint: disable=C0301

        logger.info("Actions to be applied: %s", actions)

        for key, content in SingularityCache().iteritems():
            function, filename = key.split('.', 1)

            if function not in actions:
                logger.info("Skipping %s since %s is not an allowed function.", filename, function) # pylint: disable=C0301
                continue

            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))

            if SingularityParameters()["main.backup"]:
                os.rename(filename, filename + ".bak")

            with open(filename, "w") as output:
                output.write("\n".join(content) + "\n")

