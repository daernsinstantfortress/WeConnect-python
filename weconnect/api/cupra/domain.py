from enum import Enum


class Domain(Enum):
    ALL = 'all'
    ALL_CAPABLE = 'allCapable'
    USER_CAPABILITIES = 'userCapabilities'
    MEASUREMENTS = 'measurements'
    SERVICES = 'services'
    ENGINES = 'engines'

    def __str__(self):
        return self.value
