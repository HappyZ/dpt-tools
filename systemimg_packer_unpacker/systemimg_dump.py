#! /usr/bin/env python

#
# Copyright (C) 2014 Anestis Bechtsoudis
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Unpacker for system.img from DPT pkg
# HappyZ
# Thanks to android-simg2img for providing the tool
# Thanks to anonymous contributer somewhere on earth

# SYSTEM.IMG FILE FORMAT
# It is slightly different from traditional Android sparse file
# It has extra 4 bytes paddings after chunk type


from __future__ import print_function
import binascii
import csv
import getopt
import hashlib
import posixpath
import signal
import struct
import sys


def usage(argv0):
    print("""
Usage: %s [-v] [-s] [-c <filename>] sparse_image_file ...
 -v             verbose output
 -s             show sha1sum of data blocks
 -c <filename>  save .csv file of blocks
""" % (argv0))
    sys.exit(2)


def main():
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    me = posixpath.basename(sys.argv[0])

    # Parse the command line
    verbose = 0                   # -v
    showhash = 0                  # -s
    csvfilename = None            # -c
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], "vsc:", ["verbose", "showhash", "csvfile"]
        )
    except getopt.GetoptError as e:
        print(e)
        usage(me)
    for o, a in opts:
        if o in ("-v", "--verbose"):
            verbose += 1
        elif o in ("-s", "--showhash"):
            showhash = True
        elif o in ("-c", "--csvfile"):
            csvfilename = a
        else:
            print("Unrecognized option \"%s\"" % (o))
            usage(me)

    if not args:
        print("No sparse_image_file specified")
        usage(me)

    if csvfilename:
        csvfile = open(csvfilename, "wb")
        csvwriter = csv.writer(csvfile)

    output = verbose or csvfilename or showhash

    for path in args:
        FH = open(path, "rb")
        header_bin = FH.read(28)
        header = struct.unpack("<I4H4I", header_bin)

        magic = header[0]
        major_version = header[1]
        minor_version = header[2]
        file_hdr_sz = header[3]
        chunk_hdr_sz = header[4]
        blk_sz = header[5]
        total_blks = header[6]
        total_chunks = header[7]
        image_checksum = header[8]

        if magic != 0xED26FF3A:
            print(
                "{0}: {1}: Magic should be 0xED26FF3A but is {2:08X}"
                .format(me, path, magic)
            )
            continue
        if major_version != 1 or minor_version != 0:
            print(
                "{0}: {1}: I only know about version 1.0, ".format(me, path) +
                "but this is version {0}.{1}"
                .format(major_version, minor_version)
            )
            continue
        if file_hdr_sz < 28:
            print(
                "{0}: {1}: The file header size was".format(me, path) +
                "expected at least 28, but is {2}.".format(file_hdr_sz)
            )
            continue
        if chunk_hdr_sz < 12:
            print(
                "{0}: {1}: The chunk header size was".format(me, path) +
                "expected at least 12, but is {2}.".format(chunk_hdr_sz)
            )
            continue

        print(
            "{0}: Total of {1} {2}-byte output blocks in {3} input chunks."
            .format(path, total_blks, blk_sz, total_chunks)
        )

        print("checksum={0:08X}".format(image_checksum))

        if file_hdr_sz > 28:
            header_extra = FH.read(file_hdr_sz - 28)
            print(
                "{0}: Header extra bytes: {1}"
                .format(me, binascii.hexlify(header_extra))
            )

        if not output:
            continue

        if verbose > 0:
            print("            input_bytes      output_blocks")
            print("chunk    offset     number  offset  number")

        if csvfilename:
            csvwriter.writerow(["chunk", "input offset", "input bytes",
                                "output offset", "output blocks", "type",
                                "hash"])

        offset = 0
        for i in xrange(1, total_chunks + 1):
            header_bin = FH.read(16)
            header = struct.unpack("<4I", header_bin)
            chunk_type = header[0]
            chunk_sz = header[2]
            total_sz = header[3]
            data_sz = total_sz - chunk_hdr_sz
            curhash = ""
            curtype = ""

            if chunk_hdr_sz > 16:
                header_extra = FH.read(chunk_hdr_sz - 16)
            curpos = FH.tell()
            if verbose > 0:
                print(
                    "%4u %10u %10u %7u %7u" %
                    (i, curpos, data_sz, offset, chunk_sz),
                    end=" "
                )
                if chunk_hdr_sz > 12:
                    print(
                        "[Extra bytes: %s]" %
                        (binascii.hexlify(header_extra)),
                        end=" "
                    )

            if chunk_type == 0xCAC1:
                if data_sz != (chunk_sz * blk_sz):
                    print(
                        "Raw chunk input size ({0}) ".format(data_sz) +
                        "does not match output size " +
                        "({0})".format(chunk_sz * blk_sz)
                    )
                    break
                else:
                    curtype = "Raw data"
                    data = FH.read(data_sz)
                    if showhash:
                        h = hashlib.sha1()
                        h.update(data)
                        curhash = h.hexdigest()
            elif chunk_type == 0xCAC2:
                if data_sz != 4:
                    print(
                        "Fill chunk should have 4 bytes of fill, " +
                        "but this has {0}".format(data_sz)
                    )
                    break
                else:
                    fill_bin = FH.read(4)
                    fill = struct.unpack("<I", fill_bin)
                    curtype = format("Fill with 0x%08X" % (fill))
                    if showhash:
                        h = hashlib.sha1()
                        data = fill_bin * (blk_sz / 4)
                        for block in xrange(chunk_sz):
                            h.update(data)
                        curhash = h.hexdigest()
            elif chunk_type == 0xCAC3:
                if data_sz != 0:
                    print(
                        "Don't care chunk input size is " +
                        "non-zero ({0})".format(data_sz))
                    break
                else:
                    curtype = "Don't care"
            elif chunk_type == 0xCAC4:
                if data_sz != 4:
                    print(
                        "CRC32 chunk should have 4 bytes of CRC, " +
                        "but this has {0}".format(data_sz)
                    )
                    break
                else:
                    crc_bin = FH.read(4)
                    crc = struct.unpack("<I", crc_bin)
                    curtype = format("Unverified CRC32 0x%08X" % (crc))
            else:
                print("Unknown chunk type 0x%04X" % (chunk_type))
                break

            if verbose > 0:
                print("%-18s" % (curtype), end=" ")

                if verbose > 1:
                    header = struct.unpack("<12B", header_bin)
                    print(
                        " (" +
                        "%02X%02X %02X%02X %02X%02X%02X%02X %02X%02X%02X%02X" %
                        (header[0], header[1], header[2], header[3],
                         header[4], header[5], header[6], header[7],
                         header[8], header[9], header[10], header[11]) +
                        ")",
                        end=" "
                    )

                print(curhash)

            if csvfilename:
                csvwriter.writerow([i, curpos, data_sz, offset,
                                    chunk_sz, curtype, curhash])

            offset += chunk_sz

        if verbose > 0:
            print("     %10u            %7u         End" % (FH.tell(), offset))

        if total_blks != offset:
            print(
                "The header said we should have " +
                "{0} output blocks, but we saw {1}".format(total_blks, offset)
            )

        junk_len = len(FH.read())
        if junk_len:
            print(
                "There were {0} bytes of extra data at the end of the file."
                .format(junk_len)
            )

    if csvfilename:
        csvfile.close()

    sys.exit(0)

# Python 3 shim
try:
        xrange
except NameError:
        xrange = range

if __name__ == "__main__":
    main()
