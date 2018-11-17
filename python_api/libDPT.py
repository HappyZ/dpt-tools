#!/usr/bin/python3

# built-ins
import os
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

    def diagnosis_md5sum_file(self, fp):
        '''
        get md5sum of a file
        '''
        if not self.diagnosis_isfile(fp):
            return ""
        resp = self.diagnosis_write("md5sum {}".format(fp)).splitlines()
        try:
            return resp[1].split()[0]
        except BaseException as e:
            self.err_print(str(e))
        return ""

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

    def diagnosis_backup_boot(self):
        '''
        back up boot partition to /tmp/ folder
        '''
        cmd = 'dd if=/dev/mmcblk0p8 of=/root/boot.img.bak bs=4M'
        self.diagnosis_write(cmd, timeout=999)
        if not self.diagnosis_isfile('/root/boot.img.bak'):
            self.err_print('Failed to dump boot.img.bak!')
            return ""
        return "/root/boot.img.bak"

    def diagnosis_restore_boot(self, fp="/root/boot.img.bak"):
        if not self.diagnosis_isfile(fp):
            self.err_print("{} does not exist".format(fp))
            return False
        cmd = "dd if='{}' of=/dev/mmcblk0p8 bs=4M".format(fp)
        self.info_print("Fingercrossing.. Do NOT power off device!")
        # need to be extra careful here
        resp = self.diagnosis_write(cmd, timeout=99999)
        self.info_print(resp)
        return not (resp == "")

    def diagnosis_write(self, cmd, echo=False, timeout=99):
        '''
        write cmd and read feedbacks
        '''
        if self.serial is None:
            return ""
        if 'less ' in cmd:
            self.err_print('do not support less/more')
        try:
            self.serial.flushInput()
            self.serial.flushOutput()
            self.serial.write(cmd.encode() + b'\n')
            # change timeout to (nearly) blocking first to read
            self.serial.timeout = timeout
            resp = self.serial.read_until(b'# ')
            # change back the original timeout
            self.serial.timeout = self.serialReadTimeout
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
        if echo:
            resp = resp.decode("utf-8").replace("\r\r\n", '')
        else:
            resp = resp.decode("utf-8").replace("\r\r\n", '').replace(cmd, '')
        self.dbg_print("len of {}; dbg: ".format(len(resp), resp.splitlines()))
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

    def authenticate(self, client_id_fp, key_fp, testmode=False):
        if not os.path.isfile(client_id_fp) or not os.path.isfile(key_fp):
            print(
                "! Err: did not find {0} or {1}"
                .format(client_id_fp, key_fp))
            return False

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
        signed_nonce = sig_maker._sign(nonce)

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