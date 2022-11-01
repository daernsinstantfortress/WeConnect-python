"""Unit tests for Cupra service"""

from weconnect.addressable import AddressableDict
from weconnect.api.cupra.elements.battery_status import BatteryStatus
from weconnect.api.cupra.elements.charging_settings import ChargingSettings
from weconnect.api.cupra.elements.charging_status import ChargingStatus
from weconnect.api.cupra.elements.vehicle import Vehicle
from weconnect.api.cupra.domain import Domain

def test_vehicles_element_minimal_construction_not_charging():
    # Given
    range_value = 280.0
    charge_level = 80.0
    mileage_km = 1451.0
    charging_remaining_time = 0
    target_charge = 100
    class MockFetcher:
        base_url = 'https://example.com'
        user_id = 'USERID'
        def fetchData(self, url, force):
            # url: str = f'{self.fetcher.base_url}/v2/users/{self.fetcher.user_id}/vehicles/{self.vin.value}/mycar'
            return {
                "engines": {
                    "primary": {
                        "type": "EV",
                        "fuelType": "EV",
                        "range": { "value": range_value, "unit": "Km" },
                        "level": charge_level
                    },
                    "secondary": {
                        "type": None,
                        "fuelType": None,
                        "range": None,
                        "level": None
                    }
                },
                "measurements": { 
                    "mileageKm": mileage_km
                },
                "services": {
                    "charging": {
                        "status": "NotReadyForCharging",
                        "targetPct": target_charge,
                        "chargeMode": "manual",
                        "active": False,
                        "remainingTime": charging_remaining_time,
                        "progressBarPct": 100.0
                    },
                    "climatisation": {
                        "status": "Off",
                        "targetTemperatureKelvin": 295.15,
                        "active": False,
                        "remainingTime": 0,
                        "progressBarPct": 0.0
                    }
                }
            }
    fetcher = MockFetcher()
    vehicleDict = {
        'vin': 'VIN',
        'role': Vehicle.User.Role.PRIMARY_USER,
        'enrollmentStatus': Vehicle.User.EnrollmentStatus.COMPLETED,
        'userRoleStatus': Vehicle.User.UserRoleStatus.ENABLED,
        'nickname': 'CUPRA Born',
    }
    parent: AddressableDict[str, Vehicle] = AddressableDict(localAddress='xxx', parent=None)
    vehicle = Vehicle(
        fetcher=fetcher,
        vin='VINVINVINVINVIN',
        parent=parent,
        fromDict=vehicleDict,
        fixAPI=True,
        updateCapabilities=True,
        updatePictures=False,
        selective=None,
        enableTracker=False)
    # When
    # Note: update() is called in the constructor
    # Then
    assert vehicle.vin.value == vehicleDict['vin']
    assert vehicle.role.value == vehicleDict['role']
    assert vehicle.enrollmentStatus.value == vehicleDict['enrollmentStatus']
    assert vehicle.userRoleStatus.value == vehicleDict['userRoleStatus']
    assert vehicle.nickname.value == vehicleDict['nickname']
    # We don't have these for Cupra
    # assert vehicle.model.value == vehicleDict['model']
    # assert vehicle.devicePlatform.value == vehicleDict['devicePlatform']
    # assert vehicle.brandCode.value == vehicleDict['brandCode']
    assert vehicle.domains[Domain.MEASUREMENTS.value]['mileageKm'].odometer.value == mileage_km
    charging_status: ChargingStatus = vehicle.domains[Domain.CHARGING.value]['chargingStatus']
    assert charging_status.chargingState.value == ChargingStatus.ChargingState.NOT_READY_FOR_CHARGING
    assert charging_status.chargeMode.value == ChargingStatus.ChargeMode.MANUAL
    assert charging_status.remainingChargingTimeToComplete_min.value == charging_remaining_time
    # We don't have these for Cupra
    # charging_status.chargePower_kW
    # charging_status.chargeRate_kmph
    # charging_status.chargeType
    # charging_status.chargingSettings
    battery_status: BatteryStatus = vehicle.domains[Domain.CHARGING.value]['batteryStatus']
    assert battery_status.cruisingRangeElectric_km.value == range_value
    assert battery_status.currentSOC_pct.value == charge_level
    
    charging_settings: ChargingSettings = vehicle.domains[Domain.CHARGING.value]['chargingSettings']
    assert charging_settings.targetSOC_pct.value == target_charge


