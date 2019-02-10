#!/usr/bin/python3

# built-ins
import os
import glob
import time
import serial
import base64
import httpsig
import urllib3
import requests
import argparse
from urllib.parse import quote_plus

# warning suppression
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class DPT():
    def __init__(self, addr=None, debug=False):
        '''
        Nmap scan report for <ip address>
        PORT      STATE    SERVICE
        8080/tcp  open     http-proxy
        8443/tcp  open     https-alt
        8444/tcp  open     unknown
        8445/tcp  open     unknown
        '''
        self.client_id_fp = ""
        self.key_fp = ""
        self.debug = debug
        if addr is None:
            self.addr = "digitalpaper.local"
        else:
            self.addr = addr
        self.cookies = {}
        # setup base url
        self.base_url = "https://{0}:8443".format(self.addr)
        # holder of diagnosis serial
        self.serial = None
        self.serialReadTimeout = 1  # default read timeout is 1sec
        # misc
        self.sd_tmp_mpt = "/tmp/sdtmp"
        self.sys_tmp_mpt = "/tmp/Lucifer"
        self.par_boot = "/dev/mmcblk0p8"
        self.par_system = "/dev/mmcblk0p9"
        self.par_sd = "/dev/mmcblk0p16"

    '''
    diagnosis mode related
    '''

    def connect_to_diagnosis(self, ttyName):
        '''
        connect to diagnosis
        '''
        try:
            ser = serial.Serial(ttyName, 115200, timeout=self.serialReadTimeout)
            # ser.open()
            if not ser.is_open:
                raise BaseException
            self.serial = ser
        except BaseException as e:
            self.err_print(
                "Cannot open serial port {0} due to {1}"
                .format(ttyName, str(e)))
            return False
        return True

    def diagnosis_login(self, username, password):
        '''
        login onto DPT diagnosis mode
        '''
        if self.serial is None:
            return False
        try:
            self.serial.write(b'\n')  # poke
            resp = self.serial.read(50)
            self.dbg_print(resp)
            if b'login' in resp:
                self.dbg_print('Entering username {}'.format(username))
                self.serial.write(username.encode() + b'\n')
                resp = self.serial.read(50)
                self.dbg_print(resp)
            if b'Password' in resp:
                self.dbg_print('Entering password {}'.format(password))
                self.serial.write(password.encode() + b'\n')
                resp = self.serial.read(80)
                self.dbg_print(resp)
        except serial.SerialTimeoutException as e:
            self.err_print('Timeout: {}'.format(e))
        except BaseException as e:
            self.err_print(str(e))
            return False
        if b'# ' in resp:
            return True
        return False

    def diagnosis_remove_file(self, fp):
        '''
        remove a file
        '''
        if not self.diagnosis_isfile(fp):
            return True
        resp = self.diagnosis_write("rm {}".format(fp))
        return not (resp == "")

    def diagnosis_md5sum_file(self, fp, isPartition=False):
        '''
        get md5sum of a file
        '''
        if not self.diagnosis_isfile(fp):
            return ""
        if isPartition:
            fsize = self.diagnosis_get_file_size(fp)
            cmd = "dd if={0} bs={1} count=1 | md5sum".format(fp, fsize)
            resp = self.diagnosis_write(cmd).splitlines()
        else:
            resp = self.diagnosis_write("md5sum {}".format(fp)).splitlines()
        try:
            return resp[1].split()[0]
        except BaseException as e:
            self.err_print(str(e))
        return ""

    def diagnosis_get_file_size(self, fp):
        '''
        linux to get file size
        '''
        cmd = "stat -c%%s {0}".format(fp)
        try:
            return int(self.diagnosis_write(cmd).splitlines()[1])
        except BaseException as e:
            self.err_print(str(e))
        return -1

    def diagnosis_isfile(self, fp):
        '''
        check if file exists given file path
        '''
        cmd = "[[ -f {} ]] && echo 'YESS' || echo 'NONO'".format(fp)
        return 'YESS' in self.diagnosis_write(cmd)

    def diagnosis_isfolder(self, folderp):
        '''
        check if file exists given file path
        '''
        cmd = "[[ -d {} ]] && echo 'YESS' || echo 'NONO'".format(folderp)
        return 'YESS' in self.diagnosis_write(cmd)

    def diagnosis_set_perm(self, fp, owner='0.0', perm='0777'):
        '''
        set permission of a file
        '''
        self.info_print('Set {0}: owner={1} perm={2}'.format(fp, owner, perm))
        self.diagnosis_write('chown {0} {1}'.format(owner, fp))
        self.diagnosis_write('chmod {0} {1}'.format(perm, fp))

    def diagnosis_mkdir(self, folder):
        '''
        mkdir -p folder
        '''
        if self.diagnosis_isfolder(folder):
            self.info_print("{} already exist, we are fine".format(folder))
            return True
        if not self.diagnosis_write('mkdir -p {}'.format(folder)):
            self.err_print('Failed to create folder {}'.format(folder))
            return False
        return True

    def diagnosis_ln(self, srcf, destf):
        '''
        ln -s srcfolder, targetfolder
        '''
        if not self.diagnosis_write('ln -s {0} {1}'.format(srcf, destf)):
            self.err_print('Failed to link file')
            return False
        return True

    def diagnosis_mount_system(self):
        '''
        mount system partition to self.sys_tmp_mpt
        '''
        if not self.diagnosis_mkdir(self.sys_tmp_mpt):
            return ""
        # umount first just in case
        self.diagnosis_write("umount {}".format(self.sys_tmp_mpt))
        # mount system partition (/dev/mmcblk0p9)
        self.diagnosis_write(
            "mount {0} {1}".format(self.par_system, self.sys_tmp_mpt))
        if self.diagnosis_isfolder('{}/xbin'.format(self.sys_tmp_mpt)):
            return self.sys_tmp_mpt
        return ""

    def diagnosis_mount_sd(self):
        '''
        mount mass storage to self.sd_tmp_mpt
        '''
        if not self.diagnosis_mkdir(self.sd_tmp_mpt):
            return ""
        # umount first just in case
        self.diagnosis_umount_sd()
        # mount sd partition
        resp = self.diagnosis_write(
            "mount {0} {1}".format(self.par_sd, self.sd_tmp_mpt))
        self.dbg_print(resp)
        if len(resp) > 1 and "Device or resource busy" in resp[1]:
            self.err_print(resp[1])
            return False
        return not (resp == "")

    def diagnosis_umount_sd(self):
        '''
        umount mass storage from self.sd_tmp_mpt
        '''
        resp = self.diagnosis_write("umount {}".format(self.sd_tmp_mpt))
        self.dbg_print(resp)
        return not (resp == "")

    def diagnosis_backup_boot(self, ofp="/root/boot.img.bak", toSD=False):
        '''
        back up boot partition output file path
        @param ofp: output file path
        @param toSD: if set, will copy the file to sdcard
        '''
        cmd = "dd if={0} of={1} bs=4M".format(self.par_boot, ofp)
        self.diagnosis_write(cmd, timeout=999)
        if not self.diagnosis_isfile(ofp):
            self.err_print('Failed to dump boot.img.bak!')
            return ""
        if toSD:
            if not self.diagnosis_mount_sd():
                self.err_print('Failed to copy `boot.img.bak` to mass storage!')
                self.diagnosis_umount_sd()
                return ""
            self.diagnosis_write("cp {0} {1}/".format(ofp, self.sd_tmp_mpt))
            self.diagnosis_umount_sd()
            self.info_print("Copied {} to mass storage".format(ofp))
        return ofp

    def diagnosis_restore_boot(self, fp="/root/boot.img.bak", fromSD=False):
        '''
        restore from desired boot img backup
        '''
        if fromSD:
            if not self.diagnosis_mount_sd():
                self.err_print("Failed to mount mass storage at {}".format(self.sd_tmp_mpt))
                self.diagnosis_umount_sd()
                return False
            if not self.diagnosis_isfile(fp):
                fp = "{0}/{1}".format(self.sd_tmp_mpt, fp)
        if not self.diagnosis_isfile(fp):
            self.err_print("{} does not exist".format(fp))
            return False
        md5 = self.diagnosis_md5sum_file(fp)
        self.info_print("{0} MD5: {1}".format(fp, md5))
        cmd = "dd if='{0}' of={1} bs=4M".format(fp, self.par_boot)
        self.info_print("Fingercrossing.. Do NOT touch the device!")
        # need to be extra careful here
        resp = self.diagnosis_write(cmd, timeout=99999)
        self.info_print(resp)
        if fromSD:
            self.diagnosis_umount_sd()
        return not (resp == "")

    def diagnosis_restore_system(
        self, fp="/root/system.img", fromSD=True, isSparse=True
    ):
        '''
        restore from system.img
        '''
        if fromSD:
            if not self.diagnosis_mount_sd():
                self.err_print("Failed to mount mass storage at {}".format(self.sd_tmp_mpt))
                self.diagnosis_umount_sd()
                return False
            if not self.diagnosis_isfile(fp):
                fp = "{0}/{1}".format(self.sd_tmp_mpt, fp)
        if not self.diagnosis_isfile(fp):
            self.err_print("{} does not exist".format(fp))
            return False
        md5 = self.diagnosis_md5sum_file(fp)
        self.info_print("{0} MD5: {1}".format(fp, md5))
        if isSparse:
            cmd = "extract_sparse_file '{0}' '{1}'".format(fp, self.par_system)
        else:
            cmd = "dd if='{0}' of={1} bs=4M".format(fp, self.par_system)
        self.info_print("Fingercrossing.. Do NOT touch the device!")
        # need to be extra careful here
        resp = self.diagnosis_write(cmd, timeout=99999)
        self.info_print(resp)
        if fromSD:
            self.diagnosis_umount_sd()
        return not (resp == "")

    def diagnosis_start_mass_storage(self):
        '''
        run mass_storage
        '''
        resp = self.diagnosis_write('/usr/local/bin/mass_storage &')
        self.dbg_print(resp)
        return not (resp == "")

    def diagnosis_stop_mass_storage(self):
        '''
        run mass_storage
        '''
        resp = self.diagnosis_write('busybox killall mass_storage')
        self.dbg_print(resp)
        resp = self.diagnosis_write('/usr/local/bin/mass_storage --off')
        self.dbg_print(resp)
        return not (resp == "")

    def diagnosis_write(self, cmd, echo=False, timeout=99):
        '''
        write cmd and read feedbacks
        '''
        resp = ''
        if self.serial is None:
            return resp
        if 'less ' in cmd:
            self.err_print('do not support less/more')
        try:
            self.serial.flushInput()
            self.serial.flushOutput()
            self.serial.write(cmd.encode() + b'\n')
            # change timeout to (nearly) blocking first to read
            self.serial.timeout = timeout
            tmpresp = b''
            while not '@FPX-' in resp:
                tmpresp = self.serial.read()
                resp += tmpresp.decode("utf-8")
            rest_resp = ''
            while not '# ' in rest_resp:
                tmpresp = self.serial.read()
                rest_resp += tmpresp.decode("utf-8")
            resp = (resp + rest_resp).replace("\r\r\n", '')
            # change back the original timeout
            self.serial.timeout = self.serialReadTimeout
        except KeyboardInterrupt:
            self.err_print("KeyboardInterrupt happened! Attempting to stop..")
            self.serial.write(b'\x03')
            while not '@FPX-' in resp:
                tmpresp = self.serial.read()
                resp += tmpresp.decode("utf-8")
            rest_resp = ''
            while not '# ' in rest_resp:
                tmpresp = self.serial.read()
                rest_resp += tmpresp.decode("utf-8")
            resp = (resp + rest_resp).replace("\r\r\n", '')
        except serial.SerialTimeoutException as e:
            self.err_print('Timeout: {}'.format(e))
            self.err_print("Do NOT panic. Command may be still running.")
            self.err_print("Do NOT power off the device")
            self.err_print("Quit the tool. You need manual troubleshooting:")
            self.err_print("1. See if you can get back into tty in terminal")
            self.err_print("   If not, unplug the cable and plug it back in,")
            self.err_print("   try tty again in terminal")
            self.err_print("2. Once you get in, try press `Enter` to see")
            self.err_print("   the response. It could be still running so")
            self.err_print("   nothing responded. Suggest not to kill it")
            self.err_print("3. Be patient. If it stucks for hours, then kill")
            self.err_print("   the process by pressing Ctrl + C. Depending on")
            self.err_print("   what you ran, you may or may not have troubles")
            self.err_print("4. Worst case is to flash the stock pkg, I think.")
            return ""
        except BaseException as e:
            self.err_print(str(e))
            return ""
        if not echo:
            resp = resp.replace(cmd, '')
        self.dbg_print("len of {}; dbg: {}".format(len(resp), resp.splitlines()))
        return resp


    def shut_down_diagnosis(self):
        '''
        close serial connection
        '''
        if self.serial is not None:
            try:
                self.serial.close()
            except BaseException as e:
                self.err_print('Cannot close serial port')
                return False
        return True

    '''
    Web interface related
    '''

    def run_cmd(self):
        # self._put_api_with_cookies(
        #     "/notify/login_result", data={"value": "this is a test"}
        # )
        # folder_id = self.create_folder_in_root("Test;pwd")
        # if folder_id:
        #     self.delete_folder(folder_id, force=False)
        # self._get_api_with_cookies("/folders2/c18c51bb-4323-4e9c-b874-40288e20227b")
        # self._get_testmode_auth_nonce("testmode")
        # self._get_api_with_cookies("/testmode/auth/nonce")
        pass

    def commands_need_testmode_authentication(self):
        '''
        as the doc says, we have to get nonce and K_PRIV_DT to proceed
        no luck here
        '''
        self._get_api_with_cookies("/testmode/auth/nonce")
        self._put_api_with_cookies("/testmode/launch")
        self._put_api_with_cookies("/testmode/recovery_mode")
        self._get_api_with_cookies("/testmode/assets/{path}")

    def commands_need_user_authentications(self):
        self._get_api_with_cookies("/ping", ok_code=204)
        self._put_api_with_cookies(
            "/notify/force_assigned", data={"value": ""})
        self._put_api_with_cookies(
            "/notify/login_result", data={"value": "success"})
        self._put_api_with_cookies(
            "/notify/logout_result", data={"value": "success"})
        self._get_api_with_cookies("/extensions/status")
        self._get_api_with_cookies("/extensions/status/{0}".format("{item}"))
        self._get_api_with_cookies("/extensions/configs")
        self._get_api_with_cookies("/extensions/configs/{0}".format("{item}"))

    def update_firmware(self, fwfh):
        self.info_print("fw updating in progress.. do NOT press anything..")
        filename = 'FwUpdater.pkg'
        # upload file
        response = self._put_api_with_cookies(
            '/system/controls/update_firmware/file',
            ok_code=200,
            files={'file': (quote_plus(filename), fwfh, 'rb')})
        if response.get('completed', 'no') == 'yes':
            self.dbg_print('file uploaded')
        else:
            self.err_print('failed to upload file')
            return False
        # perform precheck
        response = self._get_api_with_cookies(
            '/system/controls/update_firmware/precheck')
        battery_ok = response.get('battery', '')
        image_file_ok = response.get('image_file', '')
        if battery_ok == 'ok' and image_file_ok == 'ok':
            self.dbg_print('passed precheck')
        else:
            self.err_print(
                'precheck failed: battery {} & image_file {}'
                .format(battery_ok, image_file_ok))
            return False
        self._put_api_with_cookies('/system/controls/update_firmware')
        return True

    def delete_folder(self, folderId, force=False):
        r = self._delete_api_with_cookies(
            "/folders/{}".format(folderId), data={"force_delete_flag": force})
        if r:
            self.info_print("successful to delete")
            return True
        self.err_print("failed to delete")
        return False

    def create_folder_in_root(self, folderName):
        r = self._post_api_with_cookies(
            "/folders2", ok_code=200,
            data={"parent_folder_id": "root", "folder_name": folderName})
        if r.get("folder_id", ""):
            self.info_print(
                '{} created with id {}'
                .format(folderName, r["folder_id"]))
            return r["folder_id"]
        self.err_print("failed to create folder {}".format(folderName))
        return ""

    def get_note_templates(self):
        r = self._get_api_with_cookies("/viewer/configs/note_templates")
        return r.get('template_list', [])

    def get_serial_number(self):
        r = self._get_api_with_cookies("/register/serial_number")
        return r.get("value", "")

    def get_owner(self):
        r = self._get_api_with_cookies("/system/configs/owner")
        return r.get("value", "")

    def get_time_format(self):
        r = self._get_api_with_cookies("/system/configs/time_format")
        return r.get("value", "")

    def get_timeout_to_sleep(self):
        r = self._get_api_with_cookies("/system/configs2")
        return r.get("timeout_to_sleep", {}).get("value", "")
        # r = self._get_api_with_cookies("/system/configs/timeout_to_standby")
        # return r.get("value", "")

    def get_timezone(self):
        r = self._get_api_with_cookies("/system/configs/timezone")
        return r.get("value", "")

    def get_use_mode(self):
        r = self._get_api_with_cookies("/system/configs2")
        return r.get("use_mode", {}).get("use_mode", "")

    def get_regulation_voltage(self):
        r = self._get_api_with_cookies("/system/configs2")
        return r.get("regulation_voltage", {}).get("value", "")

    def get_pen_grip_style(self):
        r = self._get_api_with_cookies("/system/configs2")
        return r.get("pen_grip_style", {}).get("value", "")

    def get_date_format(self):
        r = self._get_api_with_cookies("/system/configs/date_format")
        return r.get("value", "")

    def get_firmware_version(self):
        r = self._get_api_with_cookies("/system/status/firmware_version")
        return r.get("value", "")

    def get_battery(self):
        r = self._get_api_with_cookies("/system/status/battery")
        return r

    def get_mac(self):
        r = self._get_api_with_cookies("/system/status/mac_address")
        return r.get("value", "")

    def get_model_name(self):
        r = self._get_api_with_cookies("/system/status/firmware_version")
        return r.get("model_name", "")

    def get_storage(self):
        r = self._get_api_with_cookies("/system/status/storage")
        return r.get("capacity", ""), r.get("available", "")

    def get_current_viewer(self):
        r = self._get_api_with_cookies("/viewer/status/current_viewing")
        orientation = r.get('orientation', '')
        view_mode = r.get('view_mode', '')
        views = r.get('views', '')
        self.dbg_print('orientation: {}'.format(orientation))
        self.dbg_print('view_mode: {}'.format(view_mode))
        self.dbg_print('views:')
        for view in views:
            self.dbg_print('* view: {0}'.format(view))
        return r

    def turn_to_page(self, page_num):
        r = self.get_current_viewer()
        if not r.get('views', []):
            self.err_print('not viewing any documents right now')
            return False
        documentId = r['views'][0]['entry_id']
        documentFp = r['views'][0]['entry_path']
        currentPg = int(r['views'][0]['current_page'])
        totalPg = int(r['views'][0]['total_page'])
        title = r['views'][0]['title']
        if page_num > totalPg:
            self.err_print('Current page only has {} pages'.format(totalPg))
            return False
        self.info_print(
            'user is reading `{}` on page {} '.format(title, currentPg) +
            '(filepath=`{}`, docid=`{}`)'.format(documentFp, documentId))
        self._put_api_with_cookies(
            "/viewer/controls/open2",
            data={"document_id": documentId, "page": page_num})
        self.info_print('page has been changed to {}'.format(page_num))
        return True

    def get_preset_marks(self):
        r = self._get_api_with_cookies("/viewer/status/preset_marks")
        return r.get('pattern_list', [])

    def get_api_version(self):
        r = self._get_api_with_cookies("/api_version")
        return r.get('value', '')

    def get_screenshot(self):
        return self._get_api(
            "/system/controls/screen_shot2", cookies=self.cookies, isfile=True)

    def get_past_logs(self):
        '''
        the logs are encrypted..
        '''
        return self._get_api(
            "/system/controls/pastlog", cookies=self.cookies, isfile=True)

    def get_client_key_fps(self):
        '''
        return the stored client key file paths
        '''
        self.dbg_print("self.client_id_fp = {}".format(self.client_id_fp))
        self.dbg_print("self.key_fp = {}".format(self.key_fp))
        return self.client_id_fp, self.key_fp

    def set_client_key_fps(self, client_id_fp, key_fp):
        '''
        store the client key file paths
        '''
        self.client_id_fp = client_id_fp
        self.key_fp = key_fp

    def auto_find_client_key_fps(self):
        '''
        automatically find the client key file paths
        inspired from https://github.com/janten/dpt-rp1-py/pull/52
        '''
        default_client_fp, default_key_fp = self.get_client_key_fps()
        if os.path.isfile(default_client_fp) and os.path.isfile(default_key_fp):
            return default_client_fp, default_key_fp
        dpa_path = "."
        # MacOS
        try:
            home_path = os.path.expanduser("~")
        except BaseException:
            return default_client_fp, default_key_fp
        tmp_dpa_path = "{}/Library/Application Support/".format(home_path)
        tmp_dpa_path += "Sony Corporation/Digital Paper App"
        if os.path.isdir(tmp_dpa_path):
            dpa_path = tmp_dpa_path
        # windows
        tmp_dpa_path = "{}/AppData/Roaming/".format(home_path)
        tmp_dpa_path += "Sony Corporation/Digital Paper App"
        if os.path.isdir(tmp_dpa_path):
            dpa_path = tmp_dpa_path
        # Linux
        tmp_dpa_path = "{}/.dpapp".format(home_path)
        if os.path.isdir(tmp_dpa_path):
            dpa_path = tmp_dpa_path
        self.dbg_print("dpa_path = {}".format(dpa_path))
        # search for desired files
        tmp_client_fp = tmp_key_fp = ''
        level3files = glob.glob(dpa_path + '/*/*/*.dat')
        level2files = glob.glob(dpa_path + '/*/*.dat')
        level1files = glob.glob(dpa_path + '/*.dat')
        for tmp_fp in level3files + level2files + level1files:
            self.dbg_print("looking at: {}".format(tmp_fp))
            if 'deviceid.dat' in tmp_fp:
                tmp_client_fp = tmp_fp
            elif 'privatekey.dat' in tmp_fp:
                tmp_key_fp = tmp_fp
        if os.path.isfile(tmp_client_fp) and os.path.isfile(tmp_key_fp):
            default_client_fp = tmp_client_fp
            default_key_fp = tmp_key_fp
        return default_client_fp, default_key_fp

    def reauthenticate(self):
        '''
        reauthentication (must done after reboot)
        '''
        return self.authenticate()

    def authenticate(self, client_id_fp="", key_fp="", testmode=False):
        '''
        authenticate is necessary to send url request
        '''
        # find client_id_fp and key_fp optional
        if not client_id_fp or not key_fp:
            client_id_fp, key_fp = self.auto_find_client_key_fps()
        if not os.path.isfile(client_id_fp) or not os.path.isfile(key_fp):
            print(
                "! Err: did not find {0} or {1}"
                .format(client_id_fp, key_fp))
            return False
        self.set_client_key_fps(client_id_fp, key_fp)

        with open(client_id_fp) as f:
            client_id = f.read().strip()

        with open(key_fp) as f:
            key = f.read().strip()

        if testmode:
            nonce = self._get_testmode_auth_nonce(client_id)
        else:
            nonce = self._get_auth_nonce(client_id)
        if not nonce:
            self.err_print("cannot get nonce")
            return False
        sig_maker = httpsig.Signer(secret=key, algorithm='rsa-sha256')
        try:
            signed_nonce = sig_maker._sign(nonce)
        except AttributeError:
            signed_nonce = sig_maker.sign(nonce)
        except BaseException as e:
            print("err:" + str(e))
            return False
        return self._put_auth(
            {"client_id": client_id, "nonce_signed": signed_nonce})

    def _put_auth(self, auth_info):
        apiurl = "{0}/auth".format(self.base_url)
        try:
            r = requests.put(apiurl, json=auth_info, verify=False)
            if r.status_code is 204:
                self.dbg_print(apiurl)
                cookietmp = r.headers.get('Set-Cookie', '')
                self.dbg_print("cookie: {}".format(cookietmp))
                _, credentials = r.headers["Set-Cookie"].split("; ")[0].split("=")
                self.cookies["Credentials"] = credentials
                self.dbg_print("self.cookies: {}".format(self.cookies))
                return True
            self.err_print(apiurl)
            try:
                self.err_request_print(r.status_code, r.json())
            except BaseException:
                self.err_print("{}, {}".format(r.status_code, r.text))
            self.err_request_print(r.status_code, r.json())
        except BaseException as e:
            self.err_print(str(e))
        return False

    def _get_auth_nonce(self, client_id):
        result = self._get_api("/auth/nonce/{0}".format(client_id))
        return result.get("nonce", "")

    def _get_testmode_auth_nonce(self, client_id):
        result = self._get_api("/testmode/auth/nonce/{0}".format(client_id))
        return result.get("nonce", "")

    def _post_api(
        self, api,
        ok_code=204, cookies=None, data={}, files={}, headers={}
    ):
        apiurl = "{0}{1}".format(self.base_url, api)
        r = requests.post(
            apiurl,
            cookies=cookies, verify=False,
            json=data, files=files, headers=headers)
        if r.status_code is ok_code:
            self.dbg_print(apiurl)
            if r.text:
                self.dbg_print(r.json())
                return r.json()
            return {}
        self.err_print(apiurl)
        try:
            self.err_request_print(r.status_code, r.json())
        except BaseException:
            self.err_print("{}, {}".format(r.status_code, r.text))
        return {}

    def _delete_api_with_cookies(self, api, ok_code=204, data={}):
        return self._delete_api(
            api, ok_code=ok_code, cookies=self.cookies, data=data)

    def _delete_api(
        self, api,
        ok_code=204, cookies=None, data={}
    ):
        apiurl = "{}{}".format(self.base_url,  api)
        r = requests.delete(
            apiurl, verify=False, cookies=self.cookies, json=data)
        if r.status_code is ok_code:
            self.dbg_print(apiurl)
            if r.text:
                self.dbg_print(r.json())
                return r.json()
            return {"status": "ok"}
        self.err_print(apiurl)
        try:
            self.err_request_print(r.status_code, r.json())
        except BaseException:
            self.err_print("{}, {}".format(r.status_code, r.text))
        return {}

    def _post_api_with_cookies(self, api, ok_code=204, data={}, files={}):
        return self._post_api(
            api, ok_code=ok_code, cookies=self.cookies, data=data, files=files)

    def _put_api(
        self, api,
        ok_code=204, cookies=None, data={}, files={}, headers={}
    ):
        apiurl = "{0}{1}".format(self.base_url, api)
        try:
            r = requests.put(
                apiurl,
                cookies=cookies, verify=False,
                json=data, files=files, headers=headers)
            if r.status_code is ok_code:
                self.dbg_print(apiurl)
                if r.text:
                    self.dbg_print(r.json())
                    return r.json()
                return {"status": "ok"}
            self.err_print(apiurl)
            try:
                self.err_request_print(r.status_code, r.json())
            except BaseException:
                self.err_print("{}, {}".format(r.status_code, r.text))
        except BaseException as e:
            self.err_print(str(e))
        return {}

    def _put_api_with_cookies(self, api, ok_code=204, data={}, files={}):
        return self._put_api(
            api, ok_code=ok_code, cookies=self.cookies, data=data, files=files)

    def _get_api(
        self, api,
        ok_code=200, cookies=None, isfile=False, headers={}
    ):
        apiurl = "{0}{1}".format(self.base_url, api)
        try:
            r = requests.get(
                apiurl,
                cookies=cookies, verify=False, headers=headers)
            if r.status_code is ok_code:
                self.dbg_print(apiurl)
                if isfile:
                    return r.content
                elif r.text:
                    self.dbg_print(r.json())
                    return r.json()
                return {"status": "ok"}
            self.err_print(apiurl)
            if r.text:
                self.err_request_print(r.status_code, r.json())
            else:
                self.err_print("status code: {0}".format(r.status_code))
                self.err_print("reason: {0}".format(r.reason))
        except BaseException as e:
            self.err_print(str(e))
        return "" if isfile else {}

    def _get_api_with_cookies(self, api, ok_code=200):
        return self._get_api(api, ok_code=ok_code, cookies=self.cookies)

    '''
    on screen print
    '''

    def err_request_print(self, status_code, msg):
        self.err_print("request error {}:".format(status_code))
        for key in msg:
            self.err_print("* {}: {}".format(key, msg[key]))

    def info_print(self, content):
        print("[info] {}".format(content))

    def err_print(self, content):
        print("[error] {}".format(content))

    def dbg_print(self, content):
        if self.debug:
            print("[debug] {}".format(content))


if __name__ == '__main__':
    p = argparse.ArgumentParser(
        description="Lib Debugging Tool")
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
    p.add_argument(
        '--firmware-update', '-fw',
        dest="dpt_fwfh",
        action='store',
        help="File path of firmware to update")

    try:
        args = vars(p.parse_args())
    except Exception as e:
        print(e)
        sys.exit()

    if args.get('debug', False):
        print(args)

    dpt = DPT(args.get('apt_addr', None), args.get('debug', False))
    if not dpt.authenticate(args.get('dpt_id', ""), args.get('dpt_key', "")):
        dpt.err_print("Cannot authenticate. Make sure your id, key, and ip addresses are correct.")
        exit(1)

    # with open('log.log', 'wb') as f:
    #     f.write(dpt.get_past_logs())
    if args['dpt_fwfh'] and os.path.isfile(args['dpt_fwfh']):
        dpt.update_firmware(open(args['dpt_fwfh'], 'rb'))
    # dpt.run_cmd()