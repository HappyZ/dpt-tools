# 0x0 Welcome

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=zhuyanzi@gmail.com&item_name=A+Cup+Of+Coffee&item_number=Thank+You&currency_code=USD)

We likely have some fun stuff here! 

Note on 12/12/2018: (T_T sad news) I have soft-bricked my DPT and based on it's current stage it couldn't recover. Unfortunately, mine is out of warranty and I'm not paying over $400 more for a replacement (talked to S.O.N.Y. about this). I would appreciate some donations so I can afford the cost. But if not, it's okay, as we also get many talented others, and we got the Taobao PKGs. I'll also ask friends to look at bricked device from the hardware side. 

Things that would greatly help new comers:
- [ ] Flashsable PKGs without going into diagnosis mode (checkout the example [here](https://github.com/HappyZ/dpt-tools/tree/master/fw_updater_packer_unpacker/pkg_example))
- [ ] A clean system modification over taobao PKGs (as they have validations..)

Thanks for your understanding. Keep up the active discussions in XDA and Issues section here. Meanwhile, please all have a great Christmas!

# 0x1 Special Thanks

Greatly thank
* [shankerzhiwu and his friend at XDA](https://forum.xda-developers.com/general/help/idea-to-root-sonys-e-reader-dpt-rp1-t3654725/post78153143) who made the USB hack possible
* [octavianx](https://github.com/octavianx/Unpack-and-rebuild-the-DPT-RP1-upgrade-firmware) who sheds light on the hack 
* [janten](https://github.com/janten/dpt-rp1-py) who initiates the commandline tool for web APIs
* `silvertriclops` who points out bugs in `get-su-bin` and "forces" me to test it :D

# 0x2 What does DPT stand for?

[cough cough] If you don't know what's DPT you won't need this.

# 0x3 Tools

## dpt-tools.py - Automation to gain root, adb, and sudo access

**Heads up!** Use at your own risk. It has only been fully tested on Macbook Pro.

This is an interative shell commandline tool that wraps processes like updating firmware pkg, obtaining diagnosis access, etc.

### Prerequirement

To use the tool properly, you need:
* Python 3.x
  * `pip install httpsig pyserial`
* MacOS/Linux with support of `xxd` command (will remove this requirement soon)
  * Windows may use MinGW, some find it working, but it has not been fully tested

### At Normal Boot Up

To ***validate a successful connection***,

```
python dpt-tools.py -id <deviceid file path> -k <your key file path> -ip <ip address>
```

Please refer to [janten's dpt-rp1-py](https://github.com/janten/dpt-rp1-py) on how do you get `deviceid` and `key` file path for your device.

Then you will enter the interactive shell mode. Press `Ctrl + C` to exit, or type `exit` or `quit`.

To ***update firmware from pkg file***, type `fw` and follow the instructions.

To ***obtain diagnosis access***, type `root` and follow the instructions. 

To ***enter diagnosis mode***, type `diagnosis` and follow the instructions. Or directly use:

```
python dpt-tools.py --diagnosis
```

### At Diagnosis Mode

To ***patch updater bash***, just run `patch-updater-bash`.

To ***obtain ADB access***, we need to flash a modified `boot.img` (`boot-1.4.01.16100-mod-happyz-181118.img`). 
It is confirmed to work on RP1 version `1.4.01.16100` and on CP1 version `1.4.02.09061` (thanks to `mingming1222`).

```
### If your device is not on above versions, do NOT flash
### 1: Backup boot image: via `backup-bootimg`
###    The backup image on device is at `/root/boot.img.bak`
###    It also mounts a disk so you can copy a backup to local folder
###    Carefully confirm the MD5 of the pulled file.
###    If not correct, backup AGAIN.
### 2: Apply the new boot image: via `restore-bootimg`
###    Use `python_api/assets/boot-1.4.01.16100-mod-happyz-181118.img`
###    Carefully confirm the MD5 of the pushed file.
###    If not correct, do NOT type `yes` to restore it.
```


It may appear to be `unauthorized`. Since I did not include a vulnerable `adbd`, I put a master public key in DPT at `/adb_keys`. This causes an insecure ADB due to `/adb_keys`. TODO: remove this and add user's own keys to `/data/misc/adb/` instead.

To address `unauthorized`, on your computer (Mac or Linux), 
```
mv ~/.android/adbkey ~/.android/adbkey_bak
cp python_api/assets/adbkey ~/.android/adbkey
adb kill-server
adb devices
```

To ***obtain shell sudo access***, type `get-su-bin` and follow the instructions.

Finally, type `reboot &` and close the tool by pressing `Ctrl +C` or type `exit` or `quit`. 

If everything goes right, it will boot up. And you can run `adb devices` on your computer to see if your DPT appears.

After then, you can do `adb shell` and then type `su` to verify if you have obtained the sudo access. You can now use `adb install` to install any packages. However, it does appear that all third party apps have super small font. 

## fw_updater_packer_unpacker - Automation to pack/unpack pkg

**Note for developers: Absolutely do NOT `exit 1` while your script (in pkg) has errors.** This will create an infinite loop of "system start -> update via pkg -> shutdown -> restart -> update -> shutdown -> ...". I learned the hard way and there is no way to fix it (soft bricked).

To flash pkg with unverified signature, you need to modify the updater file at `/usr/local/bin/start_eufwupdater.sh`.

Check [this README](https://github.com/HappyZ/dpt-tools/blob/master/fw_updater_packer_unpacker/README.md) for more details.

## To-Do List

### Development Roadmap

Now we can enter diagnosis mode thanks to shankerzhiwu and his/her friend, we can explore more things! The things I am interested in:
- [x] Enabling ADB in normal Android mode
- [x] Allowing self-signed pkg (fw package) to flash
- [x] System language
- [x] Launcher modification (commandline figured)
- [ ] Third-party app font size issue fix

### Methods
- [ ] Web interface hack
- [X] USB interface hack ([shankerzhiwu and his/her friend at XDA](https://forum.xda-developers.com/general/help/idea-to-root-sonys-e-reader-dpt-rp1-t3654725/post78153143) did this! Great work!)
- [ ] ~~Build update package and flash~~ (fails as we cannot bypass pkg validation)
- [ ] ~~Web interface testmode~~ (fails as we do not have `auth nonce` and required private key `K_PRIV_DT`)
- [ ] ~~Official app~~ (fails as the firmware updates purely rely on web interface API)

# 0x4 Other tips

### Open settings via commandline

```
adb shell am start -a android.settings.SETTINGS
```

### Switch language

Only three are supported: Chinese, English, and Japanese

```
adb shell am start -a android.settings.LOCALE_SETTINGS
```

### Switch input method

```
adb shell am start -a android.settings.INPUT_METHOD_SETTINGS
```

If you saw error dialog `Unfortunately, the iWnn IME keyboard has stopped`, this is (potentially) due to the language switch that enables an extra input method. Just go in the `Keyboard & input methods` and only enable `iWnnkbd IME`.

### Launcher app

DPT Launcher is funny. It uses `ExtensionManagerService` that scans through `/etc/dp_extensions`. Ideally we shall have an automated tool to add/remove icons (not a plan), but for now, a commandline approach is the following:

Re-mount your system to be writable (requiring sudo), and then use `NoteCreator` as a template:

```
> adb shell
$ su
# mount -o rw,remount /system
# cd /etc/dp_extensions
# cp -R NoteCreator MyTemplate
# cd MyTemplate
```

Then we need to change the filenames:
```
mv NoteCreator_extension.xml MyTemplate_extension.xml
mv NoteCreator_strings-en.xml MyTemplate_strings-en.xml
mv NoteCreator_strings-ja.xml MyTemplate_strings-ja.xml
mv NoteCreator_strings-zh_CN.xml MyTemplate_strings-zh_CN.xml
mv ic_homemenu_createnote.png ic_homemenu_mytemplate.png
```

Finally, we need to edit each file (use `busybox vi file/path/filename`):
1. For MyTemplate_extension.xml (`****` is the Android app intent name, e.g., `com.android.browser/.BrowserActivity`):
```
<?xml version="1.0" encoding="utf-8"?>

<Application name="MyTemplate" type="System" version="1">
    <LauncherEntry name="MyTemplate" category="Launcher" uri="intent:#Intent;launchFlags=0x10000000;component=****;end" string="STR_ICONMENU_9999" icon="ic_homemenu_mytemplate.png" order="999"/>
</Application>
```
2. For each `****_strings-****.xml`:
```
<?xml version="1.0" encoding="utf-8"?>
<resources xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <string name="STR_ICONMENU_9999">MyTemplate</string>
</resources>
```
3. You can upload a different png for icon `ic_homemenu_mytemplate.png` (must be 220x120 size)
4. Make sure the files under `MyTemplate` are all permission `0644` (`ls -la /etc/dp_extensions/MyTemplate/*` and `chmod 0644 /etc/dp_extensions/MyTemplate/*`).
5. Remove the database (cache) from the Extension Manager and allow it to rebuid the database:
```
cd /data/system
mv ExtMgr.db ExtMgr.db_bak
mv ExtMgr.db-journal ExtMgr.db-journal_bak
```
6. Reboot

### Guide to use Taobao PKG

(FYI, I personally prefer a clean system with changes I know, over using their PKGs with unknown changes.)

Still an ongoing disucssions at [#24](https://github.com/HappyZ/dpt-tools/issues/24). Feel free to contribute if you have figured this out.


# 0xF Mission Impossible

Well, to bypass pkg validation, you can also try to decrypt the RSA key and generate corresponding private key, when we actually have enough computation resources and time to do it lol:

<pre>
> openssl rsa -pubin -in key.pub -modulus -text

Public-Key: (2048 bit)
Modulus:
    00:e0:b7:dd:45:af:91:99:14:ae:31:b8:84:38:f3:
    f1:a7:84:90:5b:9f:a3:2b:62:dd:64:26:60:d6:14:
    2d:81:e3:3d:e1:ba:96:51:10:0b:d9:b7:d3:ee:46:
    48:05:b6:f0:a6:c6:3d:2f:55:93:9e:f7:6c:15:1b:
    92:6c:c4:89:c1:c1:2f:8a:ad:7a:17:ff:08:83:d5:
    54:a8:2b:d9:25:00:41:c7:44:0c:e9:0c:d0:45:82:
    43:8a:49:63:09:8f:f3:ae:16:8c:0d:98:fe:fb:86:
    6e:95:1f:e2:b7:41:57:84:f6:98:b0:6f:76:4b:5e:
    5c:b5:2a:2a:80:12:40:91:08:da:e4:37:e0:17:5a:
    5b:46:16:0a:d8:c4:74:dc:0e:d7:bf:f0:a3:d4:d9:
    48:db:0b:46:27:79:4a:c2:48:8b:5a:61:18:37:8d:
    15:b0:bf:c9:64:6d:59:6f:6a:b9:6a:07:84:4a:01:
    f3:1d:8a:39:34:89:cd:67:6a:af:5c:ba:37:55:87:
    cc:be:60:f5:ec:a5:5a:c5:f6:21:48:9e:a6:e2:5c:
    a7:63:74:8b:dd:f8:cf:f8:0a:af:19:8e:ae:ec:a0:
    7c:44:27:c5:54:66:57:71:8d:59:d0:3d:51:e5:f5:
    ca:b0:89:a3:1a:4d:fe:ae:e1:65:30:90:b4:d6:1b:
    bd:29
Exponent: 65537 (0x10001)
Modulus=E0B7DD45AF919914AE31B88438F3F1A784905B9FA32B62DD642660D6142D81E33DE1BA9651100BD9B7D3EE464805B6F0A6C63D2F55939EF76C151B926CC489C1C12F8AAD7A17FF0883D554A82BD9250041C7440CE90CD04582438A4963098FF3AE168C0D98FEFB866E951FE2B7415784F698B06F764B5E5CB52A2A8012409108DAE437E0175A5B46160AD8C474DC0ED7BFF0A3D4D948DB0B4627794AC2488B5A6118378D15B0BFC9646D596F6AB96A07844A01F31D8A393489CD676AAF5CBA375587CCBE60F5ECA55AC5F621489EA6E25CA763748BDDF8CFF80AAF198EAEECA07C4427C5546657718D59D03D51E5F5CAB089A31A4DFEAEE1653090B4D61BBD29
</pre>
