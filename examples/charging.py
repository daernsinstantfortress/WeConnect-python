import argparse
import logging

from weconnect import weconnect
from weconnect.service import Service


def main():
    """ Simple example showing how to start climatization in a vehicle by providing the VIN as a parameter """
    parser = argparse.ArgumentParser(
        prog='climatization',
        description='Example starting climatizaton')
    parser.add_argument('-u', '--username', help='Username of Volkswagen id', required=True)
    parser.add_argument('-p', '--password', help='Password of Volkswagen id', required=True)
    parser.add_argument('-d', '--debug', help='Turn on debug logging', default=False, action='store_true')
    parser.add_argument('--service', help='Service to connect to. One of WeConnect, MyCupra', required=True)
    parser.add_argument('--vin', help='VIN of the vehicle to set charging', required=True)
    # Properties that modify car state
    parser.add_argument('--state', help='Charging state. One of start, stop', required=False)
    parser.add_argument('--target-soc', help='Target state of charge for car', required=False)
    parser.add_argument('--auto-unlock-plug-when-charged', help='Auto unlock plug when charged. One of permanent or off', required=False)
    parser.add_argument('--max-charge-current-ac', help='Set max charge current level. One of maximum or reduced', required=False)

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    # Construct based on service
    print('#  Initialize')
    service = Service(args.service)
    if service == Service.WE_CONNECT:
        from weconnect.elements.control_operation import ControlOperation
        from weconnect.api.vw.domain import Domain
        from weconnect.api.vw.elements.enums import MaximumChargeCurrent, UnlockPlugState
    elif service == Service.MY_CUPRA:
        from weconnect.elements.control_operation import ControlOperation
        from weconnect.api.cupra.domain import Domain
        from weconnect.api.cupra.elements.enums import MaximumChargeCurrent, UnlockPlugState
    weConnect = weconnect.WeConnect(username=args.username, password=args.password,
        updateAfterLogin=False, loginOnInit=False,
        service=service)

    print('#  Login')
    weConnect.login()
    print('#  Update')
    weConnect.update()

    for vin, vehicle in weConnect.vehicles.items():
        if vin == args.vin:

            print('#  charging status')
            if "charging" in vehicle.domains \
                and 'chargingStatus' in vehicle.domains["charging"] \
                and vehicle.domains["charging"]["chargingStatus"].enabled \
                and vehicle.domains["charging"]["chargingStatus"].chargingState.enabled:
                    print('   chargingState', vehicle.domains["charging"]["chargingStatus"].chargingState.value)
            if "charging" in vehicle.domains \
                and 'chargingStatus' in vehicle.domains["charging"] \
                and vehicle.domains["charging"]["chargingStatus"].enabled \
                and vehicle.domains["charging"]["chargingStatus"].remainingChargingTimeToComplete_min.enabled:
                    print('   remainingChargingTimeToComplete_min', vehicle.domains["charging"]["chargingStatus"].remainingChargingTimeToComplete_min.value)
            if "charging" in vehicle.domains \
                and 'chargingStatus' in vehicle.domains["charging"] \
                and vehicle.domains["charging"]["chargingStatus"].enabled \
                and vehicle.domains["charging"]["chargingStatus"].chargeMode.enabled:
                    print('   chargeMode', vehicle.domains["charging"]["chargingStatus"].chargeMode.value)
            if "charging" in vehicle.domains \
                and 'chargingStatus' in vehicle.domains["charging"] \
                and vehicle.domains["charging"]["chargingStatus"].enabled \
                and vehicle.domains["charging"]["chargingStatus"].chargePower_kW.enabled:
                    print('   chargePower_kW', vehicle.domains["charging"]["chargingStatus"].chargePower_kW.value)
            if "charging" in vehicle.domains \
                and 'chargingStatus' in vehicle.domains["charging"] \
                and vehicle.domains["charging"]["chargingStatus"].enabled \
                and vehicle.domains["charging"]["chargingStatus"].chargeRate_kmph.enabled:
                    print('   chargeRate_kmph', vehicle.domains["charging"]["chargingStatus"].chargeRate_kmph.value)
            if "charging" in vehicle.domains \
                and 'chargingStatus' in vehicle.domains["charging"] \
                and vehicle.domains["charging"]["chargingStatus"].enabled \
                and vehicle.domains["charging"]["chargingStatus"].chargeType.enabled:
                    print('   chargeType', vehicle.domains["charging"]["chargingStatus"].chargeType.value)
            if "charging" in vehicle.domains \
                and 'chargingStatus' in vehicle.domains["charging"] \
                and vehicle.domains["charging"]["chargingStatus"].enabled \
                and vehicle.domains["charging"]["chargingStatus"].chargingSettings.enabled:
                    print('   chargingSettings', vehicle.domains["charging"]["chargingStatus"].chargingSettings.value)

            print('#  battery status')
            if "charging" in vehicle.domains \
                and 'chargingStatus' in vehicle.domains["charging"] \
                and vehicle.domains["charging"]["batteryStatus"].enabled \
                and vehicle.domains["charging"]["batteryStatus"].currentSOC_pct.enabled:
                    print('   currentSOC_pct', vehicle.domains["charging"]["batteryStatus"].currentSOC_pct.value)
            if "charging" in vehicle.domains \
                and 'chargingStatus' in vehicle.domains["charging"] \
                and vehicle.domains["charging"]["batteryStatus"].enabled \
                and vehicle.domains["charging"]["batteryStatus"].cruisingRangeElectric_km.enabled:
                    print('   cruisingRangeElectric_km', vehicle.domains["charging"]["batteryStatus"].cruisingRangeElectric_km.value)

            print('#  charging settings')
            if "charging" in vehicle.domains \
                and 'chargingSettings' in vehicle.domains["charging"] \
                and vehicle.domains["charging"]["chargingSettings"].enabled \
                and vehicle.domains["charging"]["chargingSettings"].targetSOC_pct.enabled:
                    print('   targetSOC_pct', vehicle.domains["charging"]["chargingSettings"].targetSOC_pct.value)
            if "charging" in vehicle.domains \
                and 'chargingSettings' in vehicle.domains["charging"] \
                and vehicle.domains["charging"]["chargingSettings"].enabled \
                and vehicle.domains["charging"]["chargingSettings"].maxChargeCurrentAC.enabled:
                    print('   maxChargeCurrentAC', vehicle.domains["charging"]["chargingSettings"].maxChargeCurrentAC.value)
            if "charging" in vehicle.domains \
                and 'chargingSettings' in vehicle.domains["charging"] \
                and vehicle.domains["charging"]["chargingSettings"].enabled \
                and vehicle.domains["charging"]["chargingSettings"].autoUnlockPlugWhenCharged.enabled:
                    print('   autoUnlockPlugWhenCharged', vehicle.domains["charging"]["chargingSettings"].autoUnlockPlugWhenCharged.value)

            # Maybe change charging state
            if args.state:
                if vehicle.controls.chargingControl is not None and vehicle.controls.chargingControl.enabled:
                    print('#  set charging')
                    vehicle.controls.chargingControl.value = ControlOperation(value=args.state)
                else:
                    print('# Charging not supported')
                
            # Maybe change target SoC
            if args.target_soc:
                if 'charging' in vehicle.domains \
                        and vehicle.domains['charging']["chargingSettings"].enabled \
                        and vehicle.domains['charging']["chargingSettings"].targetSOC_pct.enabled:
                    print('#  set charging Target SoC')
                    vehicle.domains['charging']["chargingSettings"].targetSOC_pct.value = float(args.target_soc)
                else:
                    print('# Charging not supported')

            # Maybe change autoUnlockPlugWhenCharged
            if args.auto_unlock_plug_when_charged:
                if 'charging' in vehicle.domains \
                        and vehicle.domains['charging']["chargingSettings"].enabled \
                        and vehicle.domains['charging']["chargingSettings"].autoUnlockPlugWhenCharged.enabled:
                    print('#  set autoUnlockPlugWhenCharged')
                    vehicle.domains['charging']["chargingSettings"].autoUnlockPlugWhenCharged.value = UnlockPlugState(args.auto_unlock_plug_when_charged)
                else:
                    print('# Charging not supported')

            # Maybe change maxChargeCurrentAC
            if args.max_charge_current_ac:
                if 'charging' in vehicle.domains \
                        and vehicle.domains['charging']["chargingSettings"].enabled \
                        and vehicle.domains['charging']["chargingSettings"].maxChargeCurrentAC.enabled:
                    print('#  set maxChargeCurrentAC')
                    vehicle.domains['charging']["chargingSettings"].maxChargeCurrentAC.value = MaximumChargeCurrent(args.max_charge_current_ac)
                else:
                    print('# Charging not supported')

    print('#  done')

if __name__ == '__main__':
    main()
