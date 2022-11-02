from enum import Enum
from weconnect.api.vw.elements.control_operation import ControlInputEnum


class MaximumChargeCurrent(ControlInputEnum,):
    MAXIMUM = 'maximum'
    REDUCED = 'reduced'
    INVALID = 'invalid'
    UNKNOWN = 'unknown'

    @classmethod
    def allowedValues(cls):
        return [MaximumChargeCurrent.MAXIMUM, MaximumChargeCurrent.REDUCED]


class UnlockPlugState(ControlInputEnum,):
    OFF = 'off'
    ON = 'on'
    PERMANENT = 'permanent'
    UNKNOWN = 'unknown'

    @classmethod
    def allowedValues(cls):
        return [UnlockPlugState.OFF, UnlockPlugState.ON]

class ClimatizationState(Enum,):
    OFF = 'Off'
    ON = 'On'
    HEATING = 'Heating'
    COOLING = 'Cooling'
    VENTILATION = 'Ventilation'
    INVALID = 'Invalid'
    UNKNOWN = 'Unknown Climatization State'
