# gotcha-afs-tool
An unpacker and repacker of Gotcha Force's AFS format (tested on GameCube version).

Requires a recent version of Python 3. On Windows, remember to enable "Add Python to Path" in the installer.
A .bat file is included onto which you can drag and drop an .afs or folder to unpack or repack the file/folder.

Command line usage:
```
usage: afs_tool.py [-h] [--padding PADDING] input [output]

positional arguments:
  input              Path to AFS file to be unpacked or folder to be packed.
  output             Output path of extracted folder or new AFS.

optional arguments:
  -h, --help         show this help message and exit
  --padding PADDING  Data padding, must be a power of 2. Default is 2048.```
