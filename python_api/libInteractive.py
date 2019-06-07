#!/usr/bin/python3

# built-ins
import os
import sys
import time
import subprocess


'''
Web Interface API Related
'''

def update_firmware(dpt):
    '''
    update firmware interface
    '''
    dpt.info_print(
        'Please make sure you have charged your battery before this action.')
    try:
        resp = input('>>> Please enter the pkg file path: ')
        while resp[-1] == ' ':  # remove extra spaces
            resp = resp[:-1]
        if not os.path.isfile(resp):
            dpt.err_print('File `{}` does not exist!'.format(resp))
            return False
        resp2 = input(
            '>>> Pleae confirm {} is the pkg file to use [yes/no]: '
            .format(resp)
        )
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


'''
Diagnosis Related
'''


def print_diagnosis_info():
    print("""============================
 DPT Tools - Diagnosis Mode
============================
This is diagnosis mode. Type `help` to show this message.
It behaves similarly to regular serial session with less flexibility (cannot use tab, scroll up, quick reverse search, etc.).
This mode intends to automate some complicated procedures.

Supported commands:
    `push-file`             -- devlop usage only, transfer file to DPT at 800bps (=100Bps)
    `pull-file`             -- devlop usage only, transfer file from DPT
    `restore-boot-img`      -- restore the boot img (use `boot.img`)
    `restore-system-img`    -- restore the system img (use `system.img`)
    `install-pkg`           -- mount mass storage and put in pkg (`FwUpdater.pkg`) to install
    `reboot`                -- get out of diagnosis mode and reboot into normal system
    `exit`/`quit`           -- leave the tool
    and many unix cmds (do not support less/head)
""")


def diagnosis_pull_file(
    dpt, remotefp=None, folder=None, overwrite=None
):
    '''
    pull file from device to local via xxd and parsing in 
    python
    do NOT pull large file using this, it will take forever
    to finish..
    '''
    try:
        # get and validate remote file path
        if remotefp is None:
            remotefp = input('> DPT file path: ')
        if not dpt.diagnosis_isfile(remotefp):
            dpt.err_print('File {} does not exist!'.format(remotefp))
            return None
        # get local folder path
        if folder is None:
            folder = input('> Local folder path: ')
            if not os.path.isdir(folder):
                resp = input(
                    '> {} not exist, create? [yes/no]: '.format(folder))
                if resp == 'no':
                    return None
                elif resp == 'yes':
                    os.makedirs(folder)
                else:
                    dpt.err_print('Unrecognized input {}'.format(resp))
                    return None
        # check if local fp exists
        localfp = "{0}/{1}".format(folder, os.path.basename(remotefp))
        if overwrite is None:
            overwrite = True
            if os.path.isfile(localfp):
                resp = input(
                    '> {} exist, overwrite? [yes/no]: '.format(localfp))
                overwrite = True if resp == 'yes' else False
        # get md5
        md5 = dpt.diagnosis_md5sum_file(remotefp)
        # start
        dpt.info_print("Pulling file {}, plz be patient...".format(localfp))
        if overwrite:
            # read from hexdump, parse, and write to local file
            startTime = int(time.time() * 1000)
            offset = 0
            count = 2
            with open("{}.tmp".format(localfp), 'w') as f:
                while 1:
                    # split file
                    cmd = (
                        "dd if={0} skip={1} ".format(remotefp, offset) +
                        "count={0} of=/tmp/sparse.tmp".format(count)
                    )
                    if not dpt.diagnosis_write(cmd):
                        break
                    # cat to download
                    cmd = (
                        "cat /tmp/sparse.tmp | " +
                        "hexdump -ve '32/1 \"%02X\" \"\\n\"'"
                    )
                    resp = dpt.diagnosis_write(cmd, timeout=99).splitlines()
                    if len(resp[1:-1]) > 0:
                        for each in resp[1:-1]:
                            f.write(each)
                    else:
                        break
                    offset += count
                    if offset % 100 == 0:
                        dpt.info_print("Copying.. at block {}".format(offset))
            # use xxd to convert back to binary file
            subprocess.call('xxd -r -p {0}.tmp > {0}'.format(localfp), shell=True)
            duration = int(time.time() * 1000) - startTime
            dpt.info_print('Finished in {0:.2f}sec'.format(duration / 1000.0))
            if os.path.isfile(localfp):
                dpt.info_print("File pulled to: {}".format(localfp))
                dpt.info_print("Please verify if it's MD5 is {}".format(md5))
                os.remove("{}.tmp".format(localfp))
                return localfp
    except BaseException as e:
        dpt.err_print(str(e))
    dpt.err_print("Failed to pull file {}".format(remotefp))
    return None


