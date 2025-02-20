#!/bin/bash
set -euxo pipefail

diskname=$1
devname="$2"
loopname="${devname%*p?}"
loopdev=/dev/${loopname#/dev/*}

#==========================================
# Force the ESP to use legacy MBR identifier
#------------------------------------------
#
# Raspberry Pi 3 and older systems don't handle
# the 0xef partition type for the ESP, so switch
# to the legacy one.
#
sfdisk --change-id ${loopdev} 1 6
