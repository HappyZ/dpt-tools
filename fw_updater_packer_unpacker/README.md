# Official Version

Only support unpacking since we don't have the encryption key to repack it.

Usage:
```
chmod +x official_pkg_unpacker_pkg.sh
./official_pkg_unpacker_pkg.sh <file/path/to/official/pkg> <output/folder/path>
```

# Unofficial Version

With modified diagnosis mode, it shall support unofficial pkg.

Unpacker is the same as official one, except we disabled verification.

The repacker follows a reversed procedure, but we simply use the data encryption key.

Usage:
```
chmod +x unofficial_pkg_unpacker_pkg.sh
chmod +x unofficial_pkg_repacker_pkg.sh


./unofficial_pkg_unpacker_pkg.sh <file/path/to/official/pkg> <output/folder/path>
./unofficial_pkg_repacker_pkg.sh <previous/output/folder/path>
```