def diagnosis_push_file(
    dpt, chunkSize=200, localfp=None, folder=None, overwrite=None
):
    '''
    push file from local to device through echo in diagnosis
    (serial) mode
    using echo is dumb and slow but very reliable
    limited to 200 bytes per cmd or below, since we send raw bytes
    in string (each byte sent = 4 bytes), and terminal at best
    allows 1024 bytes to send
    do NOT push large file using this, it will take
    forever to finish..
    as a reference: push a 11.2MB file costs you roughly 22min
    '''
    try:
        # get local file path
        if localfp is None:
            localfp = input('> Local file path: ')
            while localfp[-1] == ' ':  # remove extra spaces
                localfp = localfp[:-1]
        if not os.path.isfile(localfp):
            dpt.err_print('File {} does not exist!'.format(localfp))
            return None
        # get remote folder and validate it
        if folder is None:
            folder = input('> DPT folder path: ')
            # folder does not exit, create one?
            if not dpt.diagnosis_isfolder(folder):
                resp = input('> {} not exist, create? [yes/no]: '.format(folder))
                if resp == 'no':
                    return None
                elif resp == 'yes':
                    dpt.diagnosis_write('mkdir -p {}'.format(folder))
                else:
                    dpt.err_print('Unrecognized input {}'.format(resp))
                    return None
        # remote file exists, overwrite it?
        remotefp = "{0}/{1}".format(folder, os.path.basename(localfp))
        # check if the file path is too long
        if len(remotefp) > 160:
            dpt.err_print(
                "DPT file path `{}` is beyond 160 chars!".format(remotefp))
            return None
        if overwrite is None:
            overwrite = True
            if dpt.diagnosis_isfile(remotefp):
                resp = input(
                    '> {} exist, overwrite? [yes/no]: '.format(remotefp))
                overwrite = True if resp == 'yes' else False
        if overwrite:
            # write through echo
            firstRun = True
            symbol = '>'
            startTime = int(time.time() * 1000)
            totalChunks = 0
            dpt.info_print("total chunks to transfer: {:.2f}"
                           .format(os.path.getsize(localfp) / chunkSize))
            with open(localfp, 'rb') as f:
                while 1:
                    chunk = f.read(chunkSize)
                    if chunk:
                        cmd = "echo -e -n '\\x{0}' {1} {2}".format(
                            '\\x'.join('{:02x}'.format(x) for x in chunk),
                            symbol,
                            remotefp
                        )
                        if dpt.diagnosis_write(cmd) == "":
                            raise BaseException
                    else:
                        break
                    if firstRun:
                        symbol = '>>'
                        firstRun = False
                    totalChunks += 1
                    if totalChunks % 100 == 0:
                        dpt.info_print(
                            "Copying.. at chuck {}".format(totalChunks))
            duration = int(time.time() * 1000) - startTime
            dpt.info_print('Finished in {0:.2f}sec'.format(duration / 1000.0))
            if dpt.diagnosis_isfile(remotefp):
                md5 = dpt.diagnosis_md5sum_file(remotefp)
                dpt.info_print("File pushed to: {}".format(remotefp))
                dpt.info_print("It's MD5 is: {}".format(md5))
                return remotefp
    except BaseException as e:
        dpt.err_print(str(e))
    return None


def diagnosis_restore_systemimg(dpt):
    '''
    restore system img
    '''
    dpt.diagnosis_start_mass_storage()
    dpt.info_print("Your computer shall have mounted a disk.")
    dpt.info_print("Please copy your `system.img` there.")
    try:
        input("When done, plz eject disk and press Enter to continue..")
        dpt.diagnosis_stop_mass_storage()
    except KeyboardInterrupt:
        dpt.err_print("Nothing happened..")
        dpt.diagnosis_stop_mass_storage()
        return False
    try:
        resp = input('> Is it a sparse image (from official PKG)? [yes/no]: ')
        isSparse = (resp == 'yes')
        resp = input('> Confirm to continue? [yes/no]: ')
    except KeyboardInterrupt:
        dpt.err_print("Nothing happened..")
        return False
    if resp == 'yes':
        if dpt.diagnosis_restore_system(fp="system.img", isSparse=isSparse):
            dpt.info_print("Success!")
            return True
        dpt.err_print("Failed..")
        return False
    dpt.err_print("Nothing happened..")
    return False


