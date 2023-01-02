import argparse
import os
import shutil
import struct
import lz4.block
from termcolor import colored

header_xalz_magic = b'XALZ'
errorFiles = []


def decompileAssemblies(apkPath, outDirName):
        assembliesFolderPath = outDirName + "/assemblies"

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

        # Use pyxamstore to unpack if the assemblies are inside an assemblies.blob file
        if os.path.isfile(assembliesFolderPath + "/assemblies.blob"):
            current_directory = os.getcwd()
            os.chdir(assembliesFolderPath)
            os.system("pyxamstore unpack")
            os.chdir(current_directory)
            output_folder = assembliesFolderPath + "/out"
            for root, dirs, files in os.walk(output_folder):
                for file in files:
                    src_path = os.path.join(output_folder, file)
                    dst_path = os.path.join(assembliesFolderPath, file)
                    shutil.move(src_path, dst_path)
            shutil.rmtree(output_folder)
            os.remove(assembliesFolderPath + "/assemblies.blob")
            os.remove(assembliesFolderPath + "/assemblies.json")
            os.remove(assembliesFolderPath + "/assemblies.manifest")

        # Decompress xalz compressed files
        for root, dirs, files in os.walk(assembliesFolderPath):
            for file in files:
                if file.endswith('.dll'):
                    decompressXalz(root + "/" + file)

        # Decompile .dll assemblies
        # (needs to occur in a separate loop because otherwise ilspycmd has issues opening the files)
        for root, dirs, files in os.walk(assembliesFolderPath):
            for file in files:
                if file.endswith('.dll'):
                    decompileAssembly(root + "/" + file, outDirName)

        if not os.listdir(assembliesFolderPath):
            shutil.rmtree(assembliesFolderPath)

        if errorFiles:
            print("Dexamarin: error decompiling the following files: ")
            for errorFile in errorFiles:
                print('Dexamarin: error decompiling: ' + errorFile)

        print("Dexamarin: finished decompiling the {}'s Xamarin assemblies".format(apkPath))

def decompressXalz(filePath, outFilePath=None):
    with open(filePath, "rb") as ofile:
        data = ofile.read()
        if outFilePath != None:
            decompiledFilePath = outFilePath
        else:
            decompiledFilePath = ofile.name

        if data[:4] == header_xalz_magic:
            header_uncompressed_length = struct.unpack('<I', data[8:12])[0]
            payload = data[12:]

            decompressed = lz4.block.decompress(payload, uncompressed_size = header_uncompressed_length)

            with open(decompiledFilePath, "wb") as output_file:
                output_file.write(decompressed)
                output_file.close()

            print("Dexamarin: {} was xalz decompressed".format(ofile))
            return decompiledFilePath
    
    return filePath

def decompileAssembly(assembly, outDirName=None):
    with open(assembly, "rb") as ofile:
        decompiledFilePath = ofile.name.replace(".dll", ".cs")

        if os.system('ilspycmd {} > {} 2>/dev/null'.format(ofile.name, decompiledFilePath)):
            print('Dexamarin: there was an error decompiling {}'.format(ofile.name))
            errorFiles.append(ofile.name)
            os.remove(decompiledFilePath)
        else:
            os.remove(ofile.name)
            if (outDirName != None): 
                shutil.move(decompiledFilePath, outDirName)
            print('Dexamarin: {} was successfully decompiled'.format(ofile.name))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Decompile Xamarin apps')
    parser.add_argument('file', type=str, 
                        help='the apk to decompile (or single assembly if the -s option is used)')
    parser.add_argument('-s', '--single-assembly', action='store_true', 
                        help='decompile a single assembly rather than an apk')
    args = parser.parse_args()

    srcFile = args.file
    if (args.single_assembly == False):
        outName = srcFile.replace(".apk", ".decompiled.assemblies")
        os.mkdir(outName)
        decompileAssemblies(srcFile, outName)
    else:
        decompressedName = decompressXalz(srcFile, srcFile.replace(".dll", ".decompressed.dll"))
        decompileAssembly(decompressedName, decompressedName.replace(".decompressed.dll", ".decompiled.cs"))