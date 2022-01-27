'''
MIT License

Copyright (c) 2022 Alexis Ferreira

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

'''
# Requirements - Install the following:
* dotnet
* ilspycmd: https://github.com/icsharpcode/ILSpy/tree/master/ICSharpCode.Decompiler.Console
* "lz4" (pip) or "python3-lz4" (Debian, Ubuntu)
'''


import glob
import os
import shutil
import struct
import sys
import lz4.block

def main(apkPath, outDirName):
    os.mkdir(outDirName)
    decompileAssemblies(apkPath, outDirName)
        

def decompileAssemblies(apkPath, outDirName):
    os.system('unzip {} -d {}'.format(apkPath, outDirName))

    for fname in os.listdir(outDirName):
        if fname != "assemblies":
            try:
                os.remove(os.path.join(outDirName, fname))
            except PermissionError:
                shutil.rmtree(os.path.join(outDirName, fname))

    for root, dirs, files in os.walk(outDirName + "/assemblies"):
        for file in files:
            if file.endswith('.dll'):
                decompressXalz(root + "/" + file)

    for root, dirs, files in os.walk(outDirName + "/assemblies"):
        for file in files:
            if file.endswith('.dll'):
                decompDll = root + "/" + file
                os.system('ilspycmd {} > {}.cs'.format(decompDll, decompDll))
                print('{} decompiled'.format(decompDll))

# modified from:
# https://raw.githubusercontent.com/x41sec/tools/master/Mobile/Xamarin/Xamarin_XALZ_decompress.py
def decompressXalz(inputFilepath):
    header_xalz_magic = b'XALZ'
    
    with open(inputFilepath, "rb") as xalz_file:
        data = xalz_file.read()
    
        if data[:4] != header_xalz_magic:
            print("No XALZ decompression needed for {}".format(inputFilepath))
        else:
            header_index = data[4:8]
            header_uncompressed_length = struct.unpack('<I', data[8:12])[0]
            payload = data[12:]
            
            print("header index: %s" % header_index)
            print("compressed payload size: %s bytes" % len(payload))
            print("uncompressed length according to header: %s bytes" % header_uncompressed_length)
            
            decompressed = lz4.block.decompress(payload, uncompressed_size=header_uncompressed_length)
                    
            with open(inputFilepath + "_decomp.dll", "wb") as output_file:
                output_file.write(decompressed)
                output_file.close()

            print("result written to file")
            os.remove(inputFilepath)


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) != 2:
        print('DeXamarin: exactly two arguments required')
    else:
        main(args[0], args[1])