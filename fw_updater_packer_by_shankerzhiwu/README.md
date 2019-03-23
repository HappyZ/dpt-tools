This is a PKG packing script by shankerzhiwu. Post on behalf of him. Applause.

# Explanation
My PKG packing script requires DPT users to "hack" into their device in diagnosis mode, and change a few lines of the updater script to bypass the verification.

Therefore, the hacking process requires the user to actually log into the diagnosis mode.

`shankerzhiwu` took a step further (with the suggestion from `sekkit`) and made this script so DPT users do not need to go into the diagnosis mode at all, if users flash PKGs made by this script.


# How to create PKG

To make a PKG, just edit scripts in `FwUpdater` and then type `make`.

NOTE: with this script that packs a legit PKG, potentially you can do ANYTHING to any DPT system (e.g., change diagnosis password etc.). Therefore, do TEST your script before you make one and release it.

# Note

Absolutely do NOT decompile the PKG made by this script with [the tools here](https://github.com/HappyZ/dpt-tools/tree/master/fw_updater_packer_unpacker), as it may damage your system. 
