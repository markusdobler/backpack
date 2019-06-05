#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import zlib
import ctypes
import subprocess
import itertools

DESCRIPTION = 'Protect files in directories recursively with par2.'

VERSION = "0.2-rc1-mado"

# Protect files in directory recursively using par2
#
# par2 must be installed and in PATH
#   debian/ubuntu: apt-get install -y par2
#   redhat/fedora: yum install -y par2cmdline

# Redundancy percent for par2
REDUNDANCY=20

# Set to true to exclude par2 generated files (ends with .[1-9]+[0-9]*)
EXCLUDE_REPAIRED = True


# Strings:
STR_PAR2_SETUP_ERROR = 'Unable to run par2, is it installed and set in the PATH\n'

def group_files_in_clusters(files):
    label_fun = lambda f: f[:-2] + "xx"
    label_fun = lambda f: f
    files = sorted(files, key=label_fun)
    for label, grouped_files in itertools.groupby(files, label_fun):
        yield label, list(grouped_files)

def par2protect(directory,
                redundancy       = 10,
                exclude_repaired = True,
                verbose          = False,
                update           = True):
    '''
    Protect files in directory recursively using par2, detect modification with
    fast adler32 checksums
    '''

    exclude_reg = re.compile(r'(^lock)|(\.[1-9]+[0-9]*$)') # par2 repaired files end with .N, lock files start with 'lock'

    # Compute a fast ckecksum of all given files that do not start
    # with a dot
    def cksum(files):
        '''
        Compute adler32 cksum of a list of files
        '''
        val = 0
        for _fname in sorted(files):
            with open(_fname, 'rb') as _fdes:
                buf = ' '
                while len(buf) > 0:
                    buf = _fdes.read(1<<20)
                    val = zlib.adler32(buf, val)
        return ctypes.c_uint32(val).value

    with open(os.devnull, 'w') as null:

        if not verbose:
            out = null
            err = null
        else:
            out = None
            err = None

        # Walk recursively in each directory
        for root, dirs, files_in_dir in os.walk(directory):

            files_in_dir = [f for f in files_in_dir if not f[0] == '.']
            dirs[:] = sorted(d for d in dirs if not d[0] == '.')

            if exclude_repaired:
                _tmp = files_in_dir
                files_in_dir = [f for f in files_in_dir if not exclude_reg.search(f) ]
                excluded = list((set(_tmp) - set(files_in_dir)))
                if len(excluded):
                    print "par2protect: %s: excluded files:" % (root, ), \
                        ', '.join(excluded)

            if not files_in_dir:
                continue

            oldcd = os.getcwd()
            os.chdir(root)

            for (group_label, group_files) in group_files_in_clusters(files_in_dir):
                adler_filename = ".par2protect_cksum.%s" % group_label
                par2_filename = adler_filename + ".par2"
                try:
                    oval = open(adler_filename, 'rb').read(8)
                except IOError:
                    oval = ""
                nval = "%08x" % (cksum(group_files),)

                if nval != oval:
                    if oval:
                        print "par2protect: %s,%s: different adler32 checksums" % (root, group_label)

                        try:
                            subprocess.check_call(["par2", "r", par2_filename] + group_files,
                                                  stdout=out, stderr=err)
                            nval = "%08x" % (cksum(group_files),)
                        except subprocess.CalledProcessError:
                            sys.stderr.write(
                                "par2protect: %s,%s: par2 unable to repair !\n" \
                                % (root, group_label))
                        except OSError:
                            sys.stderr.write(STR_PAR2_SETUP_ERROR)
                            sys.exit(1)
                    else:
                        sys.stderr.write(
                            "par2protect: %s,%s: Not indexed before.\n" \
                            % (root, group_label))

                    try:
                        if update:
                            subprocess.check_call(["par2", "c", "-r%d" % redundancy,
                                                   par2_filename] + group_files,
                                                  stdout=out, stderr=err)
                            open(adler_filename, 'wb').write(nval)
                            print "par2protect: %s,%s: par2 and checksum updated" % (root, group_label)
                    except subprocess.CalledProcessError as cpe:
                        sys.stderr.write(
                            "par2protect: %s,%s: unable to update par2 or ckecksum\n" \
                            % (root, group_label))
                    except OSError:
                        sys.stderr.write(STR_PAR2_SETUP_ERROR)
                        sys.exit(1)

            os.chdir(oldcd)

if __name__ == '__main__':

    import sys
    import argparse

    def _main():
        '''main fucntion when called as a program look at --help output for usage'''

        parser = argparse.ArgumentParser(prog            = 'par2protect.py',
                                         formatter_class =
                                         argparse.RawDescriptionHelpFormatter,
                                         description     = DESCRIPTION,
                                         epilog='''
Copyright (c) 2014, Stany MARCEL <stanypub@gmail.com>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the <organization> nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
'''
                                     )
        parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION)
        parser.add_argument("-v", "--verbose",
                            help="increase output verbosity",
                            action="store_true")
        parser.add_argument("-r", "--redundancy",
                            help=("change the level of redundancy 1:100 (default: %d)" \
                                  % (REDUNDANCY,)),
                            metavar=('N',),
                            type=int,
                            default=REDUNDANCY)
        parser.add_argument("-n", "--no-update",
                            help="dont update par2 and checksum ",
                            action="store_true")

        parser.add_argument('DIR', nargs='+', help='directory to protect/repair')

        args = parser.parse_args()

        for _dname in args.DIR:
            if not os.path.isdir(_dname):
                parser.print_help()
                sys.exit(1)

        for _dname in args.DIR:
            par2protect(_dname,
                        redundancy = args.redundancy,
                        verbose    = args.verbose,
                        update     = not args.no_update)

        sys.exit(0)

    _main()
