import struct
import os 
import time 
import datetime
from io import BytesIO

def read_uint32(f):
    return struct.unpack("I", f.read(4))[0]

def write_uint32(f, val):
    f.write(struct.pack("I", val))


def write_pad2048(f):
    next_aligned_pos = (f.tell() + 2047) & ~2047

    f.write(b"\x00"*(next_aligned_pos - f.tell()))
    
class Date(object):
    def __init__(self):
        self.datetime = datetime.datetime(year=1970, month=1, day=1)
    
    @classmethod
    def from_file(cls, f):
        date = cls()
        year, month, day, hour, minute, second = struct.unpack("HHHHHH", f.read(12))
        
        date.datetime = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
        return date
    
    def __str__(self):
        return str(self.datetime)
        
        
class FileEntry(object):
    def __init__(self):
        self._offset = 0
        self._size = 0
        self.name = ""
        self.date = Date()
        self.data = BytesIO()
    
    @classmethod
    def from_entry_table(cls, f):
        offset = read_uint32(f)
        size = read_uint32(f)
        
        entry = cls()
        entry._offset = offset 
        entry._size = size 
        return entry 


class GotchaAFS(object):
    def __init__(self):
        self.entries = []
        self._fileinfo_offset = 0x80000-8  #offset to the file info offset 
    
    @classmethod
    def from_file(cls, f):
        archive = cls()
        
        magic = f.read(4)
        assert magic == b"AFS\x00"
        filecount = read_uint32(f)
        
        for i in range(filecount):  
            entry = FileEntry.from_entry_table(f)
            archive.entries.append(entry)
            
        for entry in archive.entries:
            #print(hex(entry._offset))
            f.seek(entry._offset)
            entry.data.write(f.read(entry._size))
            entry.data.seek(0)
        
        f.seek(archive._fileinfo_offset)
        fileinfo_offset = read_uint32(f)
        fileinfo_size = read_uint32(f)
        
        if fileinfo_offset != 0:
            f.seek(fileinfo_offset)
            for entry in archive.entries:
                entry.name = f.read(32).strip(b"\x00").decode("ascii")
                entry.date = Date.from_file(f)
                filelength = read_uint32(f)
                
                assert filelength == entry._size
        else:
            print("file info not found, skipping")
        
        return archive 
    
    @classmethod
    def from_folder(cls, path):
        archive = cls()
        
        with open(os.path.join(path, "__FILE_LISTING.txt"), "r") as f:
            for i, line in enumerate(f):
                entry = FileEntry()
                
                line = line.strip()
                filename, timestamp = line.split(";;")
                filename = filename.strip()
                
                entry.name = filename
                
                timestamp = timestamp.split(" ")
                
                if len(timestamp) != 6:
                    raise RuntimeError("Malformed timestamp on line {0}.".format(i+1))
                
                filedate = datetime.datetime(
                    year=int(timestamp[0]),
                    month=int(timestamp[1]),
                    day=int(timestamp[2]),
                    hour=int(timestamp[3]),
                    minute=int(timestamp[4]),
                    second=int(timestamp[5])
                )
                
                entry.date.datetime = filedate
                
                with open(os.path.join(path, filename), "rb") as g:
                    data = g.read()
                    entry.data.write(data)
                    entry.data.seek(0)
                archive.entries.append(entry)
        
        return archive 
    
    def dump_to_folder(self, path):
        print("Writing...")
        for entry in self.entries:
            print("extracted", entry.name, entry.date)
            with open(os.path.join(path, entry.name), "wb") as f:
                f.write(entry.data.getvalue())
            #filetime = time.mktime(entry.datetime.timetuple())
            #os.utime(os.path.join(path, entry.name), (filetime, filetime))
            
            
        with open(os.path.join(path, "__FILE_LISTING.txt"), "w") as f:
            for entry in self.entries:
                datetime = entry.date.datetime
                
                f.write(entry.name)
                f.write(";;")
                f.write("{} {} {} {} {} {}".format(
                    datetime.year, datetime.month, datetime.day, datetime.hour, datetime.minute, datetime.second))
                f.write("\n")
    
    def write(self, f):
        f.write(b"AFS\x00")
        write_uint32(f, len(self.entries))
        f.write(b"\x00"*(0x80000-8))
        
        for entry in self.entries:
            offset = f.tell()
            entry._offset = offset
            f.write(entry.data.getvalue())
            write_pad2048(f)
        
        fileinfo_offset = f.tell()
        for entry in self.entries:
            name = entry.name.encode("ascii")
            if len(name) > 32:
                raise RuntimeError("Filename {0} is too long!".format(name))
            name += b"\x00"*(32-len(name))
            f.write(name)
            datetime = entry.date.datetime
            f.write(struct.pack("HHHHHH", 
                datetime.year, datetime.month, datetime.day, datetime.hour, datetime.minute, datetime.second))
            write_uint32(f, len(entry.data.getvalue()))
        
        fileinfo_size = f.tell()-fileinfo_offset
        write_pad2048(f)
        
        f.seek(self._fileinfo_offset)
        write_uint32(f, fileinfo_offset)
        write_uint32(f, fileinfo_size)
        
        f.seek(8)
        for entry in self.entries:
            write_uint32(f, entry._offset)
            write_uint32(f, len(entry.data.getvalue()))
        
        
            
if __name__ == "__main__":
    #with open("afs_data.afs", "rb") as f:
    #    afs = GotchaAFS.from_file(f)
    
    
    #afs.dump_to_folder("extracted/")
    newafs = GotchaAFS.from_folder("extracted/")
    with open("newafs.afs", "wb") as f:
        newafs.write(f)
    """for i, entry in enumerate(entries):
            with open("extracted/file_{0}.bin".format(i), "wb") as g:
                f.seek(entry.offset)
                g.write(f.read(entry.size))"""
    """    
    with open("afs_files.txt", "w") as f:
        for entry in entries:
            if entry.name != "":
                f.write(entry.name)
                f.write("\n")"""
                
        
        
        
        