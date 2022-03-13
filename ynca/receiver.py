import threading
import logging

from typing import Dict, Optional, cast

from .connection import YncaConnection, YncaProtocolStatus
from .constants import ZONES, Subunit
from .errors import YncaInitializationFailedException
from .system import System
from .zone import Zone

logger = logging.getLogger(__name__)

# Map subunits to input names, this is used for discovering what inputs are available
# Inputs missing because unknown what subunit they map to: NET
SUBUNIT_INPUT_MAPPINGS: Dict[str, str] = {
    Subunit.TUN: "TUNER",
    Subunit.SIRIUS: "SIRIUS",
    Subunit.IPOD: "iPod",
    Subunit.BT: "Bluetooth",
    Subunit.RHAP: "Rhapsody",
    Subunit.SIRIUSIR: "SIRIUS InternetRadio",
    Subunit.PANDORA: "Pandora",
    Subunit.NAPSTER: "Napster",
    Subunit.PC: "PC",
    Subunit.NETRADIO: "NET RADIO",
    Subunit.IPODUSB: "iPod (USB)",
    Subunit.UAW: "UAW",
}


class Receiver:
    def __init__(self, serial_url: str):
        """Create a Receiver"""
        self._serial_url = serial_url
        self._connection: Optional[YncaConnection] = None
        self._available_subunits: Dict[str, bool] = {}
        self._initialized_event = threading.Event()

        # This is the list of instantiated Subunit classes
        self.subunits: Dict[str, Subunit] = {}

    @property
    def inputs(self) -> Dict[str, str]:
        # Receiver has the main inputs as discovered by System subunit
        # These are the externally connectable inputs like HDMI1, AV1 etc...
        inputs = {}

        if Subunit.SYS in self.subunits:
            inputs = cast(System, self.subunits[Subunit.SYS]).inputs

        # Next to that there are internal inputs provided by subunits
        # for example the "Tuner"input is provided by the TUN subunit
        for subunit, available in self._available_subunits.items():
            if available and subunit in SUBUNIT_INPUT_MAPPINGS.keys():
                input_id = SUBUNIT_INPUT_MAPPINGS[subunit]
                inputs[input_id] = input_id
        return inputs

    def _detect_available_subunits(self):
        logger.debug("Subunit availability check start")
        self._initialized_event.clear()
        self._connection.register_message_callback(self._protocol_message_received)

        # Figure out what subunits are available
        num_commands_sent_start = self._connection.num_commands_sent
        self._available_subunits = {}
        for subunit_id in Subunit:
            self._connection.get(subunit_id, "AVAIL")

        # Use @SYS:VERSION=? as end marker (even though this is not the SYS subunit)
        self._connection.get(Subunit.SYS, "VERSION")

        if not self._initialized_event.wait(
            (self._connection.num_commands_sent - num_commands_sent_start) * 0.120
        ):  # Each command is ~100ms + some margin
            raise YncaInitializationFailedException(
                f"Subunit availability check failed"
            )

        self._connection.unregister_message_callback(self._protocol_message_received)
        logger.debug("Subunit availability check done")

    def _initialize_available_subunits(self):
        # Every receiver has a System subunit (can not even check for its existence)
        system = System(self._connection)
        system.initialize()
        self.subunits[system.id] = system

        # Initialize detected subunits
        for subunit_id, available in self._available_subunits.items():
            if not available:
                continue
            subunit = None
            if subunit_id in ZONES:
                subunit = Zone(subunit_id, self._connection)

            if subunit is not None:
                subunit.initialize()
                self.subunits[subunit.id] = subunit

    def initialize(self):
        """
        Sets up a connection to the device and initializes the Receiver.
        This call takes several seconds.
        """
        # connection = YncaConnection(self._serial_url)
        connection = YncaConnection.create_from_serial_url(self._serial_url)
        connection.connect()
        self._connection = connection

        self._detect_available_subunits()
        self._initialize_available_subunits()

    def _protocol_message_received(
        self, status: YncaProtocolStatus, subunit: str, function_: str, value: str
    ):
        if function_ == "AVAIL":
            self._available_subunits[subunit] = status is YncaProtocolStatus.OK

        if subunit == Subunit.SYS and function_ == "VERSION":
            self._initialized_event.set()

    def close(self):
        for subunit in self.subunits.values():
            subunit.close()
        if self._connection:
            self._connection.close()