def diagnosis_restore_bootimg(dpt, bootimgfp=None):
    '''
    restore boot img
    '''
    dpt.diagnosis_start_mass_storage()
    dpt.info_print("Your computer shall have mounted a disk.")
    dpt.info_print("Please copy your `boot.img` there.")
    try:
        input("When done, plz eject disk and press Enter to continue..")
        dpt.diagnosis_stop_mass_storage()
    except KeyboardInterrupt:
        dpt.err_print("Nothing happened..")
        dpt.diagnosis_stop_mass_storage()
        return False
    # remotefp = diagnosis_push_file(dpt, folder="/tmp", overwrite=True)
    # if remotefp is not None:
    try:
        resp = input('> Confirm to continue? [yes/no]: ')
    except KeyboardInterrupt:
        dpt.err_print("Nothing happened..")
        return False
    if resp == 'yes':
        if dpt.diagnosis_restore_boot(fp="boot.img", fromSD=True):
            dpt.info_print("Success!")
            return True
        dpt.err_print("Failed..")
        return False
    dpt.err_print("Nothing happened..")
    return False


def diagnosis_restore_pkg(dpt):
    '''
    install/restore from an uploaded pkg in diagnosis mode
    '''
    dpt.diagnosis_start_mass_storage()
    dpt.info_print("Your computer shall have mounted a disk.")
    dpt.info_print("Please copy your `FwUpdater.pkg` there.")
    try:
        input("When done, plz eject disk and press Enter to continue..")
        dpt.diagnosis_stop_mass_storage()
    except KeyboardInterrupt:
        dpt.diagnosis_stop_mass_storage()
        return False
    dpt.info_print("We will now reboot the device to install PKG")
    dpt.info_print("")
    dpt.info_print("Hold the HOME button while rebooting")
    dpt.info_print("Wait till lights turning off and start flashing yellow,")
    dpt.info_print("then release the button and enjoy a cup of coffee")
    dpt.info_print("")
    dpt.info_print("If you changed your mind before the third bar appears,")
    dpt.info_print("press the POWER button during the reboot,")
    dpt.info_print("it will skip the PKG update and go to normal system")
    dpt.info_print("")
    dpt.info_print("You can also instead press the HOME button during the reboot,")
    dpt.info_print("it will go back into diagnosis mode")
    input("Ready? Press Enter to continue..")
    dpt.info_print("System rebooting..")
    dpt.diagnosis_write("reboot &")
    return True


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
            elif cmd == 'restore-boot-img':
                diagnosis_restore_bootimg(dpt)
                continue
            elif cmd == 'restore-system-img':
                diagnosis_restore_systemimg(dpt)
                continue
            elif cmd == 'install-pkg':
                diagnosis_restore_pkg(dpt)
                dpt.info_print("due to the reboot, exiting the tool..")
                dpt.shut_down_diagnosis()
                raise EOFError
            elif cmd == 'reboot':
                dpt.info_print("due to the reboot, exiting the tool..")
                dpt.diagnosis_write('reboot &')
                dpt.shut_down_diagnosis()
                raise EOFError
            rawresp = dpt.diagnosis_write(cmd)
            # ignore first and last echos
            tmp = rawresp.splitlines()
            frontLine = tmp[-1]
            resp = tmp[1:-1]
            for line in resp:
                print(line)
        except KeyboardInterrupt:
            dpt.info_print("\nPress Ctrl + D to exit")
            continue
        except EOFError:
            break
        except BaseException as e:
            dpt.err_print(str(e))


def diagnosis_mode(dpt):
    '''
    enter diagnosis mode
    '''
    dpt.info_print('Steps to enter diagnosis mode:')
    dpt.info_print('1. Turn off DPT')
    dpt.info_print('2. Hold HOME button')
    dpt.info_print('3. Press POWER button once. Then light blinks yellow')
    dpt.info_print('4. Release HOME button, a black square will show up')
    dpt.info_print('5. Connect to computer')
    dpt.info_print('6. (Windows) After step 5 you can use device manager to find which COM port DPT is connected to. E.g. COM5')
    dpt.info_print('Notice that if your DPT is in diagnosis mode, you can exit it by pressing the reset button.')
    dpt.info_print('If this program exits, and your DPT is still in diagnosis mode,')
    dpt.info_print('you get here again by starting with parameter --diagnosis')
    dpt.info_print('It is also possible to interact with diagnosis mode with a serial terminal, such as putty.')
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
        # disable file check here since Windows is different
        # if not os.path.exists(ttyName):
        #     dpt.err_print('serial `{}` not exists!'.format(ttyName))
        #     return False
    except BaseException as e:
        dpt.err_print(str(e))
        return False
    if not dpt.connect_to_diagnosis(ttyName):
        return False
    diagnosis_cmd(dpt)
    dpt.shut_down_diagnosis()
    dpt.info_print("got out of diagnosis")
    return True
