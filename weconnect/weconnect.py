from __future__ import annotations
from typing import Dict, List, Any, Optional

import locale
import logging
from datetime import timedelta

from weconnect.auth.openid_session import OpenIDSession
from weconnect.auth.session_manager import SessionManager, Service, SessionUser
from weconnect.addressable import AddressableLeaf, AddressableObject, AddressableDict
from weconnect.fetch import Fetcher
from weconnect.errors import ErrorBus
# VW specific
from weconnect.api.vw.domain import Domain
from weconnect.api.vw.api import VwApi
from weconnect.api.vw.elements.vehicle import Vehicle as VwVehicle
from weconnect.api.vw.elements.charging_station import ChargingStation as VwChargingStation
# Cupra specific
from weconnect.api.cupra.api import CupraApi
from weconnect.api.cupra.elements.vehicle import Vehicle as CupraVehicle
from weconnect.api.cupra.elements.charging_station import ChargingStation as CupraChargingStation

LOG = logging.getLogger("weconnect")

class WeConnect(AddressableObject):  # pylint: disable=too-many-instance-attributes, too-many-public-methods
    """Main class used to interact with WeConnect"""

    def __init__(  # noqa: C901 # pylint: disable=too-many-arguments
        self,
        username: str,
        password: str,
        tokenfile: Optional[str] = None,
        updateAfterLogin: bool = True,
        loginOnInit: bool = False,
        fixAPI: bool = True,
        maxAge: Optional[int] = None,
        maxAgePictures: Optional[int] = None,
        updateCapabilities: bool = True,
        updatePictures: bool = True,
        numRetries: int = 3,
        timeout: bool = None,
        selective: Optional[list[Domain]] = None,
        service = Service.WE_CONNECT
    ) -> None:
        """Initialize WeConnect interface. If loginOnInit is true the user will be tried to login.
           If loginOnInit is true also an initial fetch of data is performed.

        Args:
            username (str): Username used with WeConnect. This is your volkswagen user.
            password (str): Password used with WeConnect. This is your volkswagen password.
            tokenfile (str, optional): Optional file to read/write token from/to. Defaults to None.
            updateAfterLogin (bool, optional): Update data from WeConnect after logging in (If set to false, update needs to be called manually).
            Defaults to True.
            loginOnInit (bool, optional): Login after initialization (If set to false, login needs to be called manually). Defaults to True.
            fixAPI (bool, optional): Automatically fix known issues with the WeConnect responses. Defaults to True.
            maxAge (int, optional): Maximum age of the cache before date is fetched again. None means no caching. Defaults to None.
            maxAgePictures (Optional[int], optional):  Maximum age of the pictures in the cache before date is fetched again. None means no caching.
            Defaults to None.
            updateCapabilities (bool, optional): Also update the information about the cars capabilities. Defaults to True.
            updatePictures (bool, optional):  Also fetch and update pictures. Defaults to True.
            numRetries (int, optional): Number of retries when http requests are failing. Defaults to 3.
            timeout (bool, optional, optional): Timeout in seconds used for http connections to the VW servers
            selective (list[Domain], optional): Domains to request data for
        """
        super().__init__(localAddress='', parent=None)
        self.username: str = username
        self.password: str = password

        self.__userId: Optional[str] = None  # pylint: disable=unused-private-member
        # self.__session: requests.Session = requests.Session()

        # Entities
        self.__vehicles: AddressableDict[str, VwVehicle|CupraVehicle] = AddressableDict(localAddress='vehicles', parent=self)
        self.__stations: AddressableDict[str, VwChargingStation|CupraChargingStation] = AddressableDict(localAddress='chargingStations', parent=self)
        
        self.fixAPI: bool = fixAPI

        # Public api used by weconnect-mqtt
        self.latitude: Optional[float] = None
        # Public api used by weconnect-mqtt
        self.longitude: Optional[float] = None
        # Public api used by weconnect-mqtt
        self.searchRadius: Optional[int] = None

        self.market: Optional[str] = None
        self.useLocale: Optional[str] = locale.getlocale()[0]
        self.__elapsed: List[timedelta] = []
        self.tokenfile = tokenfile
        self.__enableTracker: bool = False

        # Session management
        self.__manager = SessionManager(tokenstorefile=tokenfile)
        self.__session: OpenIDSession = self.__manager.getSession(service, SessionUser(username=username, password=password))
        self.__session.timeout = timeout
        self.__session.retries = numRetries

        self._errorBus: ErrorBus = ErrorBus()
        self._fetcher: Fetcher = Fetcher(session=self.__session, maxAge=maxAge, maxAgePictures=maxAgePictures, errorBus=ErrorBus())

        if loginOnInit:
            self.__session.login()

        if service == Service.MY_CUPRA:
            self._api = CupraApi(weconnect=self, fetcher=self._fetcher)
        else:
            self._api = VwApi()
        self._fetcher.base_url = self._api.base_url

        if updateAfterLogin:
            self.update(updateCapabilities=updateCapabilities, updatePictures=updatePictures, selective=selective)


    def __del__(self) -> None:
        self.disconnect()
        return super().__del__()

    # Public api used by weconnect-mqtt
    def disconnect(self) -> None:
        pass

    @property
    def session(self) -> OpenIDSession:
        return self.__session

    @property
    def cache(self) -> Dict[str, Any]:
        return self._fetcher.cache

    # Public api used by weconnect-mqtt
    def persistTokens(self) -> None:
        if self.__manager is not None and self.tokenfile is not None:
            self.__manager.saveTokenstore(self.tokenfile)

    # Public api used by weconnect-mqtt
    def enableTracker(self) -> None:
        self.__enableTracker = True
        for vehicle in self.vehicles:
            vehicle.enableTracker()

    def disableTracker(self) -> None:
        self.__enableTracker = True
        for vehicle in self.vehicles:
            vehicle.disableTracker()

    # Public api used by HA volkswagen_we_connect_id
    def login(self) -> None:
        self.__session.login()

    # Public api used by HA volkswagen_we_connect_id
    @property
    def vehicles(self) -> AddressableDict[str, VwVehicle|CupraVehicle]:
        return self.__vehicles

    # Public api used by weconnect-mqtt, HA volkswagen_we_connect_id
    def update(self, updateCapabilities: bool = True, updatePictures: bool = True, force: bool = False,
               selective: Optional[list[Domain]] = None) -> None:
        self.__elapsed.clear()
        vehicles, charging_stations = self._api.update(updateCapabilities=updateCapabilities, updatePictures=updatePictures, force=force, selective=selective)
        self.__vehicles = vehicles
        self.__stations = charging_stations
        self.updateComplete()

    def setChargingStationSearchParameters(self, latitude: float, longitude: float, searchRadius: Optional[int] = None, market: Optional[str] = None,
                                           useLocale: Optional[str] = locale.getlocale()[0]) -> None:
        self.latitude = latitude
        self.longitude = longitude
        self.searchRadius = searchRadius
        self.market = market
        self.useLocale = useLocale

    def getLeafChildren(self) -> List[AddressableLeaf]:
        return [children for vehicle in self.__vehicles.values() for children in vehicle.getLeafChildren()] \
            + [children for station in self.__stations.values() for children in station.getLeafChildren()]

    def __str__(self) -> str:
        returnString: str = ''
        for vin, vehicle in self.__vehicles.items():
            returnString += f'Vehicle: {vin}\n{vehicle}\n'
        for stationId, station in sorted(self.__stations.items(), key=lambda x: x[1].distance.value, reverse=False):
            returnString += f'Charging Station: {stationId}\n{station}\n'
        return returnString

    def recordElapsed(self, elapsed: timedelta) -> None:
        self.__elapsed.append(elapsed)

    def getMinElapsed(self) -> timedelta|None:
        if len(self.__elapsed) == 0:
            return None
        return min(self.__elapsed)

    def getMaxElapsed(self) -> timedelta|None:
        if len(self.__elapsed) == 0:
            return None
        return max(self.__elapsed)

    def getAvgElapsed(self) -> timedelta|None:
        if len(self.__elapsed) == 0:
            return None
        return sum(self.__elapsed, timedelta()) / len(self.__elapsed)

    def getTotalElapsed(self) -> timedelta|None:
        if len(self.__elapsed) == 0:
            return None
        return sum(self.__elapsed, timedelta())

