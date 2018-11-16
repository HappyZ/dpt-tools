#!/usr/bin/python3


# builtins
import argparse

# lib
from python_api.libDPT import DPT
from python_api.libDPT import update_firmware
from python_api.libDPT import obtain_diagnosis_access


def print_info():
    print("""Thanks for using DPT Tools.
Type `help` to show this message.

Supported commands:
  fw -- update firmware
  root (thanks to shankerzhiwu and his/her anoymous friend) -- obtain root access
""")


def interactive(dpt):
    '''
    interactive shell to run commands
    '''
    firstTime = True
    while(1):
        if firstTime:
            print_info()
            firstTime = False
        try:
            cmd = input(">>> ")
            cmd = cmd.lower()  # convert to lower case
        except KeyboardInterrupt:
            print()
            dpt.info_print("Exiting... Thanks for using...")
            break
        except BaseException as e:
            print()
            dpt.err_print(str(e))
        if cmd == 'root':
            obtain_diagnosis_access(dpt)
        elif cmd == 'exit' or cmd == 'quit':
            dpt.info_print("Exiting... Thanks for using...")
            break
        elif cmd == 'fw':
            update_firmware(dpt)
        elif cmd == 'help' or cmd == 'h':
            print_info()


def main():
    '''
    main func to initalize dpt object
    '''
    p = argparse.ArgumentParser(
        description="DPT Tools")
    p.add_argument(
        '--client-id', '-id',
        dest="dpt_id",
        help="File containing the device's client id",
        required=True)
    p.add_argument(
        '--key', '-k',
        dest="dpt_key",
        help="File containing the device's private key",
        required=True)
    p.add_argument(
        '--addr', '-ip',
        dest="dpt_addr",
        default=None,
        help="Hostname or IP address of the device")
    p.add_argument(
        '--debug', '-d',
        action='store_true',
        help="Run with debugging mode")

    try:
        args = vars(p.parse_args())
    except Exception as e:
        print(e)
        sys.exit()

    dpt = DPT(args.get('apt_addr', None), args.get('debug', False))
    if not dpt.authenticate(args.get('dpt_id', ""), args.get('dpt_key', "")):
        dpt.err_print("Cannot authenticate. Make sure your id, key, and ip addresses are correct.")
        exit(1)

    interactive(dpt)


if __name__ == '__main__':
    main()