from __future__ import annotations
from typing import Dict, List, Any, Type, Optional
from enum import Enum
import logging

from requests import codes

from weconnect.addressable import AddressableObject, AddressableAttribute, AddressableDict, AddressableList
from weconnect.api.cupra.elements.charging_settings import ChargingSettings
from weconnect.api.cupra.elements.controls import Controls
from weconnect.api.cupra.elements.generic_status import GenericStatus
from weconnect.api.cupra.elements.generic_capability import GenericCapability
from weconnect.api.cupra.elements.charging_status import ChargingStatus
from weconnect.api.cupra.elements.parking_position import ParkingPosition
from weconnect.api.cupra.elements.odometer_measurement import OdometerMeasurement
from weconnect.api.cupra.elements.error import Error
from weconnect.api.cupra.elements.helpers.request_tracker import RequestTracker
from weconnect.api.cupra.elements.battery_status import BatteryStatus
from weconnect.errors import APICompatibilityError, APIError
from weconnect.util import kelvinToCelsius, kelvinToFarenheit, toBool
from weconnect.api.cupra.domain import Domain
from weconnect.fetch import Fetcher
from weconnect.api.cupra.elements.climatization_status import ClimatizationStatus
from weconnect.api.cupra.elements.climatization_settings import ClimatizationSettings

# Cupra
from weconnect.api.cupra.elements.engine_state import EngineState

LOG: logging.Logger = logging.getLogger("weconnect")


class DomainDict(AddressableDict):
    def __init__(self, **kwargs):
        self.error: Error = Error(localAddress='error', parent=self)
        super().__init__(**kwargs)

    def updateError(self, fromDict: Dict[str, Any]):
        if 'error' in fromDict:
            self.error.update(fromDict['error'])
        else:
            self.error.reset()

    def hasError(self) -> bool:
        return self.error.enabled


