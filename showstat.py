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
    print('\tDisk Address = %s' % hex(disklabel.disk_address))
    print('\tLoad Address = %s' % hex(disklabel.load_address))
    print('\tLoad Length = %s' % hex(disklabel.load_length))
    print('\tCode Entry = %s' % hex(disklabel.code_entry))
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
        print('\tAddress = %s' % hex(media.address),'\tBlocks = %s' % hex(media.blocks), ' (%i)'% media.blocks)
    
    print('\nWorking Media: %i' % disklabel.working_media_region_count)
    for media in disklabel.working_media_list:
        print('\tAddress = %s' % hex(media.address),'\tBlocks = %s' % hex(media.blocks), ' (%i)'% media.blocks)
    
    print('\nVirtual Volumes: %i' % disklabel.virtual_volume_count)
    for volume in disklabel.virtual_volume_list:
        #Find the boot sector for the virtual volume
        hdfile.seek(volume.address*disklabel.sector_size,0)
        #Read the sector and set up the label
        volume.setVolumeLabel(hdfile.read(512))
        print('\n\tVolume Number: %i ' % volume.volume_number, 
              'Name: %s' % volume.volume_name.decode('latin-1'), 'Address = %s' % hex(volume.address), 'Type : %s' % volume.text_label)
        
        ##if this is an MS-DOS partition, print some more information
        if volume.label_type == 1:
            print('\tIPL Vector:')
            print('\t\tDisk Address = %s' % hex(volume.disk_address))
            print('\t\tLoad Address = %s' % hex(volume.load_address))
            print('\t\tLoad Length = %s' % hex(volume.load_length))
            print('\t\tCode Entry = %s' % hex(volume.code_entry))
            print('\tVolume Capacity = %s' % hex(volume.volume_capacity), '(%i)' % volume.volume_capacity)
            print('\tData Start = %s' % hex(volume.data_start))
            print('\tHost Block Size = %s' % hex(volume.host_block_size), '(%i)' % volume.host_block_size)
            print('\tAllocation Unit (blocks) = %s' %hex(volume.allocation_unit), '(%i)' % volume.allocation_unit)
            print('\tDirectory Entries = %i' % volume.number_of_directory_entries)
            print('\tReserved Bytes (16) =',volume.reserved)
                        
            if len(volume.configuration_assignments_list)>0:
                for configuration_assignment in volume.configuration_assignments_list:
                    print('\tPhysical Device = %i' % configuration_assignment.device_unit,
                          '\tVolume = %i' % configuration_assignment.volume_index)
                    
            ## Let's see if we can work out where the FAT sectors are
            ## This is FAT12, so 12 bits (or 1.5 bytes) per cluster.
            
            
            total_clusters = volume.volume_capacity/volume.allocation_unit
            print('Clusters: %i' % total_clusters)
            fat_bytes:int = total_clusters*1.5
            print('FAT bytes %i' % fat_bytes)
            fat_sectors:int = divmod(fat_bytes, volume.host_block_size)[0]+1
            print('FAT size in sectors: %i' % fat_sectors)
            print('FAT at logical sectors: %i %i' % (volume.data_start, volume.data_start+fat_sectors) )
            directory_size=volume.number_of_directory_entries*32
            print('Directory size in bytes: %i' % directory_size)
            directory_sectors = divmod(directory_size, volume.host_block_size)[0]+1
            print('Directory sectors: %i' % directory_sectors)
            cluster_three_logical = ((directory_sectors+(fat_sectors*2)+1)*volume.host_block_size)
            cluster_three_physical = cluster_three_logical + (volume.address * volume.host_block_size)
            # Cluster three should be after the directory sectors + fat sectors, plus the first boot sector
            print('cluster 3 at logical location %s' % hex(int(cluster_three_logical)))
            print('cluster 3 at physical location %s' % hex(int(cluster_three_physical)))
            
    
    hdfile.close() 
    
if __name__ == "__main__":
        cli()
