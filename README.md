These are some python bits and bobs for manipulating Victor 9000 hard disk images.
There are two python files - ``v9kdisklabels.py``, which has some classes representing the labels/volume boot sectors found on Victor 9000 hard disks, and ``showstat.py`` which takes advantage of these.
Why showstat? The utility provided with MS-DOS for the Victor 9000 that gave information on the disk label was called "showstat". This version does a little bit more than the original.
At its most simple, running showstat against a victor hard disk image (for example from RaSCSI) will show the volume information. Here are some examples using a 60mb image that contains two volumes.

Firstly, ``showstat --help``:

``Usage: showstat.py [OPTIONS] HDFILE

  This command shows the disk label for a Victor 9000 Hard Disk image file.
  Ensure the file you're inserting is derived from the one you extracted.

Options:
  -v, --verbose                   Display Volume details
  -e, --extract <INTEGER TEXT>...
                                  Extract volume INTEGER to file TEXT
  -i, --insert <TEXT INTEGER TEXT>...
                                  Insert file TEXT into volume INTEGER with
                                  output file TEXT
  --help                          Show this message and exit.``