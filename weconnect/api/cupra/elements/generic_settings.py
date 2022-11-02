from enum import Enum
import logging

import json
import requests

from weconnect.addressable import AddressableLeaf, ChangeableAttribute, AliasChangeableAttribute
from weconnect.api.cupra.elements.enums import ClimatizationState
from weconnect.api.cupra.elements.generic_status import GenericStatus
from weconnect.api.cupra.elements.error import Error
from weconnect.errors import SetterError
from weconnect.api.cupra.domain import Domain

LOG = logging.getLogger("weconnect")


class GenericSettings(GenericStatus):
    def valueChanged(self, element, flags):  # noqa: C901
        del element
        if flags & AddressableLeaf.ObserverEvent.VALUE_CHANGED \
                and not flags & AddressableLeaf.ObserverEvent.UPDATED_FROM_SERVER:
            action = self.id.partition('Settings')[0]
            if action == 'climatisationStatus':
                action = 'climatisation'
            # print(action)

            # Figure out state
            settingsDict = dict()
            for child in self.getLeafChildren():
                if isinstance(child, ChangeableAttribute) and not isinstance(child, AliasChangeableAttribute):
                    if isinstance(child.value, Enum):  # pylint: disable=no-member # this is a fales positive
                        settingsDict[child.getLocalAddress()] = child.value.value  # pylint: disable=no-member # this is a fales positive
                    else:
                        settingsDict[child.getLocalAddress()] = child.value  # pylint: disable=no-member # this is a fales positive
            # print(settingsDict)

            # if 'targetTemperature_K' in settingsDict:
            #     state = ''
            if 'climatisationState' in settingsDict:
                if settingsDict['climatisationState'] in [
                        ClimatizationState.COOLING.value,
                        ClimatizationState.HEATING.value,
                        ClimatizationState.VENTILATION.value,
                        ClimatizationState.ON.value
                    ]:
                    state = 'start'
                else:
                    state = 'stop'
            else:
                return


            url = f'https://ola.prod.code.seat.cloud.vwgroup.com/vehicles/{self.vehicle.vin.value}/{action}/requests/{state}'
            # print(url)

            self.vehicle.fetcher.post(url)
            # putResponse = self.vehicle.weConnect.session.put(url, data=data, allow_redirects=True)

            # TODO handle response
            # if putResponse.status_code != requests.codes['ok']:
            #     errorDict = putResponse.json()
            #     if errorDict is not None and 'error' in errorDict:
            #         error = Error(localAddress='error', parent=self, fromDict=errorDict['error'])
            #         if error is not None:
            #             message = ''
            #             if error.message.enabled and error.message.value is not None:
            #                 message += error.message.value
            #             if error.info.enabled and error.info.value is not None:
            #                 message += ' - ' + error.info.value
            #             if error.retry.enabled and error.retry.value is not None:
            #                 if error.retry.value:
            #                     message += ' - Please retry in a moment'
            #                 else:
            #                     message += ' - No retry possible'
            #             raise SetterError(f'Could not set value ({message})')
            #         else:
            #             raise SetterError(f'Could not set value ({putResponse.status_code})')
            #     raise SetterError(f'Could not not set value ({putResponse.status_code})')
            
            # TODO track stuff?
            # responseDict = putResponse.json()
            # if 'data' in responseDict and 'requestID' in responseDict['data']:
            #     if self.vehicle.requestTracker is not None:
            #         self.vehicle.requestTracker.trackRequest(responseDict['data']['requestID'], Domain.ALL, 20, 120)
