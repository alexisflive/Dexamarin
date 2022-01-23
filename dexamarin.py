import os
import shutil
import sys


def main(apkPath, outDirName):
    os.mkdir(outDirName)
    getApkContents(apkPath, outDirName)
        

def getApkContents(apkPath, outDirName):
    os.system('unzip {} -d {}'.format(apkPath, outDirName))

    for fname in os.listdir(outDirName):
        if fname != "assemblies":
            try:
                os.remove(os.path.join(outDirName, fname))
            except PermissionError:
                shutil.rmtree(os.path.join(outDirName, fname))

    commands = '''
    for file in {}/assemblies/*.dll; 
        do ilspycmd $file > $file.cs; mv $file.cs {}/; echo "$file decompiled"; done
    mv {}/assemblies {}/assemblies-compiled
    '''.format(outDirName, outDirName, outDirName, outDirName)
    os.system(commands)


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) != 2:
        print('DeXamarin: exactly two arguments required')
    else:
        main(args[0], args[1])