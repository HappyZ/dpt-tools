#!/usr/bin/python3

# built-ins
import os
import time
import subprocess
# import traceback


def validate_required_files(dpt):
    requiredFiles = [
        'python_api/shankerzhiwu_disableidcheck.pkg',
        'python_api/shankerzhiwu_changepwd.pkg'
    ]
    dpt.dbg_print('Checking required files...')
    for file in requiredFiles:
        if not os.path.isfile(file):
            dpt.err_print('File {0} does not exist!'.format(file))
            return False
    return True


def disable_id_check(dpt):
    '''
    disable the id check (thanks to shankerzhiwu and his/her friend)
    '''
    fp = 'python_api/shankerzhiwu_disableidcheck.pkg'
    try:
        resp = input('>>> Have you disabled the id check already? [yes/no]: ')
        if resp == 'no':
            if not dpt.update_firmware(open(fp, 'rb')):
                dpt.err_print('Failed to upload shankerzhiwu_disableidcheck pkg')
                return False
            try:
                input(
                    '>>> Press `Enter` key to continue after your DPT reboot, ' +
                    'shows `update failure` message, and connects back to WiFi: ')
            except BaseException as e:
                dpt.err_print(str(e))
                return False
            return True
        elif resp == 'yes':
            return True
        else:
            dpt.err_print('Unrecognized response: {}'.format(resp))
    except BaseException as e:
        dpt.err_print(str(e))
    return False


def reset_root_password(dpt):
    '''
    reset the root password (thanks to shankerzhiwu and his/her friend)
    '''
    fp = 'python_api/shankerzhiwu_changepwd.pkg'
    try:
        if not dpt.update_firmware(open(fp, 'rb')):
            dpt.err_print('Failed to upload shankerzhiwu_changepwd pkg')
            return False
        return True
    except BaseException as e:
        dpt.err_print(str(e))
        return False


def obtain_diagnosis_access(dpt):
    '''
    root thanks to shankerzhiwu
    '''
    dpt.info_print(
        'Please make sure you have charged your battery before this action.')
    dpt.info_print(
        'Thank shankerzhiwu (and his/her anonymous friend) a lot on this hack!!!' +
        'All credits go to him (and his/her anonymous friend)!')
    if not validate_required_files(dpt):
        return False
    # step 1: disable the id check
    if not disable_id_check(dpt):
        return False
    dpt.info_print('Congrats! You are half-way through! You have disabled the OTG ID check')
    # step 2: reset root password
    if not reset_root_password(dpt):
        return False
    dpt.info_print(
        'You are all set! Wait till your DPT reboots and ' +
        'shows `update failure` message! More edits will be added to this tool.')
    return True


def update_firmware(dpt):
    '''
    update firmware interface
    '''
    dpt.info_print(
        'Please make sure you have charged your battery before this action.')
    try:
        resp = input('>>> Please enter the pkg file path: ')
        if not os.path.isfile(resp):
            dpt.err_print('File `{}` does not exist!'.format(resp))
            return False
        resp2 = input('>>> Pleae confirm {} is the pkg file to use [yes/no]: ')
        if resp2 == 'yes':
            if not dpt.update_firmware(open(resp, 'rb')):
                dpt.err_print('Failed to upload pkg {}'.format(resp))
                return False
            dpt.info_print('Success!')
            return True
        elif resp == 'no':
            dpt.info_print('Okay!')
        else:
            dpt.err_print('Unrecognized response: {}'.format(resp))
    except BaseException as e:
        dpt.err_print(str(e))
    return False


def print_diagnosis_info():
    print("""============================
 DPT Tools - Diagnosis Mode
============================
This is diagnosis mode. Type `help` to show this message.
It behaves similarly to regular serial session with less flexibility (cannot use tab, scroll up, quick reverse search, etc.).
This mode intends to automate some complicated procedures.

Supported commands:
    `push-file` -- transfer file to DPT at 512bps
    `pull-file` -- transfer file from DPT
    `exit`/`quit`   -- leave the tool
    and many unix cmds (do not support less/head)
""")


def diagnosis_pull_file(dpt):
    '''
    pull file from device to local via xxd and parsing in 
    python
    do NOT pull large file using this, it will take forever
    to finish..
    '''
    try:
        # get and validate remote file path
        remotefp = input('> DPT file path: ')
        if not dpt.diagnosis_isfile(remotefp):
            dpt.err_print('File {} does not exist!'.format(remotefp))
            return False
        # get local folder path
        folder = input('> Local folder path: ')
        if not os.path.isdir(folder):
            resp = input('> {} not exist, create? [yes/no]: '.format(folder))
            if resp == 'no':
                return False
            elif resp == 'yes':
                os.makedirs(folder)
            else:
                dpt.err_print('Unrecognized input {}'.format(resp))
                return False
        # check if local fp exists
        localfp = "{0}/{1}".format(folder, os.path.basename(remotefp))
        if os.path.isfile(localfp):
            resp = input('> {} exist, overwrite? [yes/no]: '.format(localfp))
            if resp == 'no':
                return False
            elif not resp == 'yes':
                dpt.err_print('Unrecognized input {}'.format(resp))
                return False
        # read from xxd, parse, and write to local file
        startTime = int(time.time() * 1000)
        cmd = "xxd -p {}".format(remotefp)
        with open("{}.tmp".format(localfp), 'w') as f:
            for each in dpt.diagnosis_write(cmd, timeout=999).splitlines():
                f.write(each)
        subprocess.call(
            ['xxd', '-r', '-p', "{}.tmp".format(localfp), '>', localfp]
        )
        duration = int(time.time() * 1000) - startTime
        dpt.info_print('Finished in {0:.2f}sec'.format(duration / 1000.0))
        if os.path.isfile(localfp):
            dpt.info_print("Success")
            os.remove("{}.tmp".format(localfp))
            return True
    except BaseException as e:
        dpt.err_print(str(e))
    return False


