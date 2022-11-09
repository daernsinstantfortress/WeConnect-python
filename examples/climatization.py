import argparse
import logging

from weconnect import weconnect
from weconnect.service import Service
from weconnect.elements.control_operation import ControlOperation

def main():
    """ Simple example showing how to start climatization in a vehicle by providing the VIN as a parameter """
    parser = argparse.ArgumentParser(
        prog='climatization',
        description='Example starting climatizaton')
    parser.add_argument('-u', '--username', help='Username of Volkswagen id', required=True)
    parser.add_argument('-p', '--password', help='Password of Volkswagen id', required=True)
    parser.add_argument('--service', help='Service to connect to. One of WeConnect, MyCupra', required=True)
    parser.add_argument('--vin', help='VIN of the vehicle to set climatization', required=True)
    parser.add_argument('--state', help='Climatization state. One of start, stop', required=False)

    args = parser.parse_args()

    # logging.basicConfig(level=logging.DEBUG)

    # Construct based on service
    print('#  Initialize')
    service = Service(args.service)
    weConnect = weconnect.WeConnect(username=args.username, password=args.password,
        updateAfterLogin=False, loginOnInit=False,
        service=service)

    print('#  Login')
    weConnect.login()
    print('#  Update')
    weConnect.update()

    for vin, vehicle in weConnect.vehicles.items():
        print(vin)
        if vin == args.vin:
            if "climatisation" in vehicle.domains \
                    and "climatisationStatus" in vehicle.domains["climatisation"] \
                    and vehicle.domains["climatisation"]["climatisationStatus"].enabled:
                if vehicle.domains["climatisation"]["climatisationStatus"].climatisationState.enabled:
                    print('#  climatization status')
                    print(vehicle.domains["climatisation"]["climatisationStatus"].climatisationState.value)

            if args.state:
                if vehicle.controls.climatizationControl is not None and vehicle.controls.climatizationControl.enabled:
                    print('#  set climatization')
                    vehicle.controls.climatizationControl.value = ControlOperation(value=args.state)
                else:
                    print('# Climatization not supported')

    print('#  done')

if __name__ == '__main__':
    main()
