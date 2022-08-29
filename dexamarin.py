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
        DEPENDENCIES:
        * .NET Core 3.1: https://dotnet.microsoft.com/en-us/download/dotnet/3.1
        * ilspycmd: https://github.com/icsharpcode/ILSpy/tree/master/ICSharpCode.Decompiler.Console
        * "lz4" (pip) or "python3-lz4" (Debian, Ubuntu)
        '''

import os
import shutil
import struct
import sys
import lz4.block

errorFiles = []

def decompileAssemblies(apkPath, outDirName):
        header_xalz_magic = b'XALZ'
        assembliesFoldePath = outDirName + "/assemblies"

        os.system('unzip {} -d {}'.format(apkPath, outDirName))

        for fname in os.listdir(outDirName):
            if fname != "assemblies":
                try:
                    path = os.path.join(outDirName, fname)
                    if os.path.isdir(path):
                        shutil.rmtree(os.path.join(outDirName, fname))
                    elif os.path.isfile(path):
                        os.remove(os.path.join(outDirName, fname))
                    else:
                        print("It is a special file (socket, FIFO, device file)")
                    print()
                except PermissionError:
                    shutil.rmtree(os.path.join(outDirName, fname))

        for root, dirs, files in os.walk(assembliesFoldePath):
            for file in files:
                if file.endswith('.dll'):
                    with open(root + "/" + file, "rb") as ofile:
                        data = ofile.read()
                        decompiledFilePath = ofile.name.replace(".dll", ".cs")

                        if data[:4] == header_xalz_magic:
                            decompressXalz(ofile.name, data)

                        if os.system('ilspycmd {} > {}'.format(ofile.name, decompiledFilePath)):
                            print(
                                'Dexamarin: there was an error decompiling {}'.format(ofile.name))
                            errorFiles.append(ofile.name)
                            os.remove(decompiledFilePath)
                        else:
                            os.remove(ofile.name)
                            shutil.move(decompiledFilePath, outDirName)
                            print(
                                'Dexamarin: {} was successfully decompiled'.format(ofile.name))

        if not os.listdir(assembliesFoldePath):
            shutil.rmtree(assembliesFoldePath)

        if errorFiles:
            print("Dexamarin: error decompiling the following files: ")
            for errorFile in errorFiles:
                print('Dexamarin: error decompiling: ' + errorFile)

        print("Dexamarin: finished decompiling the {}'s Xamarin assemblies".format(apkPath))

    # modified from:
    # https://raw.githubusercontent.com/x41sec/tools/master/Mobile/Xamarin/Xamarin_XALZ_decompress.py

def decompressXalz(inFilePath, data):
        header_uncompressed_length = struct.unpack('<I', data[8:12])[0]
        payload = data[12:]

        decompressed = lz4.block.decompress(
            payload, uncompressed_size=header_uncompressed_length)

        with open(inFilePath, "wb") as output_file:
            output_file.write(decompressed)
            output_file.close()

        print("Dexamarin: {} was xalz decompressed".format(inFilePath))

if __name__ == "__main__":
        apkPath = sys.argv[1:][0]
        outDirName = apkPath.replace(".apk", ".assemblies")
        os.mkdir(outDirName)
        decompileAssemblies(apkPath, outDirName)
