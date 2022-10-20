from __future__ import annotations
from typing import Dict, List, Set, Tuple, Callable, Any, Optional
import logging
from datetime import datetime

from weconnect.addressable import AddressableDict
from weconnect.errors import RetrievalError
from weconnect.api.vw.domain import Domain
from weconnect.api.vw.elements.vehicle import Vehicle
from weconnect.api.vw.elements.charging_station import ChargingStation


LOG = logging.getLogger("weconnect")


class VwApi:
    def __init__(self):
        self.base_url = 'https://mobileapi.apps.emea.vwapps.io'

        self.__vehicles: AddressableDict[str, Vehicle] = AddressableDict(localAddress='vehicles', parent=self)
        self.__stations: AddressableDict[str, ChargingStation] = AddressableDict(localAddress='chargingStations', parent=self)

    def update(self, updateCapabilities: bool = True, updatePictures: bool = True, force: bool = False,
            selective: Optional[list[Domain]] = None) -> Tuple[AddressableDict[str, Vehicle], AddressableDict[str, ChargingStation]]:
        self.updateVehicles(updateCapabilities=updateCapabilities, updatePictures=updatePictures, force=force, selective=selective)
        self.updateChargingStations(force=force)
        return (self.__vehicles, self.__stations)

    def updateVehicles(self, updateCapabilities: bool = True, updatePictures: bool = True, force: bool = False,  # noqa: C901
                       selective: Optional[list[Domain]] = None) -> None:
        url = f'{self.base_url}/vehicles'
        data = self.fetchData(url, force)
        if data is not None:
            if 'data' in data and data['data']:
                vins: List[str] = []
                for vehicleDict in data['data']:
                    if 'vin' not in vehicleDict:
                        break
                    vin: str = vehicleDict['vin']
                    vins.append(vin)
                    try:
                        if vin not in self.__vehicles:
                            vehicle = Vehicle(weConnect=self, vin=vin, parent=self.__vehicles, fromDict=vehicleDict, fixAPI=self.fixAPI,
                                              updateCapabilities=updateCapabilities, updatePictures=updatePictures, selective=selective,
                                              enableTracker=self.__enableTracker)
                            self.__vehicles[vin] = vehicle
                        else:
                            self.__vehicles[vin].update(fromDict=vehicleDict, updateCapabilities=updateCapabilities, updatePictures=updatePictures,
                                                        selective=selective)
                    except RetrievalError as retrievalError:
                        LOG.error('Failed to retrieve data for VIN %s: %s', vin, retrievalError)
                # delete those vins that are not anymore available
                for vin in [vin for vin in self.__vehicles if vin not in vins]:
                    del self.__vehicles[vin]

                self.__cache[url] = (data, str(datetime.utcnow()))

    def updateChargingStations(self, force: bool = False) -> None:  # noqa: C901 # pylint: disable=too-many-branches
        if self.latitude is not None and self.longitude is not None:
            url: str = f'{self.base_url}/charging-stations/v2?latitude={self.latitude}&longitude={self.longitude}'
            if self.market is not None:
                url += f'&market={self.market}'
            if self.useLocale is not None:
                url += f'&locale={self.useLocale}'
            if self.searchRadius is not None:
                url += f'&searchRadius={self.searchRadius}'
            if self.__userId is not None:
                url += f'&userId={self.__userId}'
            data = self.fetchData(url, force)
            if data is not None:
                if 'chargingStations' in data and data['chargingStations']:
                    ids: List[str] = []
                    for stationDict in data['chargingStations']:
                        if 'id' not in stationDict:
                            break
                        stationId: str = stationDict['id']
                        ids.append(stationId)
                        if stationId not in self.__stations:
                            station: ChargingStation = ChargingStation(weConnect=self, stationId=stationId, parent=self.__stations, fromDict=stationDict,
                                                                       fixAPI=self.fixAPI)
                            self.__stations[stationId] = station
                        else:
                            self.__stations[stationId].update(fromDict=stationDict)
                    # delete those vins that are not anymore available
                    for stationId in [stationId for stationId in ids if stationId not in self.__stations]:
                        del self.__stations[stationId]

                    self.__cache[url] = (data, str(datetime.utcnow()))

    def getChargingStations(self, latitude, longitude, searchRadius=None, market=None, useLocale=None,  # noqa: C901
                            force=False) -> AddressableDict[str, ChargingStation]:
        chargingStationMap: AddressableDict[str, ChargingStation] = AddressableDict(localAddress='', parent=None)
        url: str = f'{self.base_url}/charging-stations/v2?latitude={latitude}&longitude={longitude}'
        if market is not None:
            url += f'&market={market}'
        if useLocale is not None:
            url += f'&locale={useLocale}'
        if searchRadius is not None:
            url += f'&searchRadius={searchRadius}'
        if self.__userId is not None:
            url += f'&userId={self.__userId}'
        data = self.fetchData(url, force)
        if data is not None:
            if 'chargingStations' in data and data['chargingStations']:
                for stationDict in data['chargingStations']:
                    if 'id' not in stationDict:
                        break
                    stationId: str = stationDict['id']
                    station: ChargingStation = ChargingStation(weConnect=self, stationId=stationId, parent=chargingStationMap, fromDict=stationDict,
                                                               fixAPI=self.fixAPI)
                    chargingStationMap[stationId] = station

                self.__cache[url] = (data, str(datetime.utcnow()))
        return chargingStationMap