class Vehicle(AddressableObject):  # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        fetcher: Fetcher,
        vin: str,
        parent: AddressableDict[str, Vehicle],
        fromDict: Dict[str, Any],
        fixAPI: bool = True,
        updateCapabilities: bool = True,
        updatePictures: bool = True,
        selective: Optional[list[Domain]] = None,
        enableTracker: bool = False
    ) -> None:
        self.fetcher: Fetcher = fetcher
        super().__init__(localAddress=vin, parent=parent)
        
        # Public API properties
        self.vin: AddressableAttribute[str] = AddressableAttribute(
            localAddress='vin', parent=self, value=None, valueType=str)
        self.role: AddressableAttribute[Vehicle.User.Role] = AddressableAttribute(
            localAddress='role', parent=self, value=None, valueType=Vehicle.User.Role)
        self.enrollmentStatus: AddressableAttribute[Vehicle.User.EnrollmentStatus] = AddressableAttribute(
            localAddress='enrollmentStatus', parent=self, value=None, valueType=Vehicle.User.EnrollmentStatus)
        self.userRoleStatus: AddressableAttribute[Vehicle.User.UserRoleStatus] = AddressableAttribute(
            localAddress='userRoleStatus', parent=self, value=None, valueType=Vehicle.User.UserRoleStatus)
        self.model: AddressableAttribute[str] = AddressableAttribute(
            localAddress='model', parent=self, value=None, valueType=str)
        self.devicePlatform: AddressableAttribute[Vehicle.DevicePlatform] = AddressableAttribute(
            localAddress='devicePlatform', parent=self, value=None, valueType=Vehicle.DevicePlatform)
        self.nickname: AddressableAttribute[str] = AddressableAttribute(
            localAddress='nickname', parent=self, value=None, valueType=str)
        self.brandCode: AddressableAttribute[Vehicle.BrandCode] = AddressableAttribute(
            localAddress='brandCode', parent=self, value=None, valueType=Vehicle.BrandCode)
        self.capabilities: AddressableDict[str, GenericCapability] = AddressableDict(
            localAddress='capabilities', parent=self)
        self.domains: AddressableDict[str, DomainDict] = AddressableDict(
            localAddress='domains', parent=self)
        self.images: AddressableAttribute[Dict[str, str]] = AddressableAttribute(
            localAddress='images', parent=self, value=None, valueType=dict)
        self.tags: AddressableAttribute[List[str]] = AddressableAttribute(
            localAddress='tags', parent=self, value=None, valueType=list)
        self.coUsers: AddressableList[Vehicle.User] = AddressableList(
            localAddress='coUsers', parent=self)
        self.controls: Controls = Controls(
            localAddress='controls', vehicle=self, parent=self)
        
        self.fixAPI: bool = fixAPI
        self.requestTracker: Optional[RequestTracker] = None
        if enableTracker:
            self.requestTracker = RequestTracker(self)

        self.update(fromDict, updateCapabilities=updateCapabilities, updatePictures=updatePictures, selective=selective)

    def enableTracker(self) -> None:
        if self.requestTracker is None:
            self.requestTracker = RequestTracker(self)

    def disableTracker(self) -> None:
        if self.requestTracker is not None:
            self.requestTracker.clear()
        self.requestTracker = None

    def statusExists(self, domain: str, status: str) -> bool:
        if domain in self.domains and status in self.domains[domain]:
            return True
        return False

    def update(  # noqa: C901  # pylint: disable=too-many-branches
        self,
        fromDict: Dict[str, Any] = {},
        updateCapabilities: bool = True,
        updatePictures: bool = True,
        force: bool = False,
        selective: Optional[list[Domain]] = None
    ) -> None:
        if fromDict is not None:
            LOG.debug('Create /update vehicle')

            self.vin.fromDict(fromDict, 'vin')
            self.role.fromDict(fromDict, 'userRole')
            self.enrollmentStatus.fromDict(fromDict, 'enrollmentStatus')
            self.userRoleStatus.fromDict(fromDict, 'userRoleStatus')
            self.model.fromDict(fromDict, 'model')
            self.devicePlatform.fromDict(fromDict, 'devicePlatform')
            self.nickname.fromDict(fromDict, 'vehicleNickname')
            self.brandCode.fromDict(fromDict, 'brandCode')

            if updateCapabilities and 'capabilities' in fromDict and fromDict['capabilities'] is not None:
                for capDict in fromDict['capabilities']:
                    if 'id' in capDict:
                        if capDict['id'] in self.capabilities:
                            self.capabilities[capDict['id']].update(fromDict=capDict)
                        else:
                            self.capabilities[capDict['id']] = GenericCapability(
                                capabilityId=capDict['id'], parent=self.capabilities, fromDict=capDict,
                                fixAPI=self.fixAPI)
                for capabilityId in [capabilityId for capabilityId in self.capabilities.keys()
                                     if capabilityId not in [capability['id']
                                     for capability in fromDict['capabilities'] if 'id' in capability]]:
                    del self.capabilities[capabilityId]
            else:
                self.capabilities.clear()
                self.capabilities.enabled = False

            if 'images' in fromDict:
                self.images.setValueWithCarTime(fromDict['images'], lastUpdateFromCar=None, fromServer=True)
            else:
                self.images.enabled = False

            if 'tags' in fromDict:
                self.tags.setValueWithCarTime(fromDict['tags'], lastUpdateFromCar=None, fromServer=True)
            else:
                self.tags.enabled = False

            if 'coUsers' in fromDict and fromDict['coUsers'] is not None:
                for user in fromDict['coUsers']:
                    if 'id' in user:
                        usersWithId = [x for x in self.coUsers if x.id.value == user['id']]
                        if len(usersWithId) > 0:
                            usersWithId[0].update(fromDict=user)
                        else:
                            self.coUsers.append(Vehicle.User(localAddress=str(len(self.coUsers)), parent=self.coUsers, fromDict=user))
                    else:
                        raise APICompatibilityError('User is missing id field')
                # Remove all users that are not in list anymore
                for user in [user for user in self.coUsers if user.id.value not in [x['id'] for x in fromDict['coUsers']]]:
                    self.coUsers.remove(user)
            else:
                self.coUsers.enabled = False
                self.coUsers.clear()

            for key, value in {key: value for key, value in fromDict.items()
                               if key not in ['vin',
                                              'role',
                                              'enrollmentStatus',
                                              'userRoleStatus',
                                              'model',
                                              'devicePlatform',
                                              'nickname',
                                              'brandCode',
                                              'capabilities',
                                              'images',
                                              'tags',
                                              'coUsers']}.items():
                LOG.warning('%s: Unknown attribute %s with value %s', self.getGlobalAddress(), key, value)

        self.updateStatus(updateCapabilities=updateCapabilities, force=force, selective=selective)

    def updateStatus(self, updateCapabilities: bool = True, force: bool = False,  # noqa: C901 # pylint: disable=too-many-branches
                selective: Optional[list[Domain]] = None):

        jobKeyClassMap: Dict[Domain, Dict[str, Type[GenericStatus]]] = {
            Domain.MEASUREMENTS: {
                'mileageKm': OdometerMeasurement,
            },

            # We will map cupra values to these standard ones
            Domain.CHARGING: {
                'batteryStatus': BatteryStatus,
                'chargingStatus': ChargingStatus,
                'chargingSettings': ChargingSettings,
            },
            Domain.CLIMATISATION: {
                'climatisationStatus': ClimatizationStatus,
                'climatisationSettings': ClimatizationSettings,
                # 'windowHeatingStatus': WindowHeatingStatus,
                # 'climatisationRequestStatus': GenericRequestStatus,
                # 'climatisationSettingsRequestStatus': GenericRequestStatus,
            },

            # Cupra only
            Domain.SERVICES: {
                'charging': ChargingStatus,     # -> Domain.CHARGING chargingStatus
                'climatisation': ClimatizationStatus
            },
            Domain.ENGINES: {
                'primary': EngineState
            }
        }

        if self.vin.value is None:
            raise APIError('VIN value is not set')
        if selective is None:
            jobs = [domain.value for domain in Domain if domain != Domain.ALL and domain != Domain.ALL_CAPABLE]
        elif Domain.ALL_CAPABLE in selective:
            if self.capabilities:
                jobs = []
                for dom in [domain for domain in Domain if domain != Domain.ALL and domain != Domain.ALL_CAPABLE]:
                    if dom.value in self.capabilities and self.capabilities[dom.value].enabled and not self.capabilities[dom.value].status.enabled:
                        jobs.append(dom.value)
                if updateCapabilities:
                    jobs.append(Domain.USER_CAPABILITIES.value)
            else:
                jobs = ['all']
        elif Domain.ALL in selective:
            jobs = ['all']
        else:
            jobs = [domain.value for domain in selective]
        
        url: str = f'{self.fetcher.base_url}/v2/users/{self.fetcher.user_id}/vehicles/{self.vin.value}/mycar'
        data: Optional[Dict[str, Any]] = self.fetcher.fetchData(url, force)

        if data is not None:
            # Iterate over top-level items in data dict
            for domain, keyClassMap in jobKeyClassMap.items():
                if not updateCapabilities and domain == Domain.USER_CAPABILITIES:
                    continue
                # if domain.value in data:
                if domain.value not in self.domains:
                    self.domains[domain.value] = DomainDict(localAddress=domain.value, parent=self.domains)
                
                for key, className in keyClassMap.items():
                    if domain.value in data:
                        if key in data[domain.value]:
                            if key in self.domains[domain.value]:
                                LOG.debug('Status %s exists, updating it', key)
                                self.domains[domain.value][key].update(fromDict=data[domain.value][key])
                            else:
                                LOG.debug('Status %s does not exist, creating it', key)
                                self.domains[domain.value][key] = className(vehicle=self, parent=self.domains[domain.value], statusId=key,
                                                                            fromDict=data[domain.value][key], fixAPI=self.fixAPI)
                    # else:
                        # Make a placeholder that we can overwrite later
                        # if key in self.domains[domain.value]:
                        # self.domains[domain.value][key] = className(vehicle=self, parent=self.domains[domain.value], statusId=key,
                        #                                                     fromDict={}, fixAPI=self.fixAPI)
                        # else:
                        #     self.domains[domain.value] = { key: None }
                if domain.value in data:
                    if 'error' in data[domain.value]:
                        self.domains[domain.value].updateError(data[domain.value])

                # check that there is no additional status than the configured ones, except for "target" that we merge into
                # the known ones
                # for key, value in {key: value for key, value in data[domain.value].items()
                #                     if key not in list(keyClassMap.keys()) and key not in ['error']}.items():
                #     LOG.warning('%s: Unknown attribute %s with value %s in domain %s', self.getGlobalAddress(), key, value, domain.value)
                # else:
                #     # Make a placeholder that we can overwrite later
                #     if domain.value not in self.domains:
                #         self.domains[domain.value] = DomainDict(localAddress=domain.value, parent=self.domains)

            # check that there is no additional domain than the configured ones
            for key, value in {key: value for key, value in data.items() if key not in list([domain.value for domain in jobKeyClassMap.keys()])}.items():
                LOG.warning('%s: Unknown domain %s with value %s', self.getGlobalAddress(), key, value)

        # Controls
        self.controls.update()

        # HACK map Cupra values back to VW values
        # We need this conditional otherwise it will fail if `data is not None`
        if Domain.SERVICES.value in self.domains:
            charging_dict = self.domains[Domain.SERVICES.value]['charging'].fromDict
            engines_dict = self.domains[Domain.ENGINES.value]['primary'].fromDict
            climatization_dict = self.domains[Domain.SERVICES.value]['climatisation'].fromDict
            # Create a charging domain object
            self.domains[Domain.CHARGING.value] = DomainDict(localAddress=Domain.CHARGING.value, parent=self.domains)

            charging_settings_dict = {
                'targetSOC_pct': charging_dict['targetPct']
            }
            self.domains[Domain.CHARGING.value]['chargingSettings'] = ChargingSettings(vehicle=self,
                parent=self.domains[Domain.CHARGING.value],
                statusId='chargingSettings',
                fixAPI=self.fixAPI,
                fromDict=charging_settings_dict)
            # We also have to call update(), not just pass fromDict to constructor
            self.domains[Domain.CHARGING.value]['chargingSettings'].update(charging_settings_dict)

            # Set charging status domain key
            charging_status_dict = {
                'remainingTime': charging_dict['remainingTime'],
                'status': charging_dict['status'],
                'chargeMode': charging_dict['chargeMode'],
            }
            self.domains[Domain.CHARGING.value]['chargingStatus'] = ChargingStatus(vehicle=self,
                parent=self.domains[Domain.CHARGING.value],
                statusId='chargingStatus',
                fixAPI=self.fixAPI,
                fromDict=charging_status_dict,
            )
            # # We also have to call update(), not just pass fromDict to constructor
            self.domains[Domain.CHARGING.value]['chargingStatus'].update(charging_status_dict)

            # Set battery status domain key
            battery_status_dict = {
                'currentSOC_pct': engines_dict['level'],
                'cruisingRangeElectric_km': engines_dict['range']['value']
            }
            self.domains[Domain.CHARGING.value]['batteryStatus'] = BatteryStatus(vehicle=self,
                parent=self.domains[Domain.CHARGING.value],
                statusId='batteryStatus',
                fixAPI=self.fixAPI,
                fromDict=battery_status_dict)
            # We also have to call update(), not just pass fromDict to constructor
            self.domains[Domain.CHARGING.value]['batteryStatus'].update(battery_status_dict)

            # Climate status domain key
            climate_status_dict = {
                'climatisationState': climatization_dict['status'],
                'remainingClimatisationTime_min': climatization_dict['remainingTime']
            }
            self.domains[Domain.CLIMATISATION.value]['climatisationStatus'] = ClimatizationStatus(vehicle=self,
                parent=self.domains[Domain.CLIMATISATION.value],
                statusId='climatisationStatus',
                fixAPI=self.fixAPI,
                fromDict=climate_status_dict)
            # We also have to call update(), not just pass fromDict to constructor
            self.domains[Domain.CLIMATISATION.value]['climatisationStatus'].update(climate_status_dict)

            # Climate settings domain key
            climate_settings_dict = {
                'targetTemperature_K': climatization_dict['targetTemperatureKelvin'],
                'targetTemperature_C': kelvinToCelsius(float(climatization_dict['targetTemperatureKelvin'])),
                'targetTemperature_F': kelvinToFarenheit(float(climatization_dict['targetTemperatureKelvin']))
            }
            self.domains[Domain.CLIMATISATION.value]['climatisationSettings'] = ClimatizationSettings(vehicle=self,
                parent=self.domains[Domain.CLIMATISATION.value],
                statusId='climatisationSettings',
                fixAPI=self.fixAPI,
                fromDict=climate_settings_dict)
            # We also have to call update(), not just pass fromDict to constructor
            self.domains[Domain.CLIMATISATION.value]['climatisationSettings'].update(climate_settings_dict)

    def __str__(self) -> str:  # noqa: C901
        returnString: str = ''
        if self.vin.enabled and self.vin.value is not None:
            returnString += f'VIN:               {self.vin.value}\n'
        if self.model.enabled and self.model.value is not None:
            returnString += f'Model:             {self.model.value}\n'
        if self.devicePlatform.enabled and self.devicePlatform.value is not None:
            returnString += f'Device Platform:   {self.devicePlatform.value.value}\n'
        if self.nickname.enabled and self.nickname.value is not None:
            returnString += f'Nickname:          {self.nickname.value}\n'
        if self.brandCode.enabled and self.brandCode.value is not None:
            returnString += f'Brand Code:        {self.brandCode.value.value}\n'
        if self.role.enabled and self.role.value is not None:
            returnString += f'Role:              {self.role.value.value}\n'  # pylint: disable=no-member
        if self.enrollmentStatus.enabled and self.enrollmentStatus.value is not None:
            returnString += f'Enrollment Status: {self.enrollmentStatus.value.value}\n'  # pylint: disable=no-member
        if self.userRoleStatus.enabled and self.userRoleStatus.value is not None:
            returnString += f'User Role Status:  {self.userRoleStatus.value.value}\n'  # pylint: disable=no-member
        if self.coUsers.enabled:
            returnString += f'Co-Users: {len(self.coUsers)} items\n'
            for coUser in self.coUsers:
                if coUser.enabled:
                    returnString += ''.join(['\t' + line for line in str(coUser).splitlines(True)]) + '\n'
        if self.tags.enabled and self.tags.value:
            returnString += 'Tags:               ' + ', '.join(self.tags.value) + '\n'
        if self.capabilities.enabled:
            returnString += f'Capabilities: {len(self.capabilities)} items\n'
            for capability in self.capabilities.values():
                if capability.enabled:
                    returnString += ''.join(['\t' + line for line in str(capability).splitlines(True)]) + '\n'
        if self.domains.enabled:
            returnString += f'Domains: {len(self.domains)} items\n'
            for domain in self.domains:
                returnString += f'[{domain}] Elements: {len(self.domains[domain])} items\n'
                for status in self.domains[domain].values():
                    if status.enabled:
                        returnString += ''.join(['\t' + line for line in str(status).splitlines(True)]) + '\n'
                if self.domains[domain].hasError():
                    returnString += ''.join(['\t' + line for line in f'Error: {self.domains[domain].error}'.splitlines(True)]) + '\n'
        return returnString

    class Badge(Enum):
        CHARGING = 'charging'
        CONNECTED = 'connected'
        COOLING = 'cooling'
        HEATING = 'heating'
        LOCKED = 'locked'
        PARKING = 'parking'
        UNLOCKED = 'unlocked'
        VENTILATING = 'ventilating'
        WARNING = 'warning'

    class DevicePlatform(Enum,):
        MBB = 'MBB'
        MBB_ODP = 'MBB_ODP'
        MBB_OFFLINE = 'MBB_OFFLINE'
        WCAR = 'WCAR'
        UNKNOWN = 'UNKNOWN'

    class BrandCode(Enum,):
        V = 'V'
        UNKNOWN = 'unknown brand code'

    class User(AddressableObject):
        def __init__(
            self,
            localAddress: str,
            parent: AddressableObject,
            fromDict: Dict[str, str] = {},
        ) -> None:
            super().__init__(localAddress=localAddress, parent=parent)
            self.id: AddressableAttribute[str] = AddressableAttribute(localAddress='id', parent=self, value=None, valueType=str)
            self.role: AddressableAttribute[Vehicle.User.Role] = AddressableAttribute(localAddress='role', parent=self, value=None, valueType=Vehicle.User.Role)
            self.roleReseted: AddressableAttribute[bool] = AddressableAttribute(localAddress='roleReseted', parent=self, value=None, valueType=bool)
            self.enrollmentStatus: AddressableAttribute[Vehicle.User.EnrollmentStatus] = AddressableAttribute(
                localAddress='enrollmentStatus', parent=self,
                value=None,
                valueType=Vehicle.User.EnrollmentStatus)

            if fromDict is not None:
                self.update(fromDict)

        def update(self, fromDict) -> None:
            LOG.debug('Update User from dict')

            if 'id' in fromDict:
                self.id.setValueWithCarTime(fromDict['id'], lastUpdateFromCar=None, fromServer=True)
            else:
                self.id.enabled = False

            if 'role' in fromDict and fromDict['role']:
                try:
                    self.role.setValueWithCarTime(Vehicle.User.Role(fromDict['role']), lastUpdateFromCar=None, fromServer=True)
                except ValueError:
                    self.role.setValueWithCarTime(Vehicle.User.Role.UNKNOWN, lastUpdateFromCar=None, fromServer=True)
                    LOG.warning('An unsupported role: %s was provided, please report this as a bug', fromDict['role'])
            else:
                self.role.enabled = False

            if 'roleReseted' in fromDict:
                self.roleReseted.setValueWithCarTime(toBool(fromDict['roleReseted']), lastUpdateFromCar=None, fromServer=True)
            else:
                self.roleReseted.enabled = False

            if 'enrollmentStatus' in fromDict and fromDict['enrollmentStatus']:
                try:
                    self.enrollmentStatus.setValueWithCarTime(Vehicle.User.EnrollmentStatus(fromDict['enrollmentStatus']), lastUpdateFromCar=None,
                                                              fromServer=True)
                except ValueError:
                    self.enrollmentStatus.setValueWithCarTime(Vehicle.User.EnrollmentStatus.UNKNOWN, lastUpdateFromCar=None, fromServer=True)
                    LOG.warning('An unsupported target operation: %s was provided, please report this as a bug', fromDict['enrollmentStatus'])
            else:
                self.enrollmentStatus.enabled = False

        def __str__(self) -> str:
            returnValue: str = ''
            if self.id.enabled and self.id.value is not None:
                returnValue += f'Id: {self.id.value}, '
            if self.role.enabled and self.role.value is not None:
                returnValue += f' Role: {self.role.value.value}, '  # pylint: disable=no-member
            if self.roleReseted.enabled and self.roleReseted.value is not None:
                returnValue += f' Reseted: {self.roleReseted.value}, '
            if self.enrollmentStatus.enabled and self.enrollmentStatus.value is not None:
                returnValue += f' Enrollment Status: {self.enrollmentStatus.value.value}'  # pylint: disable=no-member
            return returnValue

        class Role(Enum,):
            PRIMARY_USER = 'PRIMARY_USER'
            SECONDARY_USER = 'SECONDARY_USER'
            GUEST_USER = 'GUEST_USER'
            CDIS_UNKNOWN_USER = 'CDIS_UNKNOWN_USER'
            UNKNOWN = 'UNKNOWN'

            def __str__(self) -> str:
                return self.value

        class EnrollmentStatus(Enum,):
            STARTED = 'started'
            NOT_STARTED = 'not_started'
            COMPLETED = 'completed'
            GDC_MISSING = 'gdc_missing'
            INACTIVE = 'inactive'
            UNKNOWN = 'unknown'


        class UserRoleStatus(Enum,):
            ENABLED = 'ENABLED'
            DISABLED_HMI = 'DISABLED_HMI'
            DISABLED_SPIN = 'DISABLED_SPIN'
            DISABLED_PU_SPIN_RESET = 'DISABLED_PU_SPIN_RESET'
            CDIS_UNKNOWN_USER = 'CDIS_UNKNOWN_USER'
            UNKNOWN = 'UNKNOWN'
