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
import os
import copy


@click.command()
@click.argument("hdfile", type=click.File("rb"))
@click.option('--verbose', '-v', is_flag=True, help='Display Volume details')
@click.option('--extract', '-e', type=(int,str), help='Extract volume INTEGER to file TEXT')
@click.option('--insert', '-i', type=(str,int,str), help='Insert file TEXT into volume INTEGER with output file TEXT')
@click.option('--dumpall', '-d', is_flag=True, help='Dump all the volumes with .XXX suffix where XXX is the Volume No.')

def cli(hdfile, verbose, extract, insert, dumpall):
    """This command shows the disk label for a Victor 9000 Hard Disk image file.
    Ensure the file you're inserting is derived from the one you extracted."""

    sectordata = hdfile.read(512)
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
    
    # If this is a real disk image, we might have bad tracks - in which case let's eject a sanitised
    # version of the disk image.
    if disklabel.available_media_region_count > 1:
        
        # Make a new disklabel which only has the one zone
        newlabel=copy.deepcopy(disklabel)

        #set up a new availablemedia object
        avmedia = v9kdisklabels.AvailableMedia()
        avmedia.address=0
        avmedia.blocks=newlabel.cylinders*newlabel.heads*17
        avmedia.region_number=0
        
        # Stick it in the available Media list
        newlabel.available_media_region_count=1
        newlabel.available_media_list=[]
        newlabel.available_media_list.append(avmedia)
        
        #Stick it in the working Media list (as a copy)
        newlabel.working_media_region_count=1
        newlabel.working_media_list=[]
        newlabel.working_media_list.append(copy.deepcopy(avmedia))
        
        sanitised_file = open(hdfile.name+'.new','wb')

        print('\nThis looks to be an image of a disc that had bad regions.\n'+
              'Generating a new file: %s that has these stripped.' % sanitised_file.name)
        print('The following information will be based on the new file.')
        
        outdata = bytearray(newlabel.get_binary_label())
        padding = bytearray(newlabel.sector_size-len(outdata))
        outdata.extend(padding)
        #Write new label out
        sanitised_file.write(outdata)
        
        #foreach working media copy x blocks from x address (if first, address+2)

        for media in disklabel.available_media_list:
            address = media.address
            blocks = media.blocks
            if media.region_number==0:
                address += 1
                blocks -= 1
            hdfile.seek(address*disklabel.sector_size,0)
            outdata=hdfile.read(blocks*disklabel.sector_size)
            sanitised_file.write(outdata)
                
        padding = bytearray(os.stat(hdfile.name).st_size-os.stat(sanitised_file.name).st_size)
        sanitised_file.write(padding)
        #close files
        hdfile.close()
        sanitised_file.close()
        #point hdfile at the new file
        hdfile=open(sanitised_file.name,'rb')
        disklabel=newlabel      
        
        

    
    print('\nVirtual Volumes: %i' % disklabel.virtual_volume_count)
    for volume in disklabel.virtual_volume_list:
        #Find the boot sector for the virtual volume
        hdfile.seek(volume.address*disklabel.sector_size,0)
        #Read the sector and set up the label
        volume.setVolumeLabel(hdfile.read(512))
        print('\tVolume Number: %i ' % volume.volume_number, 
            'Name: %s' % volume.volume_name.decode('latin-1'), 'Address = %s' % hex(volume.address), 'Type : %s' % volume.text_label)
        if verbose:
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
                
                print('\tFAT Calculation for volume:')
                total_clusters = volume.volume_capacity/volume.allocation_unit
                print('\t\tClusters: %i' % total_clusters)
                fat_bytes:int = round(total_clusters*1.5)
                print('\t\tFAT bytes %i' % fat_bytes)
                fat_sectors = divmod(fat_bytes, volume.host_block_size)[0]+1
                print('\t\tFAT size in sectors: %i' % fat_sectors)
                print('\t\tFAT size in sectors from class: %i' % volume.fat_bootsector.fat_size)
                print('\t\tFAT at logical sectors: %i %i' % (volume.data_start, volume.data_start+fat_sectors) )
                directory_size=volume.number_of_directory_entries*32
                print('\t\tDirectory size in bytes: %i' % directory_size)
                directory_sectors = divmod(directory_size, volume.host_block_size)[0]
                if divmod(directory_size,directory_sectors)[1] > 0:
                    directory_sectors +=1
                print('\t\tDirectory sectors: %i' % directory_sectors)
                cluster_three_logical = ((directory_sectors+(fat_sectors*2)+1)*volume.host_block_size)
                cluster_three_physical = cluster_three_logical + (volume.address * volume.host_block_size)
                # Cluster three should be after the directory sectors + fat sectors, plus the first boot sector
                print('\t\tCluster 3 (0x2) at logical location %s' % hex(int(cluster_three_logical)))
                print('\t\tCluster 3 (0x2) at physical location %s' % hex(int(cluster_three_physical)))

    if extract:
        print('Attempting to extract Volume %i image...' % extract[0])
        if extract[0] < len(disklabel.virtual_volume_list):

            volume = disklabel.virtual_volume_list[extract[0]]
            if volume.label_type == 1:
                savevolume = open(extract[1],'wb')            
                extract_volume(hdfile, savevolume, volume)
                savevolume.close()
            else:
                print('Volume %i is not an MS-DOS volume.' % extract[0])
        else:
            print('Volume %i does not exist.' % extract[0])        
    elif insert:
        print('Attempting to insert %s as volume %i in new file %s.' % (insert[0], insert[1], insert[2]))     
        infile = open(insert[0],'rb')
        outfile = open(insert[2], 'wb')
        volume = disklabel.virtual_volume_list[insert[1]]
        if os.stat(infile.name).st_size == volume.volume_capacity*volume.host_block_size:
            insert_volume(hdfile, infile, outfile, volume)
            print('Success!')
        else:
            print('Volume size mismatch.')
        infile.close()
        outfile.close()
    elif dumpall:
        print('Dumping all MS-DOS volumes...')
        for volume in disklabel.virtual_volume_list:
            if volume.label_type == 1:
                savevolume = open(hdfile.name+'.'+'{:0>3}'.format(volume.volume_number),'wb')
                extract_volume(hdfile, savevolume, volume)
                savevolume.close()
        
    hdfile.close() 

