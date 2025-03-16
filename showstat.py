##
#   showstat.py
#   Shows disk information for a V9k hard disk image (linear)
#
#   Copyright (c) Daniel Jameson 2025
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import click
import v9kdisklabels

@click.command()
@click.argument("hdfile", type=click.File("rb"))
def cli(hdfile):
    """This command shows the disk label for a Victor 9000 Hard Disk image file"""

    disklabel = v9kdisklabels.HDLabel()
    disklabel.set_labels(hdfile.read())
    data = disklabel.get_binary_label()
    hdfile.close()
    print('Label Type = %i' % disklabel.label_type)
    print('Device ID = %i' % disklabel.device_id)
    print('Serial Number = %s' %disklabel.serial_number.decode())
    print('Sector Size = %i' %disklabel.sector_size)
    print('\nIPL Vector:')
    print('\tDisk Address = ', hex(disklabel.disk_address))
    print('\tLoad Address = ', hex(disklabel.load_address))
    print('\tLoad Length = ', hex(disklabel.load_length))
    print('\tCod Entry = ', hex(disklabel.cod_entry))
    print('\nControl Parameters (Drive shape):')
    
    
if __name__ == "__main__":
        cli()
