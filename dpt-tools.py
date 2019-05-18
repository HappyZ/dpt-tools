#!/usr/bin/python3


# builtins
import argparse

# lib
from python_api.libDPT import DPT
from python_api.libInteractive import diagnosis_mode
from python_api.libInteractive import update_firmware


def print_info():
    print("""===========
 DPT Tools
===========
Thanks for using DPT Tools. Type `help` to show this message.
Supported commands:
    fw        -- update firmware
    diagnosis -- enter diagnosis mode (to gain adb, su, etc.)
    exit/quit -- leave the tool
""")


def interactive(dpt, diagnosis=False):
    '''
    interactive shell to run commands
    @param dpt: DPT object
    @param diagnosis: if set True, will directly enter diagnosis mode
    '''
    firstTime = True
    if diagnosis:
        diagnosis_mode(dpt)
        return
    while(1):
        if firstTime:
            print_info()
            firstTime = False
        try:
            cmd = input(">>> ")
            cmd = cmd.lower()  # convert to lower case
        except KeyboardInterrupt:
            print()
            dpt.info_print("Press Ctrl + D to exit")
            continue
        except EOFError:
            print()
            dpt.info_print("Exiting... Thanks for using...")
            break
        except BaseException as e:
            print()
            cmd = ''
            dpt.err_print(str(e))
        # reauthenticate after every command
        if not dpt.reauthenticate():
            dpt.err_print("Cannot reauthenticate, did you reboot into normal mode?")
            dpt.err_print("Client id filepath: {}".format(dpt.client_id_fp))
            dpt.err_print("Client key filepath: {}".format(dpt.key_fp))
            break
        if cmd == 'exit' or cmd == 'quit':
            dpt.info_print("Exiting... Thanks for using...")
            break
        elif cmd == 'fw':
            update_firmware(dpt)
        elif cmd == 'help' or cmd == 'h':
            print_info()
        elif cmd == 'diagnosis':
            diagnosis_mode(dpt)


def main():
    '''
    main func to initalize dpt object
    '''
    p = argparse.ArgumentParser(description="DPT Tools")
    p.add_argument(
        '--client-id', '-id',
        dest="dpt_id",
        default="",
        help="File containing the device's client id")
    p.add_argument(
        '--key', '-k',
        dest="dpt_key",
        default="",
        help="File containing the device's private key")
    p.add_argument(
        '--addr', '-ip',
        dest="dpt_addr",
        default=None,
        help="Hostname or IP address of the device")
    p.add_argument(
        '--diagnosis',
        action='store_true',
        help="Run diagnosis mode directly")
    p.add_argument(
        '--debug', '-d',
        action='store_true',
        help="Run with debugging mode")

    try:
        args = vars(p.parse_args())
    except Exception as e:
        print(e)
        sys.exit()

    dpt = DPT(args.get('dpt_addr', None), args.get('debug', False))
    if (
        not args.get('diagnosis', False) and 
        not dpt.authenticate(args.get('dpt_id', ""), args.get('dpt_key', ""))
    ):
        dpt.err_print(
            "Cannot authenticate. " +
            "Make sure your id, key, and ip addresses are correct."
        )
        exit(1)

    interactive(dpt, diagnosis=args.get('diagnosis', False))


if __name__ == '__main__':
    main()