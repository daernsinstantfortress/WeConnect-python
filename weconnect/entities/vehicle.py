from __future__ import annotations
from typing import Dict, List, Set, Any, Type, Optional, cast, TYPE_CHECKING

from weconnect.addressable import AddressableObject, AddressableDict, AddressableAttribute, AddressableList

class Vehicle(AddressableObject):  # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        weConnect: WeConnect,
        vin: str,
        parent: AddressableDict[str, Vehicle],
        fromDict: Dict[str, Any],
        fixAPI: bool = True,
        updateCapabilities: bool = True,
        updatePictures: bool = True,
        selective: Optional[list[Domain]] = None,
        enableTracker: bool = False
    ) -> None:
        self.weConnect: WeConnect = weConnect
        super().__init__(localAddress=vin, parent=parent)

        # Public API used by HA volkswagen_we_connect_id
        self.model: AddressableAttribute[str] = AddressableAttribute(
            localAddress='model', parent=self, value=None, valueType=str)
        # Public API used by HA volkswagen_we_connect_id
        self.domains: AddressableDict[str, DomainDict[str, GenericStatus]] = AddressableDict(
            localAddress='domains', parent=self)
        # Public API used by HA volkswagen_we_connect_id
        self.controls: Controls = Controls(
            localAddress='controls', vehicle=self, parent=self)

        self.vin: AddressableAttribute[str] = AddressableAttribute(\
            localAddress='vin', parent=self, value=None, valueType=str)
        self.role: AddressableAttribute[Vehicle.User.Role] = AddressableAttribute(
            localAddress='role', parent=self, value=None, valueType=Vehicle.User.Role)
        self.enrollmentStatus: AddressableAttribute[Vehicle.User.EnrollmentStatus] = AddressableAttribute(
            localAddress='enrollmentStatus', parent=self, value=None, valueType=Vehicle.User.EnrollmentStatus)
        self.userRoleStatus: AddressableAttribute[Vehicle.User.UserRoleStatus] = AddressableAttribute(
            localAddress='userRoleStatus', parent=self, value=None, valueType=Vehicle.User.UserRoleStatus)
        self.devicePlatform: AddressableAttribute[Vehicle.DevicePlatform] = AddressableAttribute(
            localAddress='devicePlatform', parent=self, value=None, valueType=Vehicle.DevicePlatform)
        self.nickname: AddressableAttribute[str] = AddressableAttribute(localAddress='nickname', parent=self, value=None, valueType=str)
        self.brandCode: AddressableAttribute[str] = AddressableAttribute(localAddress='brandCode', parent=self, value=None, valueType=Vehicle.BrandCode)
        self.capabilities: AddressableDict[str, GenericCapability] = AddressableDict(localAddress='capabilities', parent=self)
        self.images: AddressableAttribute[Dict[str, str]] = AddressableAttribute(localAddress='images', parent=self, value=None, valueType=dict)
        self.tags: AddressableAttribute[List[str]] = AddressableAttribute(localAddress='tags', parent=self, value=None, valueType=list)
        self.coUsers: AddressableList[Vehicle.User] = AddressableList(localAddress='coUsers', parent=self)
        self.fixAPI: bool = fixAPI

        # if SUPPORT_IMAGES:
        #     self.__carImages: Dict[str, Image.Image] = {}
        #     self.__badges: Dict[Vehicle.Badge, Image.Image] = {}
        #     self.pictures: AddressableDict[str, Image.Image] = AddressableDict(localAddress='pictures', parent=self)

        # self.requestTracker: Optional[RequestTracker] = None
        # if enableTracker:
        #     self.requestTracker = RequestTracker(self)

        # self.update(fromDict, updateCapabilities=updateCapabilities, updatePictures=updatePictures, selective=selective)
