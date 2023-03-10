from enum import Enum
import logging

from weconnect.addressable import AddressableObject, AddressableAttribute, AddressableDict
from weconnect.elements.generic_status import GenericStatus

LOG = logging.getLogger("weconnect")


class AccessStatus(GenericStatus):
    def __init__(
        self,
        vehicle,
        parent,
        statusId,
        fromDict=None,
        fixAPI=True,
    ):
        self.overallStatus = AddressableAttribute(localAddress='overallStatus', parent=self, value=None, valueType=AccessStatus.OverallState)
        self.engineStatus = AddressableAttribute(localAddress='overallStatus', parent=self, value=None, valueType=AccessStatus.EngineState)
        self.lightsStatus = AddressableAttribute(localAddress='overallStatus', parent=self, value=None, valueType=AccessStatus.LightsState)
        self.doors = AddressableDict(localAddress='doors', parent=self)
        self.windows = AddressableDict(localAddress='windows', parent=self)
        super().__init__(vehicle=vehicle, parent=parent, statusId=statusId, fromDict=fromDict, fixAPI=fixAPI)

    def update(self, fromDict, ignoreAttributes=None):  # noqa: C901
        ignoreAttributes = ignoreAttributes or []
        LOG.debug('Update access status from dict')

        # Cupra
        if 'value' not in fromDict:
            fromDict['value'] = fromDict

        if 'value' in fromDict:
            # self.overallStatus.fromDict(fromDict['value'], 'overallStatus')

            if 'doors' in fromDict['value'] and fromDict['value']['doors'] is not None:
                for doorName in fromDict['value']['doors']:

                    doorDict = fromDict['value']['doors'][doorName]

                    if 'name' not in doorDict:
                        doorDict['name'] = doorName

                    if 'name' in doorDict:
                        if doorDict['name'] in self.doors:
                            self.doors[doorDict['name']].update(fromDict=doorDict)
                        else:
                            self.doors[doorDict['name']] = AccessStatus.Door(fromDict=doorDict, parent=self.doors)
                # for doorName in [doorName for doorName in self.doors.keys()
                #                  if doorName not in [door['name'] for door in fromDict['value']['doors'] if 'name' in door]]:
                #     # del self.doors[doorName]
                #     LOG.debug('deleted something here')
            else:
                self.doors.clear()
                self.doors.enabled = False

            if 'trunk' in fromDict['value']:
                doorDict = fromDict['value']['trunk']

                if 'name' not in doorDict:
                    doorDict['name'] = 'trunk'

                if 'name' in doorDict:
                    if doorDict['name'] in self.doors:
                        self.doors[doorDict['name']].update(fromDict=doorDict)
                    else:
                        self.doors[doorDict['name']] = AccessStatus.Door(fromDict=doorDict, parent=self.doors)

            if 'windows' in fromDict['value'] and fromDict['value']['windows'] is not None:
                for windowName in fromDict['value']['windows']:

                    windowDict = { 'name' : windowName, 'status' : fromDict['value']['windows'][windowName] }

                    if 'name' in windowDict:
                        if windowDict['name'] in self.windows:
                            self.windows[windowDict['name']].update(fromDict=windowDict)
                        else:
                            self.windows[windowDict['name']] = AccessStatus.Window(fromDict=windowDict, parent=self.windows)
                # for windowName in [windowName for windowName in self.windows.keys()
                #                    if windowName not in [window['name']
                #                    for window in fromDict['value']['windows'] if 'name' in window]]:
                #     del self.doors[windowName]
            else:
                self.windows.clear()
                self.windows.enabled = False

            fromDict['value']['overallStatus'] = AccessStatus.OverallState.SAFE

            for doorName in self.doors.keys():
                door = self.doors[doorName]
                if (door.openState.value != AccessStatus.Door.OpenState.CLOSED) or (door.lockState.value != AccessStatus.Door.LockState.LOCKED):
                    fromDict['value']['overallStatus'] = AccessStatus.OverallState.UNSAFE

            for windowName in self.windows.keys():
                window = self.windows[windowName]
                if (window.openState.value is not AccessStatus.Window.OpenState.CLOSED):
                    fromDict['value']['overallStatus'] = AccessStatus.OverallState.UNSAFE

            self.overallStatus.fromDict(fromDict['value'], 'overallStatus')

            if 'engine' in fromDict['value']:
                self.engineStatus.fromDict(fromDict['value'], 'engine')

            if 'lights' in fromDict['value']:
                self.lightsStatus.fromDict(fromDict['value'], 'lights')

        else:
            self.overallStatus.enabled = False
            self.doors.clear()
            self.doors.enabled = False
            self.windows.clear()
            self.windows.enabled = False
            self.engineStatus.enabled = False
            self.lightsStatus.enabled = False

        super().update(fromDict=fromDict, ignoreAttributes=(ignoreAttributes + ['overallStatus', 'doors', 'windows']))

    def __str__(self):
        string = super().__str__()
        if self.overallStatus is not None and self.overallStatus.enabled:
            string += f'\n\tOverall Status: {self.overallStatus.value.value}'
        if len(self.doors) > 0:
            string += f'\n\tDoors: {len(self.doors)} items'
            for door in self.doors.values():
                string += f'\n\t\t{door}'
        if len(self.windows) > 0:
            string += f'\n\tWindows: {len(self.windows)} items'
            for window in self.windows.values():
                string += f'\n\t\t{window}'
        if self.engineStatus is not None and self.engineStatus.enabled:
            string += f'\n\tEngine: {self.engineStatus.value.value}'
        if self.lightsStatus is not None and self.lightsStatus.enabled:
            string += f'\n\tLights: {self.lightsStatus.value.value}'

        return string

    class OverallState(Enum):
        SAFE = 'safe'
        UNSAFE = 'unsafe'
        INVALID = 'invalid'
        UNKNOWN = 'unknown overall state'

    class EngineState(Enum):
        ON = 'on'
        OFF = 'off'

    class LightsState(Enum):
        ON = 'on'
        OFF = 'off'

    class Door(AddressableObject):
        def __init__(
            self,
            parent,
            fromDict=None,
        ):
            super().__init__(localAddress=None, parent=parent)
            self.openState = AddressableAttribute(
                localAddress='openState', parent=self, value=None, valueType=AccessStatus.Door.OpenState)
            self.lockState = AddressableAttribute(
                localAddress='lockState', parent=self, value=None, valueType=AccessStatus.Door.LockState)
            if fromDict is not None:
                self.update(fromDict)

        def update(self, fromDict):
            LOG.debug('Update door from dict')

            if 'name' in fromDict:
                self.id = fromDict['name']
                self.localAddress = self.id
            else:
                LOG.error('Door is missing name attribute')

            if 'locked' in fromDict:
                if fromDict['locked'] == "true":
                    self.lockState.setValueWithCarTime(
                        AccessStatus.Door.LockState.LOCKED, lastUpdateFromCar=None, fromServer=True)
                elif fromDict['locked'] == "false":
                    self.lockState.setValueWithCarTime(
                        AccessStatus.Door.LockState.UNLOCKED, lastUpdateFromCar=None, fromServer=True)
                else:
                    self.lockState.setValueWithCarTime(
                        AccessStatus.Door.LockState.UNKNOWN, lastUpdateFromCar=None, fromServer=True)
            else:
                self.lockState.setValueWithCarTime(
                    AccessStatus.Door.LockState.UNKNOWN, lastUpdateFromCar=None, fromServer=True)


            if 'open' in fromDict:
                if fromDict['open'] == "true":
                    self.openState.setValueWithCarTime(
                        AccessStatus.Door.OpenState.OPEN, lastUpdateFromCar=None, fromServer=True)
                elif fromDict['open'] == "false":
                    self.openState.setValueWithCarTime(
                        AccessStatus.Door.OpenState.CLOSED, lastUpdateFromCar=None, fromServer=True)
                else:
                    self.openState.setValueWithCarTime(
                        AccessStatus.Door.OpenState.UNKNOWN, lastUpdateFromCar=None, fromServer=True)
            else:
                self.openState.setValueWithCarTime(
                    AccessStatus.Door.OpenState.UNKNOWN, lastUpdateFromCar=None, fromServer=True)


            # if 'status' in fromDict and fromDict['status']:
            #     if 'locked' in fromDict['status']:
            #         self.lockState.setValueWithCarTime(
            #             AccessStatus.Door.LockState.LOCKED, lastUpdateFromCar=None, fromServer=True)
            #     elif 'unlocked' in fromDict['status']:
            #         self.lockState.setValueWithCarTime(
            #             AccessStatus.Door.LockState.UNLOCKED, lastUpdateFromCar=None, fromServer=True)
            #     else:
            #         self.lockState.setValueWithCarTime(
            #             AccessStatus.Door.LockState.UNKNOWN, lastUpdateFromCar=None, fromServer=True)

            #     if 'open' in fromDict['status']:
            #         self.openState.setValueWithCarTime(AccessStatus.Door.OpenState.OPEN,
            #                                            lastUpdateFromCar=None, fromServer=True)
            #     elif 'closed' in fromDict['status']:
            #         self.openState.setValueWithCarTime(
            #             AccessStatus.Door.OpenState.CLOSED, lastUpdateFromCar=None, fromServer=True)
            #     elif 'unsupported' in fromDict['status']:
            #         self.openState.setValueWithCarTime(
            #             AccessStatus.Door.OpenState.UNSUPPORTED, lastUpdateFromCar=None, fromServer=True)
            #     elif 'invalid' in fromDict['status']:
            #         self.openState.setValueWithCarTime(
            #             AccessStatus.Door.OpenState.INVALID, lastUpdateFromCar=None, fromServer=True)
            #     else:
            #         self.openState.setValueWithCarTime(
            #             AccessStatus.Door.OpenState.UNKNOWN, lastUpdateFromCar=None, fromServer=True)
            # elif 'locked' in fromDict:

            # else:
            #     self.lockState.enabled = False
            #     self.openState.enabled = False

            for key, value in {key: value for key, value in fromDict.items() if key not in ['locked', 'open', 'name']}.items():
                LOG.warning('%s: Unknown attribute %s with value %s', self.getGlobalAddress(), key, value)

        def __str__(self):
            returnString = f'{self.id}: '
            if self.openState.enabled:
                returnString += f'{self.openState.value.value}'  # pylint: disable=no-member
            if self.lockState.enabled:
                returnString += f', {self.lockState.value.value}'  # pylint: disable=no-member
            return returnString

        class OpenState(Enum):
            OPEN = 'open'
            CLOSED = 'closed'
            UNSUPPORTED = 'unsupported'
            INVALID = 'invalid'
            UNKNOWN = 'unknown open state'

        class LockState(Enum):
            LOCKED = 'locked'
            UNLOCKED = 'unlocked'
            UNKNOWN = 'unknown lock state'

    class Window(AddressableObject):
        def __init__(
            self,
            parent,
            fromDict=None,
        ):
            super().__init__(localAddress=None, parent=parent)
            self.openState = AddressableAttribute(
                localAddress='openState', parent=self, value=None, valueType=AccessStatus.Window.OpenState)
            if fromDict is not None:
                self.update(fromDict)

        def update(self, fromDict):
            LOG.debug('Update window from dict')

            if 'name' in fromDict:
                self.id = fromDict['name']
                self.localAddress = self.id
            else:
                LOG.error('Window is missing name attribute')

            if 'status' in fromDict and fromDict['status']:
                if 'open' in fromDict['status']:
                    self.openState.setValueWithCarTime(
                        AccessStatus.Window.OpenState.OPEN, lastUpdateFromCar=None, fromServer=True)
                elif 'closed' in fromDict['status']:
                    self.openState.setValueWithCarTime(
                        AccessStatus.Window.OpenState.CLOSED, lastUpdateFromCar=None, fromServer=True)
                elif 'unsupported' in fromDict['status']:
                    self.openState.setValueWithCarTime(AccessStatus.Window.OpenState.UNSUPPORTED, lastUpdateFromCar=None)
                elif 'invalid' in fromDict['status']:
                    self.openState.setValueWithCarTime(AccessStatus.Window.OpenState.INVALID, lastUpdateFromCar=None)
                else:
                    self.openState.setValueWithCarTime(
                        AccessStatus.Window.OpenState.UNKNOWN, lastUpdateFromCar=None, fromServer=True)
                    LOG.warning('No unsupported window status: %s was provided, please report this as a bug', fromDict['status'])
            else:
                self.openState.enabled = False

            for key, value in {key: value for key, value in fromDict.items() if key not in ['name', 'status']}.items():
                LOG.warning('%s: Unknown attribute %s with value %s', self.getGlobalAddress(), key, value)

        def __str__(self):
            return f'{self.id}: {self.openState.value.value}'  # pylint: disable=no-member

        class OpenState(Enum,):
            OPEN = 'open'
            CLOSED = 'closed'
            UNSUPPORTED = 'unsupported'
            INVALID = 'invalid'
            UNKNOWN = 'unknown open state'