def diagnosis_push_file(dpt, chunkSize=128):
    '''
    push file from local to device through echo in diagnosis
    (serial) mode
    using echo is dumb and slow but very reliable
    limited to 128 bytes per sec since we send raw bytes in
    string (each byte sent = 4 bytes), and terminal at best
    allows 1024 bytes to send
    do NOT push large file using this, it will take
    forever to finish..
    '''
    try:
        # get local file path
        localfp = input('> Local file path: ')
        while localfp[-1] == ' ':  # remove extra spaces
            localfp = localfp[:-1]
        if not os.path.isfile(localfp):
            dpt.err_print('File {} does not exist!'.format(localfp))
            return False
        # get remote folder and validate it
        folder = input('> DPT folder path: ')
        # folder does not exit, create one?
        if not dpt.diagnosis_isfolder(folder):
            resp = input('> {} not exist, create? [yes/no]: '.format(folder))
            if resp == 'no':
                return False
            elif resp == 'yes':
                dpt.diagnosis_write('mkdir -p {}'.format(folder))
            else:
                dpt.err_print('Unrecognized input {}'.format(resp))
                return False
        # remote file exists, overwrite it?
        remotefp = "{0}/{1}".format(folder, os.path.basename(localfp))
        if dpt.diagnosis_isfile(remotefp):
            resp = input('> {} exist, overwrite? [yes/no]: '.format(remotefp))
            if resp == 'no':
                return False
            elif not resp == 'yes':
                dpt.err_print('Unrecognized input {}'.format(resp))
                return False
        # write through echo
        firstRun = True
        symbol = '>'
        startTime = int(time.time() * 1000)
        with open(localfp, 'rb') as f:
            while 1:
                chunk = f.read(chunkSize)
                if chunk:
                    cmd = "echo -e -n '\\x{0}' {1} {2}".format(
                        '\\x'.join('{:02x}'.format(x) for x in chunk),
                        symbol,
                        remotefp
                    )
                    dpt.diagnosis_write(cmd)
                else:
                    break
                if firstRun:
                    symbol = '>>'
                    firstRun = False
        duration = int(time.time() * 1000) - startTime
        dpt.info_print('Finished in {0:.2f}sec'.format(duration / 1000.0))
        if dpt.diagnosis_isfile(remotefp):
            dpt.info_print("Success")
            return True
    except BaseException as e:
        dpt.err_print(str(e))
    return False


def diagnosis_cmd(dpt):
    '''
    run commands in diagnosis mode
    '''
    # login
    if not dpt.diagnosis_login(username='root', password='12345'):
        dpt.err_print('failed to login..')
        return
    # interactive mode
    firstTime = True
    frontLine = 'root #: '
    while 1:
        if firstTime:
            print_diagnosis_info()
            firstTime = False
        try:
            cmd = input(frontLine)
            if cmd == 'exit' or cmd == 'quit':
                break
            elif cmd == 'help':
                print_diagnosis_info()
                continue
            elif cmd == 'push-file':
                diagnosis_push_file(dpt)
                continue
            elif cmd == 'pull-file':
                diagnosis_pull_file(dpt)
                continue
            rawresp = dpt.diagnosis_write(cmd)
            # ignore first and last echos
            tmp = rawresp.splitlines()
            frontLine = tmp[-1]
            resp = tmp[1:-1]
            for line in resp:
                print(line)
        except KeyboardInterrupt:
            break
        except EOFError:
            break
        except BaseException as e:
            dpt.err_print(str(e))


def diagnosis_mode(dpt):
    '''
    enter diagnosis mode
    '''
    dpt.info_print('Steps to enter diagnosis mode:')
    dpt.info_print('1. Turn of DPT')
    dpt.info_print('2. Hold HOME button')
    dpt.info_print('3. Press POWER button once. Then light blinks yellow')
    dpt.info_print('4. Wait till a black square appear on the screen')
    dpt.info_print('5. Connect to computer')
    try:
        resp = input('>>> Black square on the screen? [yes/no]: ')
        if resp == 'no':
            return False
        elif not resp == 'yes':
            dpt.err_print('Unrecognized response: {}'.format(resp))
            return False
        ttyName = input('>>> Enter the serial port [/dev/tty.usbmodem01]: ')
        if ttyName == "":
            ttyName = "/dev/tty.usbmodem01"
        if not os.path.exists(ttyName):
            dpt.err_print('serial `{}` not exists!'.format(ttyName))
            return False
    except BaseException as e:
        dpt.err_print(str(e))
        return False
    if not dpt.connect_to_diagnosis(ttyName):
        return False
    diagnosis_cmd(dpt)
    dpt.shut_down_diagnosis()
    return True
