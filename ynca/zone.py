from __future__ import annotations
import re
import logging

from typing import Dict

from .connection import YncaConnection, YncaProtocolStatus
from .constants import DSP_SOUND_PROGRAMS, Mute, Subunit
from .function_mixins import PlaybackFunctionMixin
from .helpers import number_to_string_with_stepsize
from .subunit import SubunitBase

logger = logging.getLogger(__name__)


class Zone(PlaybackFunctionMixin, SubunitBase):
    def __init__(
        self,
        subunit_id: str,
        connection: YncaConnection,
    ):
        super().__init__(subunit_id, connection)
        self._reset_internal_state()

    def _reset_internal_state(self):
        self._max_volume = 16.5  # is 16.5 for zones where it is not configurable
        self._volume = None
        self._scenes: Dict[str, str] = {}

        self._attr_inp = None
        self._attr_pwr = None
        self._attr_mute = None
        self._attr_soundprg = None
        self._attr_straight = None
        self._attr_zonename = None

    def on_initialize(self):
        self._reset_internal_state()

        # BASIC gets PWR, SLEEP, VOL, MUTE, INP, STRAIGHT, ENHANCER and SOUNDPRG (if applicable)
        self._get("BASIC")
        self._get("MAXVOL")
        self._get("SCENENAME")
        self._get("ZONENAME")

    def _subunit_message_received_without_handler(
        self, status: YncaProtocolStatus, function_: str, value: str
    ) -> bool:
        updated = True

        if matches := re.match(r"SCENE(\d+)NAME", function_):
            scene_id = matches[1]
            self._scenes[scene_id] = value
        else:
            updated = False

        return updated

    def _handle_vol(self, value: str):
        self._volume = float(value)

    def _handle_maxvol(self, value: str):
        self._max_volume = float(value)

    @property
    def name(self) -> str | None:
        """Get zone name"""
        return self._attr_zonename

    @property
    def on(self) -> bool | None:
        """Get current on state"""
        return self._attr_pwr == "On" if self._attr_pwr is not None else None

    @on.setter
    def on(self, value: bool):
        """Turn on/off zone"""
        self._put("PWR", "On" if value is True else "Standby")

    @property
    def mute(self) -> Mute | None:
        """Get current mute state"""
        return Mute(self._attr_mute) if self._attr_mute is not None else None

    @mute.setter
    def mute(self, value: Mute):
        """Mute"""
        self._put("MUTE", value)

    @property
    def max_volume(self) -> float | None:
        """Get maximum volume in dB"""
        return self._max_volume

    @property
    def min_volume(self) -> float:
        """Get minimum volume in dB"""
        return -80.5  # Seems to be fixed and the same for all zones

    @property
    def volume(self) -> float:
        """Get current volume in dB"""
        return self._volume

    @volume.setter
    def volume(self, value: float):
        """Set volume in dB. The receiver only works with 0.5 increments. Input values will be rounded to nearest 0.5 step."""
        if self.min_volume <= value <= self._max_volume:
            self._put("VOL", number_to_string_with_stepsize(value, 1, 0.5))
        else:
            raise ValueError(
                "Volume out of range, must be between min_volume and max_volume"
            )

    def volume_up(self, step_size: float = 0.5):
        """
        Increase the volume with given stepsize.
        Supported stepsizes are: 0.5, 1, 2 and 5
        """
        value = "Up"
        if step_size in [1, 2, 5]:
            value = "Up {} dB".format(step_size)
        self._put("VOL", value)

    def volume_down(self, step_size: float = 0.5):
        """
        Decrease the volume with given stepsize.
        Supported stepsizes are: 0.5, 1, 2 and 5
        """
        value = "Down"
        if step_size in [1, 2, 5]:
            value = "Down {} dB".format(step_size)
        self._put("VOL", value)

    @property
    def input(self) -> str:
        """Get current input"""
        return self._attr_inp

    @input.setter
    def input(self, value: str):
        """Set input"""
        self._put("INP", value)

    @property
    def dsp_sound_program(self) -> str:
        """Get the current DSP sound program"""
        return self._attr_soundprg

    @dsp_sound_program.setter
    def dsp_sound_program(self, value: str):
        """Set the DSP sound program"""
        if value in DSP_SOUND_PROGRAMS:
            self._put("SOUNDPRG", value)
        else:
            raise ValueError("Soundprogram not in DspSoundPrograms")

    @property
    def straight(self) -> bool | None:
        """Get the current Straight value"""
        return self._attr_straight == "On" if self._attr_straight is not None else None

    @straight.setter
    def straight(self, value: bool):
        """Set the Straight value"""
        self._put("STRAIGHT", "On" if value is True else "Off")

    @property
    def scenes(self) -> Dict[str, str]:
        """Get the dictionary with scenes where key, value = id, name"""
        return self._scenes

    def activate_scene(self, scene_id: str):
        """Activate a scene"""
        if scene_id not in self._scenes.keys():
            raise ValueError("Invalid scene ID")
        else:
            self._put("SCENE", f"Scene {scene_id}")


class Main(Zone):
    def __init__(
        self,
        connection: YncaConnection,
    ):
        super().__init__(Subunit.MAIN, connection)


class Zone2(Zone):
    def __init__(
        self,
        connection: YncaConnection,
    ):
        super().__init__(Subunit.ZONE2, connection)


class Zone3(Zone):
    def __init__(
        self,
        connection: YncaConnection,
    ):
        super().__init__(Subunit.ZONE3, connection)


class Zone4(Zone):
    def __init__(
        self,
        connection: YncaConnection,
    ):
        super().__init__(Subunit.ZONE4, connection)
