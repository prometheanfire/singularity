# Copyright (C) 2012 by Alex Brandt <alunduil@alunduil.com>
#
# singularity is freely distributable under the terms of an MIT-style license.
# See COPYING or http://www.opensource.org/licenses/mit-license.php.

import logging
import json
import os

logger = logging.getLogger(__name__) # pylint: disable=C0103

def translate(message): # pylint: disable=R0912,R0915
    """Translate the expected message to the new format.

    ### Arguments

    Argument | Description
    -------- | -----------
    message  | The string received from Xen or another communicator.

    ### Description

    If other communicators use a different message format this will have to be
    factored back into the individual communicators.

    ### Message Format Expected

    {
      "name": "resetnetwork",
    }

    {
      "name": "",
      "value": "",
    }

    {
      "label": "public",
      "ips": [
        { 
          "netmask": "255.255.255.0",
          "enabled": "1",
          "ip": "198.101.227.76"
        }
      ],
      "mac": "40:40:97:83:78:2e",
      "ip6s": [
        {
          "netmask": "96",
          "enabled": "0",
          "ip": "2001:4800:780F:0511:1E87:052F:FF83:782E",
          "gateway": "fe80::def"
        }
      ],
      "gateway": "198.101.227.1",
      "slice": "21006919",
      "dns": [
        "72.3.128.240",
        "72.3.128.241"
      ]
    }

    This information has changed in next gen servers:

    {
      "ip6s": [
        {
          "ip": "2001:4800:780e:0510:39be:d318:ff04:5959", 
          "netmask": 64, 
          "enabled": "1", 
          "gateway": "fe80::def"
        },
      ], 
      "label": "public", 
      "broadcast": "198.101.246.255", 
      "ips": [
        {
          "ip": "198.101.246.127", 
          "netmask": "255.255.255.0", 
          "enabled": "1", 
          "gateway": "198.101.246.1"
        },
      ], 
      "mac": "BC:76:4E:04:59:59", 
      "gateway_v6": "fe80::def", 
      "dns": [
        "72.3.128.241", 
        "72.3.128.240",
      ], 
      "gateway": "198.101.246.1"
    }
    
    {
      "label": "private",
      "ips": [
        {
          "netmask": "255.255.128.0",
          "enabled": "1",
          "ip": "10.180.144.116"
        }
      ],
      "routes": [
        {
          "route": "10.176.0.0",
          "netmask": "255.240.0.0",
          "gateway": "10.180.128.1"
        },
        {
          "route": "10.191.192.0",
          "netmask": "255.255.192.0",
          "gateway": "10.180.128.1"
        }
      ],
      "mac": "40:40:a1:47:e2:af"
    }

    The layout of this information has changed in next gen servers:

    {
      "label": "private",
      "broadcast": "10.180.127.255",
      "ips": [
        {
          "ip": "10.180.7.18",
          "netmask": "255.255.128.0",
          "enabled": "1",
          "gateway": null,
        },
      ],
      "mac": "BC:76:4E:04:59:AD",
      "dns": [
        "72.3.128.241",
        "72.3.128.240",
      ],
      "routes": [
        {
          "route": "10.191.192.0",
          "netmask": "255.255.192.0",
          "gateway": "10.180.0.1",
        },
        {
          "route": "10.176.0.0",
          "netmask": "255.240.0.0",
          "gateway": "10.180.0.1",
        },
      ],
      "gateway": null,
    }



    """

    parsed = json.loads(message)

    logger.info("Received message, %s", parsed)
    logger.debug("Type of message, %s", type(parsed))

    message = {}

    # TOOD Refactor this "parsing" to be more elegant.

    try:
        message["function"] = parsed["name"]
    except KeyError:
        logger.warning("Did not recieve 'name' from message")
    
    try:
        message["arguments"] = parsed["value"]
    except KeyError:
        logger.warning("Did not recieve 'value' from message")

    message["ips"] = {}

    logger.debug("Parsed Keys: %s", parsed.keys())

    try:
        logger.debug("Interface name for %s: %s", parsed["mac"], interface(parsed["mac"])) # pylint: disable=C0301
        message["ips"][interface(parsed["mac"])] = []
    except KeyError as error:
        logger.exception(error)
        logger.warning("Did not receive 'mac' from message")

    try:
        for ip in parsed["ips"]: # pylint: disable=C0103
            if ip["enabled"] == "1": # A string?  Really?
                message["ips"][interface(parsed["mac"])].append((cidr(ip["ip"], ip["netmask"]), "ipv4")) # pylint: disable=C0301
    except KeyError:
        logger.warning("Did not receive 'ips' or 'ips.ip' or 'ips.netmask' from message") # pylint: disable=C0301

    try:
        for ip in parsed["ip6s"]: # pylint: disable=C0103
            if ip["enabled"] == 1: # A string?  Really?
                message["ips"][interface(parsed["mac"])].append((cidr(ip["ip"], ip["netmask"]), "ipv6")) # pylint: disable=C0301
    except KeyError:
        logger.warning("Did not receive 'ip6s' or ip6s.ip' or 'ip6s.netmask' from message") # pylint: disable=C0301

    message["routes"] = {}

    try:
        message["routes"][interface(parsed["mac"])] = []
    except KeyError:
        logger.warning("Did not receive 'mac' from message")

    try:
        for ip in parsed["ips"]: # pylint: disable=C0103
            if ip["enabled"] == "1" and ip["gateway"] is not None:
                message["routes"][interface(parsed["mac"])].append(("default", ip["gateway"], "ipv4")) # pylint: disable=C0301
    except KeyError:
        logger.warning("Did not receive 'ips' or 'ips.gateway' from message") # pylint: disable=C0301

    try:
        for ip in parsed["ip6s"]: # pylint: disable=C0103
            if ip["enabled"] == "1" and ip["gateway"] is not None:
                message["routes"][interface(parsed["mac"])].append(("default", ip["gateway"], "ipv6")) # pylint: disable=C0301
    except KeyError:
        logger.warning("Did not receive 'ip6s' or 'ip6s.gateway' from message") # pylint: disable=C0301

    try:
        if parsed["gateway"] is not None:
            message["routes"][interface(parsed["mac"])].append(("default", parsed["gateway"], "ipv4")) # Should be ipv4 but need to verify ... # pylint: disable=C0301 
    except KeyError:
        logger.warning("Did not receive 'gateway' from message")

    try:
        if parsed["gateway_v6"] is not None:
            message["routes"][interface(parsed["mac"])].append(("default", parsed["gateway_v6"], "ipv6")) # Should be ipv4 but need to verify ... # pylint: disable=C0301 
    except KeyError:
        logger.warning("Did not receive 'gateway_v6' from message")

    try:
        for route in parsed["routes"]:
            message["routes"][interface(parsed["mac"])].append((cidr(route["route"], route["netmask"]), route["gateway"], "ipv4")) # Should be ipv4 but need to verify ... # pylint: disable=C0301
    except KeyError:
        logger.warning("Did not receive 'routes' or 'routes.route' or 'routes.netmask' or 'routes.gateway' from message") # pylint: disable=C0301

    try:
        logger.debug("Received DNS list: %s", parsed["dns"])
        message["resolvers"] = []
        for resolver in parsed["dns"]:
            logger.debug("Resolver to create an entry for: %s", resolver)
            message["resolvers"].append((resolver, "ipv4", interface(parsed["mac"]))) # Should be ipv4 but need to verify ... # pylint: disable=C0301
    except KeyError:
        logger.warning("Did not receive 'dns' or 'mac' from message") # pylint: disable=C0301
        if "resolvers" in message and not len(message["resolvers"]):
            del message["resolvers"]

    logger.debug("Compiled message: %s", message)

    if len(message["ips"]):
        if not any([ len(message["ips"][nic]) for nic in message["ips"].iterkeys() ]): # pylint: disable=C0301
            del message["ips"]
    else:
        del message["ips"]

    if len(message["routes"]):
        if not any([ len(message["routes"][nic]) for nic in message["routes"].iterkeys() ]): # pylint: disable=C0301
            del message["routes"]
        else:
            for nic in message["routes"].iterkeys():
                message["routes"][nic] = list(set(message["routes"][nic])) # Make sure we don't have any duplicate routes on a NIC # pylint: disable=C0301
    else:
        del message["routes"]

    logger.info("Compiled message: %s", message)

    return message