def extract_volume(hdfile, savevolume, volume):
    #Whilst the v9k automatically deals with rounding to the sector, PC DOS is a bit
    #more literal...
    directory_size=volume.number_of_directory_entries*32
    ##print('\t\tDirectory size in bytes: %i' % directory_size)
    directory_sectors = divmod(directory_size, volume.host_block_size)[0]
    if divmod(directory_size, volume.host_block_size)[1] > 0:
        directory_sectors +=1
    # If this is DOS3.1 we seem to need an extra sector for the directory...
    
    volume.fat_bootsector.root_dir_entries=round((directory_sectors*512)/32)
    #print(volume.fat_bootsector.getFATBootSectorBytes())
    data=bytearray(volume.fat_bootsector.getFATBootSectorBytes())
    padding=bytearray(volume.host_block_size-len(data)-2)
    data.extend(padding)
    data.extend([0x55,0xaa])
    savevolume.write(data)
    filepointer=(volume.address*volume.host_block_size)+volume.host_block_size
    blockcounter=1
    hdfile.seek(filepointer,0)
    while blockcounter<volume.volume_capacity:
        savevolume.write(hdfile.read(volume.host_block_size))
        blockcounter+=1
    print('Extracted %s' % savevolume.name)
    return

def insert_volume(hdfile, infile, outfile, volume):
    blockcounter=0
    hdfile.seek(0)
    outdata=hdfile.read(volume.host_block_size)
    insertdata = infile.read(volume.host_block_size)
    while outdata:
        if blockcounter<(volume.address+1) or blockcounter>(volume.address+volume.volume_capacity):
            outfile.write(outdata)
        else:
            insertdata = infile.read(volume.host_block_size)
            if insertdata:
                outfile.write(insertdata)
            else:
                outfile.write(outdata)
        outdata=hdfile.read(volume.host_block_size)
        blockcounter+=1
    return

    
if __name__ == "__main__":
        cli()