def test_vehicles_element_minimal_construction_charging():
    # Given
    range_value = 250.0
    charge_level = 78.0
    mileage_km = 1471.0
    charging_remaining_time = 355
    target_charge = 78.0
    status_charging = "Charging"
    class MockFetcher:
        base_url = 'https://example.com'
        user_id = 'USERID'
        def fetchData(self, url, force):
            # url: str = f'{self.fetcher.base_url}/v2/users/{self.fetcher.user_id}/vehicles/{self.vin.value}/mycar'
            return {
                "engines": {
                    "primary": {
                        "type": "EV",
                        "fuelType": "EV",
                        "range": { "value": range_value, "unit": "Km" },
                        "level": charge_level
                    },
                    "secondary": {
                        "type": None,
                        "fuelType": None,
                        "range": None,
                        "level": None
                    }
                },
                "measurements": { 
                    "mileageKm": mileage_km
                },
                "services": {
                    "charging": {
                        "status": status_charging,
                        "targetPct": target_charge,
                        "chargeMode": "manual",
                        "active": True,
                        "remainingTime": charging_remaining_time,
                        "progressBarPct": 100.0
                    },
                    "climatisation": {
                        "status": "Off",
                        "targetTemperatureKelvin": 295.15,
                        "active": False,
                        "remainingTime": 0,
                        "progressBarPct": 0.0
                    }
                }
            }
    fetcher = MockFetcher()
    vehicleDict = {
        'vin': 'VIN',
        'role': Vehicle.User.Role.PRIMARY_USER,
        'enrollmentStatus': Vehicle.User.EnrollmentStatus.COMPLETED,
        'userRoleStatus': Vehicle.User.UserRoleStatus.ENABLED,
        'nickname': 'CUPRA Born',
    }
    parent: AddressableDict[str, Vehicle] = AddressableDict(localAddress='xxx', parent=None)
    vehicle = Vehicle(
        fetcher=fetcher,
        vin='VINVINVINVINVIN',
        parent=parent,
        fromDict=vehicleDict,
        fixAPI=True,
        updateCapabilities=True,
        updatePictures=False,
        selective=None,
        enableTracker=False)
    # When
    # Note: update() is called in the constructor
    # Then
    assert vehicle.vin.value == vehicleDict['vin']
    assert vehicle.role.value == vehicleDict['role']
    assert vehicle.enrollmentStatus.value == vehicleDict['enrollmentStatus']
    assert vehicle.userRoleStatus.value == vehicleDict['userRoleStatus']
    assert vehicle.nickname.value == vehicleDict['nickname']
    # We don't have these for Cupra
    # assert vehicle.model.value == vehicleDict['model']
    # assert vehicle.devicePlatform.value == vehicleDict['devicePlatform']
    # assert vehicle.brandCode.value == vehicleDict['brandCode']
    assert vehicle.domains[Domain.MEASUREMENTS.value]['mileageKm'].odometer.value == mileage_km
    charging_status: ChargingStatus = vehicle.domains[Domain.CHARGING.value]['chargingStatus']
    assert charging_status.chargingState.value == ChargingStatus.ChargingState.CHARGING
    assert charging_status.chargeMode.value == ChargingStatus.ChargeMode.MANUAL
    assert charging_status.remainingChargingTimeToComplete_min.value == charging_remaining_time
    # We don't have these for Cupra
    # charging_status.chargePower_kW
    # charging_status.chargeRate_kmph
    # charging_status.chargeType
    # charging_status.chargingSettings
    battery_status: BatteryStatus = vehicle.domains[Domain.CHARGING.value]['batteryStatus']
    assert battery_status.cruisingRangeElectric_km.value == range_value
    assert battery_status.currentSOC_pct.value == charge_level
    
    charging_settings: ChargingSettings = vehicle.domains[Domain.CHARGING.value]['chargingSettings']
    assert charging_settings.targetSOC_pct.value == target_charge
    