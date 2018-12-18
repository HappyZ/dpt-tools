#!/usr/bin/python3

# built-ins
import os
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


def validate_required_files(dpt, purpose='diagnosis'):
    if purpose == 'su-binary':
        requiredFiles = [
            'python_api/assets/su',
            'python_api/assets/supolicy',
            'python_api/assets/libsupol.so',
            'python_api/assets/install-recovery.sh'
        ]
    elif purpose == 'eufwupdater':
        requiredFiles = [
            'python_api/assets/start_eufwupdater.sh'
        ]
    else:
        requiredFiles = [
            'python_api/assets/shankerzhiwu_disableidcheck.pkg',
            'python_api/assets/shankerzhiwu_changepwd.pkg'
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
    fp = 'python_api/assets/shankerzhiwu_disableidcheck.pkg'
    try:
        resp = input('>>> Have you disabled the id check already? [yes/no]: ')
        if resp == 'no':
            if not dpt.update_firmware(open(fp, 'rb')):
                dpt.err_print('Failed to upload shankerzhiwu_disableidcheck pkg')
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
    fp = 'python_api/assets/shankerzhiwu_changepwd.pkg'
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
    try:
        input(
            '>>> After your DPT reboots, shows `update failure` message, ' +
            'connects back to WiFi, etc., press `Enter` key to continue')
    except BaseException as e:
        dpt.err_print(str(e))
        return False
    # step 2: reset root password
    if not reset_root_password(dpt):
        return False
    dpt.info_print(
        'You are all set! Wait till your DPT reboots and ' +
        'shows `update failure` message! More edits will be added to this tool.')
    return True


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
    `patch-updater-bash`-- patch the updater bash to bypass sig validation
    `push-file`         -- transfer file to DPT at 800bps (=100Bps)
    `pull-file`         -- transfer file from DPT
    `backup-bootimg`    -- backup the boot img and download it to local device
    `restore-bootimg`   -- restore the boot img
    `get-su-bin`        -- enable `su` (root) in adb (beta, not well tested)
    `exit`/`quit`       -- leave the tool
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


def diagnosis_patch_eufwupdater(dpt):
    '''
    patch the start_eufwupdater.sh to bypass pkg check
    '''
    if not validate_required_files(dpt, purpose='eufwupdater'):
        return False
    bashfp = diagnosis_push_file(
        dpt,
        localfp='python_api/assets/start_eufwupdater.sh',
        folder='/usr/local/bin',
        overwrite=True)
    if bashfp is None:
        dpt.err_print("Failed to patch!!")
        return False
    dpt.diagnosis_set_perm(bashfp, owner='1496.1496', perm='0775')
    dpt.info_print("Success!")
    return True


def diagnosis_backup_bootimg(dpt):
    '''
    backup boot img and then pull img from DPT to local disk
    '''
    remotefp = dpt.diagnosis_backup_boot(toSD=True)
    md5 = dpt.diagnosis_md5sum_file(remotefp)
    dpt.info_print("Success!")
    # mount mass storage to allow quick copy of backup
    dpt.diagnosis_start_mass_storage()
    dpt.info_print("Your computer shall have mounted a disk.")
    dpt.info_print("Please open that disk and copy your backup")
    dpt.info_print("`boot.img.bak` to a safe place.")
    dpt.info_print("Also, check if its MD5 is: {}.".format(md5))
    dpt.info_print("After then you can delete the file in that disk.")
    try:
        input(
            "While done, please eject the disk, " +
            "and press Enter key to continue..")
        dpt.diagnosis_stop_mass_storage()
    except KeyboardInterrupt:
        dpt.err_print("Nothing happened..")
        dpt.diagnosis_stop_mass_storage()
        return False
    # # pull this backup file to current folder
    # if remotefp:
    #     fp = diagnosis_pull_file(
    #         dpt, remotefp=remotefp, folder=".", overwrite=True
    #     )
    #     if fp is not None:
    #         dpt.info_print("Success!")
    #         return True
    # dpt.info_print("Nothing happened..")
    # return False


def diagnosis_get_su_bin(dpt):
    '''
    get sudo access in adb mode (so it would be much much eaiser to
    make changes (no painful serial data transfer)
    after doing this, adb should handle most necessary modifications
    here we use system-method (push binary files to system)
    '''
    if not validate_required_files(dpt, purpose='su-binary'):
        return False
    dpt.info_print("Mounting /system partition..")
    mountpoint = dpt.diagnosis_mount_system()
    dpt.info_print("Mounted to {}".format(mountpoint))
    if not mountpoint:
        dpt.err_print("Nothing happened..")
        return False

    dpt.info_print("Uploading su file to /system/xbin..")
    sufp = diagnosis_push_file(
        dpt,
        localfp='python_api/assets/su',
        folder='{}/xbin'.format(mountpoint),
        overwrite=True)
    if sufp is None:
        dpt.err_print("Due to previous failure, we stopped..")
        return False
    dpt.diagnosis_set_perm(sufp, owner='0.0', perm='0755')
    daemonsufp = sufp[:-2] + 'daemonsu'
    dpt.diagnosis_write('cp {0} {1}'.format(sufp, daemonsufp))
    extfolder = "{}/bin/.ext".format(mountpoint)
    dpt.diagnosis_mkdir(extfolder)
    dpt.diagnosis_set_perm(extfolder, owner='0.0', perm='0777')
    dpt.diagnosis_write('cp {0} {1}/.su'.format(sufp, extfolder))

    dpt.info_print("Uploading supolicy file to /system/xbin..")
    supolicyfp = diagnosis_push_file(
        dpt,
        localfp='python_api/assets/supolicy',
        folder='{}/xbin'.format(mountpoint),
        overwrite=True)
    if supolicyfp is None:
        dpt.err_print("Due to previous failure, we stopped..")
        return False
    dpt.diagnosis_set_perm(supolicyfp, owner='0.0', perm='0755')
    libsupolsofp = diagnosis_push_file(
        dpt,
        localfp='python_api/assets/libsupol.so',
        folder='{}/lib'.format(mountpoint),
        overwrite=True)
    if libsupolsofp is None:
        dpt.err_print("Due to previous failure, we stopped..")
        return False
    dpt.diagnosis_set_perm(libsupolsofp, owner='0.0', perm='0644')

    dpt.info_print("Uploading install-recovery.sh to /system/bin..")
    installrecfp = diagnosis_push_file(
        dpt,
        localfp='python_api/assets/install-recovery.sh',
        folder='{}/bin'.format(mountpoint),
        overwrite=True)
    if installrecfp is None:
        dpt.err_print("Due to previous failure, we stopped..")
        return False
    dpt.diagnosis_set_perm(installrecfp, owner='0.0', perm='0755')

    dpt.info_print("Tweaking /system/bin/app_process..")
    appprocessfp = '{0}/bin/app_process'.format(mountpoint)
    dpt.diagnosis_write('mv {0} {0}_bak'.format(appprocessfp))
    dpt.diagnosis_ln("/system/xbin/daemonsu", appprocessfp)

    dpt.info_print("Tweaking /system/bin/app_process32..")
    appprocess32fp = '{0}32'.format(appprocessfp)
    if dpt.diagnosis_isfile("{}_original".format(appprocess32fp)):
        dpt.diagnosis_remove_file(appprocess32fp)
    else:
        dpt.diagnosis_write("mv {0} {0}_original".format(appprocess32fp))
    dpt.diagnosis_ln("/system/xbin/daemonsu", appprocess32fp)

    dpt.info_print("Tweaking /system/bin/app_process_init..")
    if not dpt.diagnosis_isfile("{}_init".format(appprocessfp)):
        dpt.diagnosis_write(
            "cp {0}_original {1}_init".format(appprocess32fp, appprocessfp))
        dpt.diagnosis_set_perm(
            "{}_init".format(appprocessfp), owner='0.2000', perm='0755')

    dpt.info_print("Misc: add /system/etc/.installed_su_daemon")
    miscfp = "{}/etc/.installed_su_daemon".format(mountpoint)
    dpt.diagnosis_write("echo 1 > {}".format(miscfp))
    dpt.diagnosis_set_perm(miscfp, owner='0.0', perm='0644')

    dpt.info_print("Done!")


def diagnosis_restore_bootimg(dpt, usetmpfp=None, bootimgfp=None):
    '''
    restore boot img
    '''
    if usetmpfp is None:
        resp = input('> Upload boot img? [yes/no]: ')
        usetmpfp = False if resp == 'yes' else True
    # directly use the original backup, if exists
    if usetmpfp:
        dpt.info_print("Trying to use /root/boot.img.bak")
        return dpt.diagnosis_restore_boot(fp="/root/boot.img.bak")
    # otherwise we need to first upload our own boot img
    # NOTE: use mass storage instead
    dpt.diagnosis_start_mass_storage()
    dpt.info_print("Your computer shall have mounted a disk.")
    dpt.info_print("Please copy your `boot.img.bak` there.")
    try:
        input("While done, please press Enter key to continue..")
        dpt.diagnosis_stop_mass_storage()
    except KeyboardInterrupt:
        dpt.err_print("Nothing happened..")
        dpt.diagnosis_stop_mass_storage()
        return False
    # remotefp = diagnosis_push_file(dpt, folder="/tmp", overwrite=True)
    # if remotefp is not None:
    resp = input('> Confirm to continue? [yes/no]: ')
    if resp == 'yes':
        if dpt.diagnosis_restore_boot(fp="boot.img.bak", fromSD=True):
            dpt.info_print("Success!")
            return True
        dpt.err_print("Failed..")
        return False
    dpt.err_print("Nothing happened..")
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
            elif cmd =='patch-updater-bash':
                diagnosis_patch_eufwupdater(dpt)
                continue
            elif cmd == 'push-file':
                diagnosis_push_file(dpt)
                continue
            elif cmd == 'pull-file':
                diagnosis_pull_file(dpt)
                continue
            elif cmd == 'backup-bootimg':
                diagnosis_backup_bootimg(dpt)
                continue
            elif cmd == 'restore-bootimg':
                diagnosis_restore_bootimg(dpt)
                continue
            elif cmd == 'get-su-bin':
                diagnosis_get_su_bin(dpt)
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
    dpt.info_print('1. Turn off DPT')
    dpt.info_print('2. Hold HOME button')
    dpt.info_print('3. Press POWER button once. Then light blinks yellow')
    dpt.info_print('4. Release HOME button, a black square will show up')
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
    return True