def interface(mac_address):
    """The interface name for the given MAC address."""

    # TODO Merge with mac_addresses?
    # TODO Other OS's?

    sys_net = os.path.join(os.path.sep, "sys", "class", "net")

    nics = {}
    for nic in os.listdir(sys_net):
        with open(os.path.join(sys_net, nic, "address")) as mac:
            nics[mac.read().strip().lower()] = nic

    logger.debug("Found MACs: %s", nics)

    return nics[mac_address.lower()]

def cidr(ip, netmask): # pylint: disable=C0103
    """Converts an IP and Netmask into CIDR notation."""

    bit_count = 0

    try:
        bits = reduce(lambda a, b: a << 8 | b, [ int(octet) for octet in netmask.split('.') ]) # pylint: disable=C0301

        while bits:
            bit_count += bits & 1
            bits >>= 1
    except AttributeError:
        bit_count = int(netmask)

    return "{0}/{1}".format(ip, bit_count)

def macs():
    """Gets all mac addresses on the system."""

    # TODO Merge with interface()?
    # TODO Other OS's?

    sys_net = os.path.join(os.path.sep, "sys", "class", "net")

    macs = [] # pylint: disable=W0621
    for nic in os.listdir(sys_net):
        with open(os.path.join(sys_net, nic, "address")) as mac:
            macs.append(mac.read().strip().lower())

    return macs

