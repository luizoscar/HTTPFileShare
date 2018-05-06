#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
###############################################################################################'
 HttpFileShare.py

 This is a free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This file is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with the software; see the file COPYING. If not, write to the
 Free Software Foundation, Inc.,
 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

###############################################################################################'
 @class Main class, used as a HTTP file server.
 @autor: Luiz Oscar Machado Barbosa - <luizoscar@gmail.com>
##############################################################################################
'''

import getopt
import math
import os
import random
import socket
import sys
import tarfile
import zipfile
import tempfile
from threading import Thread
from datetime import datetime

try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    from gi.repository import Gtk, Gdk
except:
    pass


if sys.version_info < (3, 0):
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
else:
    from http.server import BaseHTTPRequestHandler, HTTPServer

max_downloads = 1  # Number of allowed downloads
cur_download = 0  # Current download number
src_file = None  # File to be uploaded
link_name = None  # The allowed link name
httpd = None  # HTTP Server
must_delete_after = False  # Delete the file after download


# Create custom HTTPRequestHandler class
class HTTPRequestHandler(BaseHTTPRequestHandler):

    # handle GET command
    def do_GET(self):
        global link_name, max_downloads, cur_download, must_delete_after, src_file, httpd

        if self.path.endswith(link_name):
            try:
                if max_downloads > 0:
                    print("Sending file [{0}/{1}] to {2}".format(str(cur_download + 1), max_downloads, self.client_address[0]))
                else:
                    print("Sending file to {0}".format(self.client_address[0]))
                    
                f = open(src_file, 'rb')  # open the source file

                # send code 200 response
                self.send_response(200)

                # send header first
                filename = os.path.basename(src_file)
                self.send_header('Content-type', 'application/octet-stream')
                self.send_header('Content-Disposition', 'attachment;filename={}'.format(filename))
                fs = os.fstat(f.fileno())
                self.send_header("Content-Length", str(fs[6]))
                self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
                self.end_headers()

                # send file content to client
                self.wfile.write(f.read())
                f.close()

                # Increment the number of downloads and check if reached the limit
                cur_download = cur_download + 1
                if max_downloads > 0 and cur_download == max_downloads:

                    # Disconnect the server
                    def kill_me_please(server):
                        print("Disconnecting")
                        server.shutdown()

                    # Must disconnect using a thread to avoid deadlock
                    Thread(target=kill_me_please, args=(httpd,)).start()

            except IOError:
                self.send_error(404, "File not found")
        else:
            print("Incorrect URL: {}".format(self.path))
            self.send_error(403, 'Read access forbidden')


def show_usage():
    '''
    Show the application usage
    '''

    print('Simple Python HTTP file share\n')
    print('Usage: HttpFileShare.py -f [File / Directory] -p [port] -d [Max Downloads]\n')
    print('Options:\n')
    print('    -f <File / Directory>    The path to the file or directory that will be shared (Required).')
    print('    -p <TCP Server Port>     The HTTP server TCP port (Optional, default value is 8000).')
    print('    -d <Max Downloads>       The max number of downloads allowed (Optional, default value is 1).')
    print('    -c <Archiver>            The archiver to compress the source directory (Optional, valid values are: gz, tar, zip, bzip2 or lzma).')
    sys.exit(2)


def get_line_number(line_number, file_name):
    '''
    Return the line of a text file

    @param line_number:The number of the line
    @param file_name: The file name
    '''
    with open(file_name) as f:
        for i, line in enumerate(f, 1):
            if i == line_number:
                return line


def generate_link_name():
    '''
    Generate the URL path name
    '''
    path = os.path.abspath(__file__)
    dir_path = os.path.dirname(path) + os.path.sep
    first_file = dir_path + 'first_words.txt'
    second_file = dir_path + 'second_words.txt'

    if os.path.isfile(first_file) and os.path.isfile(second_file):
        num_first = sum(1 for line in open(first_file))
        first_word = get_line_number(random.randint(0, num_first - 1), first_file)

        num_second = sum(1 for line in open(second_file))
        second_word = get_line_number(random.randint(0, num_second - 1), second_file)

        resp = first_word.strip() + "-" + second_word.strip()
    else:
        resp = datetime.now().strftime('%Y%m%d-%H%M%S')

    return resp


def to_human_size(nbytes):
    """
    Convert from bytes to SI format

    @param nbytes: The number of bytes
    """
    SIZE_UNITY = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

    human = nbytes
    rank = 0
    if nbytes != 0:
        rank = int((math.log10(nbytes)) / 3)
        rank = min(rank, len(SIZE_UNITY) - 1)
        human = nbytes / (1024.0 ** rank)
    f = ('%.2f' % human).rstrip('0').rstrip('.')
    return '%s %s' % (f, SIZE_UNITY[rank])


def compress_directory_tgz(src_file, compression, extension):
    '''
    Compress a directory to a temporary tar.gz file

    @param src_file: The source directory
    @param compression: The gzip compression (Valid values are '','gz','bz2','xz')
    @param extension: The file extension
    '''

    # Create the temp file
    filename = tempfile.gettempdir() + os.sep + os.path.basename(src_file) + extension
    if os.path.isfile(filename):
        os.remove(filename)

    print("Compressing the directory {0} to {1}".format(src_file, filename))
    # Compress the directory
    with tarfile.open(filename, "w:" + compression) as tar:
        tar.add(src_file, arcname=os.path.sep)

    # Return the temp file name
    return filename


def compress_directory_zip(src_file):
    '''
    Compress a directory to a temporary tar.gz file

    @param src_file: The source directory
    '''

    # Create the temp file
    zipname = tempfile.gettempdir() + os.sep + os.path.basename(src_file) + '.zip'
    if os.path.isfile(zipname):
        os.remove(zipname)

    print("Compressing the directory {0} to {1}".format(src_file, zipname))
    # Compress the directory
    dir_to_zip_len = len(src_file.rstrip(os.sep)) + 1
    with zipfile.ZipFile(zipname, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for dirname, subdirs, files in os.walk(src_file):
            for filename in files:
                path = os.path.join(dirname, filename)
                entry = path[dir_to_zip_len:]
                zf.write(path, entry)

    # Return the temp file name
    return zipname


def main(argv):

    global link_name, max_downloads, must_delete_after, src_file, httpd

    port = 8000  # Default server TCP Port
    archiver = 'gz'  # Compress directories to tar.gz

    try:
        opts, args = getopt.getopt(
            argv, "hp:f:d:a:", ["Port=", "From=", "Downloads=", "Archiver="])
    except getopt.GetoptError:
        show_usage()
    for opt, arg in opts:
        if opt == '-h':
            show_usage()
        elif opt in ("-p", "--Port"):
            port = int(arg)
        elif opt in ("-f", "--From"):
            src_file = arg
        elif opt in ("-d", "--Downloads"):
            max_downloads = int(arg)
        elif opt in ("-a", "--Archiver"):
            archiver = arg.lower() if not None else ''

    if not src_file:
        show_usage()

    if not os.path.isfile(src_file) and not os.path.isdir(src_file):
        print("*** Unable to locate the file / directory: {}\n".format(src_file))
        show_usage()

    if port is None:
        print("*** A HTTP port is required. Note: ports bellow 1024 may require elevate privilege access.\n")
        show_usage()

    if max_downloads is None:
        print("*** The max number of downloads is required. Default is 1 download.\n")
        show_usage()

    # Create the server, binded to all network connections
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, HTTPRequestHandler)

    # Retrieve the interface IP
    local_ip = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2]
    if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)),
    s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET,
    socket.SOCK_DGRAM)]][0][1]]) if l][0][0]

    # Generate the link name
    link_name = generate_link_name()

    # If the file is a directory, compress it
    must_delete_after = os.path.isdir(src_file)
    if must_delete_after:
        if archiver == 'gz':
            src_file = compress_directory_tgz(src_file, 'gz', '.tar.gz')
        elif archiver == 'tar':
            src_file = compress_directory_tgz(src_file, '', '.tar')
        elif archiver == 'bzip2':
            src_file = compress_directory_tgz(src_file, 'bz2', '.tar.bz2')
        elif archiver == 'lzma':
            if sys.version_info < (3, 3):
                print("*** LZMA is not supported for Python < 3.3.\n")
                sys.exit(1)
            else:
                src_file = compress_directory_tgz(src_file, 'xz', '.tar.xz')
        elif archiver == 'zip':
            src_file = compress_directory_zip(src_file)
        else:
            print("*** Invalid archiver {}.\n".format(archiver))
            show_usage()

    url = 'http://{0}:{1}/{2}'.format(local_ip, port, link_name)
    
    if max_downloads > 0:
        print('Sharing {0} times the file {1} - {2}'.format(str(max_downloads),src_file, to_human_size(os.stat(src_file).st_size)))
    else:
        print('Sharing unlimited times the file {0} - {1}'.format(src_file, to_human_size(os.stat(src_file).st_size)))
        print('NOTE: The server can be stopped by pressing CTRL+C')
        
    print('Your download link is: {}'.format(url))

    try:
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(url, -1)
        clipboard.store()
        print("The share URL was copied to the clipboard.")
    except:
        pass

    # Start to serve the files
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        # If the source was a compressed dir, the file will be deleted
        if must_delete_after:
            print("Deleting the temporary file {}".format(src_file))
            os.remove(src_file)


if __name__ == "__main__":
    main(sys.argv[1:])
