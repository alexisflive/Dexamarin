# Dexamarin

Xamarin app decompilation tool (only Android APK support for now)


## DEPENDENCIES (install these before running this tool)
* .NET Core: Download and install from **[here](https://dotnet.microsoft.com/en-us/download/dotnet)**
* [ilspycmd](https://github.com/icsharpcode/ILSpy/tree/master/ICSharpCode.ILSpyCmd): **dotnet tool install ilspycmd -g**
* other requirements: **pip install requirements.txt**

## Usage
Run either `dexamarin.py app.apk` or `dexamarin.py -s assembly.dll` for single file decompression and decompilation