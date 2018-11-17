# 0x0 Welcome

We likely have some fun stuff here!

# 0x1 Special Thanks

Greatly thank
* [shankerzhiwu and his/her friend at XDA](https://forum.xda-developers.com/general/help/idea-to-root-sonys-e-reader-dpt-rp1-t3654725/post78153143) who made the USB hack possible
* [octavianx](https://github.com/octavianx/Unpack-and-rebuild-the-DPT-RP1-upgrade-firmware) who sheds light on the hack 
* [janten](https://github.com/janten/dpt-rp1-py) who initiates the commandline tool for web APIs

# 0x2 What does DPT stand for?

[cough cough] If you don't know what's DPT you won't need this.

# 0x3 Tools

## dpt-tools.py

NOTE: Use at your own risk. I have tested this on my *MacBook*. You need `pip install httpsig pyserial` if you don't have it already. It only runs on Python 3.

This intends to be an interative shell commandline tool that wraps processes like updating firmware pkg, obtaining diagnosis access, etc.

### Prerequirement

To use the tool properly, you also need `xxd`.

### Validating successful connections

```
python dpt-tools.py -id <deviceid file path> -k <your key file path> -ip <ip address>
```

Please refer to [janten's dpt-rp1-py](https://github.com/janten/dpt-rp1-py) on how do you get `deviceid` and `key` file path for your device.

Then you will enter the interactive shell mode. Press `Ctrl + C` to exit, or type `exit` or `quit`.

### Obtaining diagnosis access

In the interactive shell, type `root`.

### Update firmware from pkg file

In the interactive shell, type `fw` and follow the instructions.


## To-Do List

### Development Roadmap

Now we can enter diagnosis mode thanks to shankerzhiwu and his/her friend, we can explore more things! The things I am interested in:
- [ ] Enabling ADB in normal Android mode
- [ ] Enabling faster file transfer in diagnosis mode (so far it takes forever to push a file)
- [ ] Allowing self-signed pkg (fw package) to flash
- [ ] Exploring system modifications
- [ ] Understand the supported apps

### Methods
- [ ] Web interface hack
- [X] USB interface hack ([shankerzhiwu and his/her friend at XDA](https://forum.xda-developers.com/general/help/idea-to-root-sonys-e-reader-dpt-rp1-t3654725/post78153143) did this! Great work!)
- [ ] ~~Build update package and flash~~ (fails as we cannot bypass pkg validation, but I can confirm the current paid hacking method can, meaning they obtained the required private key from somewhere)
- [ ] ~~Web interface testmode~~ (fails as we do not have `auth nonce` and required private key `K_PRIV_DT`)
- [ ] ~~Official app~~ (fails as the firmware updates purely rely on web interface API)

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=zhuyanzi@gmail.com&item_name=A+Cup+Of+Coffee&item_number=Thank+You&currency_code=USD)

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
