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
    parser.add_argument('--service', help='Service to connect to. One of WeConnect, MyCupra', required=True)
    parser.add_argument('--vin', help='VIN of the vehicle to set charging', required=True)
    parser.add_argument('--state', help='Charging state. One of start, stop', required=True)

    args = parser.parse_args()

    # logging.basicConfig(level=logging.DEBUG)

    # Construct based on service
    print('#  Initialize')
    service = Service(args.service)
    if service == Service.WE_CONNECT:
        from weconnect.api.vw.elements.control_operation import ControlOperation
    elif service == Service.MY_CUPRA:
        from weconnect.api.cupra.elements.control_operation import ControlOperation
    weConnect = weconnect.WeConnect(username=args.username, password=args.password,
        updateAfterLogin=False, loginOnInit=False,
        service=service)

    print('#  Login')
    weConnect.login()
    print('#  Update')
    weConnect.update()

    for vin, vehicle in weConnect.vehicles.items():
        if vin == args.vin:
            if "charging" in vehicle.domains \
                and 'chargingStatus' in vehicle.domains["charging"] \
                and vehicle.domains["charging"]["chargingStatus"].enabled:
                if vehicle.domains["charging"]["chargingStatus"].chargingState.enabled:
                    print('#  charging status')
                    print(vehicle.domains["charging"]["chargingStatus"].chargingState.value)

            if vehicle.controls.chargingControl is not None and vehicle.controls.chargingControl.enabled:
                print('#  set charging')
                vehicle.controls.chargingControl.value = ControlOperation(value=args.state)
            else:
                print('# Charging not supported')

    print('#  done')

if __name__ == '__main__':
    main()
