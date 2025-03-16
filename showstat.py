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

    sectordata = hdfile.read(1048)
    disklabel = v9kdisklabels.HDLabel()  
    disklabel.set_hdd_labels(sectordata)
   
    
    # Sector size in the right place is probably the best indication of a valid
    # image...
    if (disklabel.sector_size != 512):
        print('\nThis might not be a V9k disk image, but we\'ll have a go anyway...')
    
    print('\nDisk image: %s' % hdfile.name)
    print('Label Type = %i' % disklabel.label_type)
    print('Device ID = %i' % disklabel.device_id)
    print('Serial Number = %s' %disklabel.serial_number.decode('latin-1'))
    print('Sector Size = %i' %disklabel.sector_size)
    print('\nIPL Vector:')
    print('\tDisk Address = ', hex(disklabel.disk_address))
    print('\tLoad Address = ', hex(disklabel.load_address))
    print('\tLoad Length = ', hex(disklabel.load_length))
    print('\tCod Entry = ', hex(disklabel.cod_entry))
    print('\nPrimary Boot Volume = %i' % disklabel.primary_boot_volume)
    print('\nControl Parameters (Drive shape):')
    print('\tCylinders = %i' % disklabel.cylinders)
    print('\tHeads = %i' % disklabel.heads)
    print('\tReduced Current Cylinder = %i' % disklabel.reduced_current)
    print('\tWrite Precompensation Cylinder = %i' % disklabel.write_precomp)
    print('\tECC data burst = %i' % disklabel.data_burst)
    print('\tFast Step Control = %i' % disklabel.fast_step_control)
    print('\tInterleave = %i' % disklabel.interleave)
    print('\tSpare bytes (6) = ', disklabel.spare_bytes)
    
    print('\nAvailable Media: %i' % disklabel.available_media_region_count)
    for media in disklabel.available_media_list:
        print('\tAddress = ',hex(media.address),'\tBlocks = ',hex(media.blocks), '(', media.blocks, ')')
    
    print('\nWorking Media: %i' % disklabel.working_media_region_count)
    for media in disklabel.working_media_list:
        print('\tAddress = ',hex(media.address),'\tBlocks = ',hex(media.blocks), '(', media.blocks, ')')
    
    print('\nVirtual Volumes: %i' % disklabel.virtual_volume_count)
    for volume in disklabel.virtual_volume_list:
        #Find the boot sector for the virtual volume
        hdfile.seek(volume.address*disklabel.sector_size,0)
        #Read the sector and set up the label
        volume.setVolumeLabel(hdfile.read(512))
        print('\tVolume Number: %i ' % volume.volume_number, 
              'Name: %s' % volume.volume_name.decode('latin-1'), 'Address = ',hex(volume.address))

    
    hdfile.close() 
    
if __name__ == "__main__":
        cli()
