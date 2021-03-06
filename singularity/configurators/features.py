# Copyright (C) 2012 by Alex Brandt <alunduil@alunduil.com>
#
# singularity is freely distributable under the terms of an MIT-style license.
# See COPYING or http://www.opensource.org/licenses/mit-license.php.

import logging

from singularity.configurators import SingularityConfigurator
from singularity.parameters import SingularityParameters

logger = logging.getLogger("console") # pylint: disable=C0103

class FeaturesConfigurator(SingularityConfigurator):
    def runnable(self, configuration):
        """True if configurator can run on this system and in this context.

        ### Arguments

        Argument      | Description
        --------      | -----------
        configuration | Configuration items to be applied (dict)

        ### Description

        We should be able to run if the following conditions are true:
        * Recieve a function of features

        """

        if "function" not in configuration:
            logger.info("Must be passed a function in the message")
            return False

        if configuration["function"] != "features":
            logger.info("Must be passed \"features\" as the function")
            return False

        logger.info("FeaturesConfigurator is runnable!")
        return True

    def content(self, configuration):
        """Generated content of this configurator as a dictionary.
        
        ### Arguments

        Argument      | Description
        --------      | -----------
        configuration | Configuration settings to be applied by this configurator (dict)

        ### Description

        Returns the requested features information.  As a return message.

        """

        from singularity.configurators import SingularityConfigurators

        actions = set([ configurator.function for configurator in SingularityConfigurators() ]) # pylint: disable=C0301

        logger.debug("All the actions: %s", actions)

        actions &= set([ func.strip() for func in SingularityParameters()["main.functions"].split(",") ]) # pylint: disable=C0301

        logger.debug("Allowed actions: %s", actions)

        return { "message": ",".join(actions) }

