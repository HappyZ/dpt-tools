This doc assumes to be a MacOS. Linux may have GNU commands that differ from the BSD ones. 

# 0x0 Allow your DPT to accept PKG without correct key

This will create SECURITY FLAW in your system! Use PKG [here](https://github.com/HappyZ/dpt-tools/blob/master/fw_updater_packer_by_shankerzhiwu/pkg_example/hack_basics/fw.pkg).

Note: you will still be able to flash the official PKG afterwards.

Windows users: do NOT try to edit the update script with your notepad, as it will alternate the newline `\n` into `\r\n` which halts the system and brick the system!

# 0x1 Create your own PKG package

## Use Official PKGs as Examples

An easy approach is to use the official pkg to begin with. Once you have downloaded the official pkg, use `official_pkg_unpacker_pkg.sh` to unpack it.

Usage:
```
chmod +x official_pkg_unpacker_pkg.sh
./official_pkg_unpacker_pkg.sh <file/path/to/official/pkg> <output/folder/path>
```

Then you can change the bash and let it run "anything" (as long as supported in diagnosis mode) during the update.

## Tips

* In the bash, `exit 0` means it will reboot, while `exit 1` or any error status will shut down the system.
* Double check your commands. Try them first in diagnosis mode.
* Absolutely do NOT `exit 1` while your script has errors. This will create an infinite loop of "system start -> update via pkg -> shutdown -> restart -> update -> shutdown -> ...". I learned the hard way and there is no way to fix it (soft bricked).

# 0x2 Re-Pack it with your own key

(as written in the bash, I use the data decryption key instead)

Pack the PKG with:
```
chmod +x unofficial_pkg_repacker_pkg.sh

./unofficial_pkg_repacker_pkg.sh <previous/output/folder/path>
```

Note that `chkver.sh` and `verify.sh` will check the validity of the pkg also (via version number etc.). So only modify things if you really know what is going on. You need to remove the version check. And you need to better not touch `rawdata` (remove that line or related) if you do not know what it does. 

# 0x3 Validate the package


Easy validation by unpacking it again:
```
chmod +x unofficial_pkg_unpacker_pkg.sh

./unofficial_pkg_unpacker_pkg.sh <file/path/to/official/pkg> <new/output/folder/path>
```

If succeeded, the package PKG will be recognized by the DPT system.


# 0x4 Flash it

You can use `dpt-tools.py` to update the firmware you made:

```
python dpt-tools.py -id <deviceid file path> -k <your key file path> -ip <ip address>
```
Then type `fw` and follow the instruction.


# Known Issues

* After reboot, it will appear errors saying update failed. But PKG is actually applied.

# Examples

Check out [these examples](https://github.com/HappyZ/dpt-tools/tree/master/fw_updater_packer_unpacker/pkg_example/)
