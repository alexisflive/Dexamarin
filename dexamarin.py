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
                    # else it is a special file socket, FIFO, device file (don't do anything)
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

                        if os.system('ilspycmd {} > {} 2>/dev/null'.format(ofile.name, decompiledFilePath)):
                            print('Dexamarin: there was an error decompiling {}'.format(ofile.name))
                            errorFiles.append(ofile.name)
                            os.remove(decompiledFilePath)
                        else:
                            os.remove(ofile.name)
                            shutil.move(decompiledFilePath, outDirName)
                            print('Dexamarin: {} was successfully decompiled'.format(ofile.name))

        if not os.listdir(assembliesFoldePath):
            shutil.rmtree(assembliesFoldePath)

        if errorFiles:
            print("Dexamarin: error decompiling the following files: ")
            for errorFile in errorFiles:
                print('Dexamarin: error decompiling: ' + errorFile)

        print("Dexamarin: finished decompiling the {}'s Xamarin assemblies".format(apkPath))


def decompressXalz(inFilePath, data):
        header_uncompressed_length = struct.unpack('<I', data[8:12])[0]
        payload = data[12:]

        decompressed = lz4.block.decompress(payload, uncompressed_size = header_uncompressed_length)

        with open(inFilePath, "wb") as output_file:
            output_file.write(decompressed)
            output_file.close()

        print("Dexamarin: {} was xalz decompressed".format(inFilePath))


if __name__ == "__main__":
        apkPath = sys.argv[1:][0]
        outDirName = apkPath.replace(".apk", ".assemblies")
        os.mkdir(outDirName)
        decompileAssemblies(apkPath, outDirName)