These are some python bits and bobs for manipulating Victor 9000 hard disk images.
There are two python files - ``v9kdisklabels.py``, which has some classes representing the labels/volume boot sectors found on Victor 9000 hard disks, and ``showstat.py`` which takes advantage of these.
Why showstat? The utility provided with MS-DOS for the Victor 9000 that gave information on the disk label was called "showstat". This version does a little bit more than the original.
At its most simple, running showstat against a victor hard disk image (for example from RaSCSI) will show the volume information. You can also extract MS-DOS formatted volumes from the hard drive file together with a standard PC boot-sector. This allowed them to be mounted/edited in software such as winimage. Once edited you can insert them back into a copy of the original file for use on the Victor.
This enables the adding of software to a hard disk image without having to transfer to disk, or over serial.


Here are some examples using a 60mb image that contains two volumes.

Firstly, ``showstat --help``:

```Usage: showstat.py [OPTIONS] HDFILE

  This command shows the disk label for a Victor 9000 Hard Disk image file.
  Ensure the file you're inserting is derived from the one you extracted.

Options:
  -v, --verbose                   Display Volume details
  -e, --extract <INTEGER TEXT>...
                                  Extract volume INTEGER to file TEXT
  -i, --insert <TEXT INTEGER TEXT>...
                                  Insert file TEXT into volume INTEGER with
                                  output file TEXT
  --help                          Show this message and exit.```

  Viewing basic information:
  ```python showstat.py 60meg.dsk

Disk image: 60meg.dsk
Label Type = 2
Device ID = 1
Serial Number = 1001
Sector Size = 512

IPL Vector:
        Disk Address = 0x27
        Load Address = 0x0
        Load Length = 0x130c
        Code Entry = 0x0

Primary Boot Volume = 0

Control Parameters (Drive shape):
        Cylinders = 700
        Heads = 10
        Reduced Current Cylinder = 128
        Write Precompensation Cylinder = 128
        ECC data burst = 11
        Fast Step Control = 7
        Interleave = 5
        Spare bytes (6) =  b'\x00\x00W\x1b\x00\x00'

Available Media: 1
        Address = 0x0   Blocks = 0x1d0c7  (118983)

Working Media: 1
        Address = 0x0   Blocks = 0x1d0c7  (118983)

Virtual Volumes: 3
        Volume Number: 0  Name:  VOL1            Address = 0x2 Type : MSDOS
        Volume Number: 1  Name: VOLUME 1         Address = 0xea62 Type : MSDOS
        Volume Number: 2  Name: maintenance      Address = 0x1cea6 Type : 65535
```

You can see the basic information for the drive. And teh volumes on it - this particular image has three volumes, 0 and 1 are usable MSDOS volumes, at this stage I'm not sure what the maintenance volume is there for!

Addresses of volumes are the number of sectors from the start of the disk where they start. We can see further information about the volumes using the -v or --verbose option:

```Virtual Volumes: 3
        Volume Number: 0  Name:  VOL1            Address = 0x2 Type : MSDOS
        IPL Vector:
                Disk Address = 0x25
                Load Address = 0x0
                Load Length = 0x130c
                Code Entry = 0x0
        Volume Capacity = 0xea60 (60000)
        Data Start = 0x1
        Host Block Size = 0x200 (512)
        Allocation Unit (blocks) = 0x40 (64)
        Directory Entries = 468
        Reserved Bytes (16) = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        Physical Device = 65280         Volume = 0
        Physical Device = 65281         Volume = 0
        Physical Device = 0     Volume = 0
        Physical Device = 0     Volume = 1
        FAT Calculation for volume:
                Clusters: 937
                FAT bytes 1406
                FAT size in sectors: 3
                FAT size in sectors from class: 3
                FAT at logical sectors: 1 4
                Directory size in bytes: 14976
                Directory sectors: 30
                Cluster 3 (0x2) at logical location 0x4a00
                Cluster 3 (0x2) at physical location 0x4e00
        Volume Number: 1  Name: VOLUME 1         Address = 0xea62 Type : MSDOS
        IPL Vector:
                Disk Address = 0x0
                Load Address = 0x0
                Load Length = 0x0
                Code Entry = 0x0
        Volume Capacity = 0xe455 (58453)
        Data Start = 0x1
        Host Block Size = 0x200 (512)
        Allocation Unit (blocks) = 0x40 (64)
        Directory Entries = 456
        Reserved Bytes (16) = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        FAT Calculation for volume:
                Clusters: 913
                FAT bytes 1370
                FAT size in sectors: 3
                FAT size in sectors from class: 3
                FAT at logical sectors: 1 4
                Directory size in bytes: 14592
                Directory sectors: 29
                Cluster 3 (0x2) at logical location 0x4800
                Cluster 3 (0x2) at physical location 0x1d50c00
        Volume Number: 2  Name: maintenance      Address = 0x1cea6 Type : 65535
```

This shows the contents of what would be the FAT boot sector on a PC, but is the volume record on the Victor. These include pointers to the "initial program load" vector, and the bootable volume holds information about drive allocations (these are in order, A: onwards, the physical attribute refers to the left and right floppy drives). Also displayed is a FAT calculation for the volume, if it's an MS-DOS volume. This is the information that will form the boot sector if you extract the volume, and also provides the necessary addresses for a sense check if you're looking at things in a hex editor.

To extract a volume (let's say volume 1 in this case):
```showstat.py -e 1 vol1.img 60meg.dsk
```
You'll see the disk information displayed and then:
```Attempting to extract Volume 1 image...
                Directory size in bytes: 14592
Extracted vol1.img
```

You can then add/retrieve files from the extracted image using whatever tools you have available.

To re-integrate the volume:
```showstat.py -i vol1.img 1 new60meg.dsk 60meg.dsk
```
And you should get the messge:
```Attempting to insert vol1.img as volume 1 in new file new60meg.dsk.
```

Your original image will remain as it was, a new file is created (new60meg.dsk) with your edited volume inserted back in the right place.
