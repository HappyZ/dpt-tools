# 0x0 Allow your DPT to accept PKG without correct key

This will create SECURITY FLAW in your system!

Comment out the key verification: (edit via `busybox vi`)
```
########################################
# verify sig
########################################
# dd if=$1 bs=$(($DATA_OFFSET)) skip=1 2>/dev/null | head -c $(($BODY_SIZE)) |
# openssl dgst -sha256 -verify $3 -signature $SIG_FILE 1>/dev/null
# if [ $? -ne 0 ]
# then
#   echo "Verify failed."
#   exit 0
# fi
```

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

# 0x2 Re-Pack it with your own key

(as written in the bash, I use the data decryption key instead)

Pack the PKG with:
```
chmod +x unofficial_pkg_repacker_pkg.sh

./unofficial_pkg_repacker_pkg.sh <previous/output/folder/path>
```

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

* Not supporting animations yet.
