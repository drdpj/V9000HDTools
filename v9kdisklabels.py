##
#   v8kdisklabels.py
#   classes to deal with v9k disk labels
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

import struct
from dataclasses import dataclass
from typing import List

# This is the format for the main element of the disk label
DISK_LABEL_FORMAT = struct.Struct("<HH 16s HIHHIH") 


#This is the format for the control block for the physical drive
CONTROL_PARAMS_FORMAT = struct.Struct(">HBHHBBB 6s")

#Available media and working media have dwords for address and block count
MEDIA_LIST_FORMAT = struct.Struct("<II")

#Volumes have a dword address
VOLUME_ADDRESS_FORMAT = struct.Struct("<I")

#This is the format for the partition boot sectors
#They're referred to as virtual volumes
VIRTUAL_VOLUME_LABEL_FORMAT = struct.Struct("<H 16s I HH III HHH 16s")

SINGLE_BYTE_FORMAT = struct.Struct("B")

CONFIGURATION_ASSIGNMENT_FORMAT = struct.Struct("<HH")

#Volume Types
VOLUME_TYPES=['Undefined','MSDOS','CP/M','UNIX','Custom 4', 'Custom 5', 'Custom 6','Custom 7', 'Custom 8']

#Standard PC DOS Boot Sector - extended?
PC_BOOT_SECTOR_FORMAT = struct.Struct("<3s 8s H B H B H H B H H H H")

@dataclass
class AvailableMedia:
    """Class representing data associated with available media.
    
    Attributes
    ----------
    region_number : int
        An index number for the media region.
    address : int
        Physical address of the region on the disk.
    blocks : int
        The size of the region in blocks."""
        
    region_number:int = 0
    address:int = 0
    blocks:int = 0

@dataclass        
class WorkingMedia:
    """Class representing data associated with working media.
    
    Attributes
    ----------
    region_number : int
        An index number for the media region.
    address : int
        Physical address of the region on the disk.
    blocks : int
        The size of the region in blocks."""
    
    region_number: int = 0
    address: int = 0
    blocks: int = 0

@dataclass    
class Assignments:
    """Class representing physical and volume assignments to drives letters.
    """
    device_unit:int = 0 # word
    volume_index:int = 0 # word
    
    
    
class VirtualVolumeLabel:
    """Class representing the data associated with a virtual volume.
    
    Attributes
    ----------
    volume_number : int
        Index number of the volume on the disk
    label_type : int
        Numerical representation of label type
        1=MS-DOS
        2=CP/M
        3=UNIX
    volume_name : bytearray(16)
        String with the name of the volume
    disk_address : int
        Double word with the virtual address of the 
        Initial Program Load boot program image.
    load_address : int
        Double word, the paragraph address of the memory where the 
        boot program is to load. A zero entry indicates a default 
        load to the highest RAM location.
    load_length : int
        Length of the boot program in paragraphs.
    code_entry : int
        Double word representing the entry address of the
        boot program. Segment of zero defaults to the segment
        of the loaded program.
    volume_capacity : int
        Number of actual blocks comprising the virtual volume.
    data_start : int
        Offset (in blocks) to the start of the data space.
    host_block_size : int
        Size of a block (sector) in bytes
    allocation_unit : int
        Size of allocation units in blocks
    number_of_directory_entries : int
        Number of entries allowed in root directory
    reserved : bytearray(16)
        16 spare bytes
    configuration_assignments_list : List[Assignments]
        A list of drive assignments in order from A: onwards.
    text_label : str
        A string representing the type of partition. Not part
        of the actual disk label
    """
    
    volume_number:int = 0
    
    #This is from the main disk label
    address:int = 0
    
    #These are the virtual label values
    #Data start is the fist sector after the boot sector that's used
    #On MS-DOS partitions this will be the first FAT (there are two)
    
    label_type :int = 0 # word
    volume_name = bytearray(16)
    disk_address = 0 #dword
    load_address = 0 #word
    load_length = 0 #word
    code_entry = 0 #dword
    volume_capacity = 0 #dword - number of physical blocks
    data_start = 0 #dword - virtual address
    host_block_size = 0 #word - MSDOS is 512bytes
    allocation_unit = 0 #word - in physical blocks
    number_of_directory_entries = 0 # word - entry count
    reserved = bytearray(16)
    configuration_assignments_list: List[Assignments]= []
    text_label: str
    fat_bootsector = None
    
    def __init__(self):
        #Zero lists
        self.configuration_assignments_list=[]
        
    
    def setVolumeLabel(self, bootsector):
        """_summary_

        Args:
            bootsector (bytes): a list of bytes for the virtual volume bootsector.
        """

        pointer = 0
        (self.label_type, self.volume_name, self.disk_address, self.load_address,
         self.load_length, self.code_entry, self.volume_capacity, self.data_start, self.host_block_size,
         self.allocation_unit, self.number_of_directory_entries, 
         self.reserved) = VIRTUAL_VOLUME_LABEL_FORMAT.unpack(bootsector[pointer:VIRTUAL_VOLUME_LABEL_FORMAT.size])
        pointer += VIRTUAL_VOLUME_LABEL_FORMAT.size
        
        if self.label_type <= 8:
            self.text_label = VOLUME_TYPES[self.label_type]
        else:
            self.text_label = str(self.label_type)
        
        # Configuration assignments...
        configuration_assignment_count = int.from_bytes(SINGLE_BYTE_FORMAT.unpack(
            bootsector[pointer:pointer+SINGLE_BYTE_FORMAT.size]))
        pointer += SINGLE_BYTE_FORMAT.size
        
        counter = 0
        while counter < configuration_assignment_count:
            configuration_assignment = Assignments()
            (configuration_assignment.device_unit, 
             configuration_assignment.volume_index) = CONFIGURATION_ASSIGNMENT_FORMAT.unpack(
                 bootsector[pointer:pointer+CONFIGURATION_ASSIGNMENT_FORMAT.size])
            pointer = pointer + CONFIGURATION_ASSIGNMENT_FORMAT.size
            self.configuration_assignments_list.append(configuration_assignment)
            counter += 1
            
        if self.label_type ==0x01:
            self.fat_bootsector = FATbootSector(self)
            
    def getVolumeLabel(self):
        pass
    
    def getFATBootSector(self):
        pass
    
class FATbootSector:
    """Class representing a standard PC Bootsector for a FAT partition. 
    Fixed values aren't listed here but can be seen in the source.
    
    Attributes
    ----------
    jmp_boot : bytearray(3) 
        Jump instruction to boot code
    
    bytes_per_sector : int
        Bytes per sector (usually 512)
    sectors_per_cluster : int
        Single byte value
    root_dir_entries : int
        Number of entries in root directory
    total_sectors_16 : int
        Total sectors on volume if < 0x10000
    fat_size : int = 0
        Number sectors per FAT
    sec_per_track:int = 0 #word - sectors/track, not used bar IBM BIOS
    heads:int = 0 #word 
    hidden_sectors:int = 0 #dword (sectors before volume)
    total_sectors_32:int = 0 #dword
    """
    jmp_boot = bytearray([0xeb,0x00, 0x90]) #first three bytes
    oem_name = bytearray("MSDOS3.1","latin1") #8 bytes
    bytes_per_sector : int = 0 #word
    sectors_per_cluster : int = 0 #byte
    reserved_sectors : int = 1 #word - always 1 on FAT12
    num_fats : int = 2 #byte - always 2 for victor images
    root_dir_entries : int = 0 #word
    total_sectors_16 : int = 0 #word
    media_field : int = 0xF8 #byte - 0xF8 is standard for HDD
    fat_size : int = 0 #word - number of FAT sectors
    sec_per_track : int = 0 #word - sectors/track, not used bar IBM BIOS
    heads : int = 0 #word 
    hidden_sectors : int = 0 #dword (sectors before volume)
    total_sectors_32 : int = 0 #dword
    end_marker = bytearray([])

    def __init__(self, volume: VirtualVolumeLabel):
        self.bytes_per_sector = volume.host_block_size
        self.root_dir_entries = volume.number_of_directory_entries
        self.sectors_per_cluster = volume.allocation_unit
        self.total_sectors_16 = volume.volume_capacity
        total_clusters = self.total_sectors_16/self.sectors_per_cluster
        fat_bytes:int = round(total_clusters*1.5)
        self.fat_size = divmod(fat_bytes, self.bytes_per_sector)[0]+1
        #print('PC Format Boot sector size: %i' % PC_BOOT_SECTOR_FORMAT.size)
        
    
    def getFATBootSectorBytes(self):
        return PC_BOOT_SECTOR_FORMAT.pack(self.jmp_boot, self.oem_name,
                                          self.bytes_per_sector, self.sectors_per_cluster,
                                          self.reserved_sectors, self.num_fats,
                                          self.root_dir_entries, self.total_sectors_16,
                                          self.media_field, self.fat_size,
                                          self.sec_per_track, self.heads, self.hidden_sectors)
        
    
    
   

class HDLabel:
    """Class representing the disk label for a Victor 9000 SASI disk image.

    Attributes
    ----------
    label_type : int
        Version of the label. Usually 1 or 2
    device_id : int
        Classification identifying the arrangement, for example, the drive 
        manufacturer, controller revision number. This allows for the 
        identification of compatible controllers/drives.
    serial_number : bytearray(16)
        The serial number of the unit is stored here.
    sector_size : int 
        The physical atomical unit of storage on the media.
    disk_address : int
        The logical disk address of the boot program image.
    load_address : int
        Double word, the paragraph address of the memory where the 
        boot program is to load. A zero entry indicates a default 
        load to the highest RAM location.
    load_length : int
        Length of the boot program in paragraphs.
    code_entry : int
        Double word representing the entry address of the
        boot program. Segment of zero defaults to the segment
        of the loaded program.
    primary_boot_volume : int
        The logical address of the virtual volume label containing 
        the IPL vector and configuration information.
    cylinders : int
        Number of cylinders on the disk.
    heads : int
        Number of heads.
    reduced_current : int
        Sector at which reduced current is used. (128)
    write_precomp : int
        Sector at which write precompensation reduced. (128)
    data_burst : int
        Data burst byte
    fast_step_control : int
        Fast step control byte
    interleave : int
        Interleave
    spare_bytes : bytearray(6)
        Additional bytes
    available_media_region_count : int
        Count of Available regions on the disk - permanent usable areas.
        These will be related to the "bad tracks" and sectors that
        come on old drive labels.
    available_media_list: List[AvailableMedia]
        List of AvailableMedia objects
    working_media_region_count : int
        Count of working media regions - areas that work!
    working_media_list: List[WorkingMedia]
        List of WorkingMedia objects
    virtual_volume_count : int
        Count of virtual volumes on the disk    
    virtual_volume_list: List[VirtualVolumeLabel]
        List of VirtualVolumeLabel objects representing the virtual
        volumes.
    """
    #This is the main hard disk label in sector 0
    label_type : int = 0 #word
    device_id : int = 0 #word
    serial_number = bytearray(16) #16 byte string
    sector_size : int = 0  #word
    disk_address : int = 0 #dword
    load_address : int = 0 #word
    load_length : int = 0 #word
    code_entry : int = 0 #dword
    primary_boot_volume : int = 0 #word
    cylinders : int = 0 #word big endian
    heads : int = 0 #byte
    reduced_current : int = 0 #word big endian
    write_precomp : int = 0 #word big endian
    data_burst : int = 0 #byte
    fast_step_control : int = 0 #byte
    interleave : int = 0 #byte
    spare_bytes = bytearray(6) # 6 bytes
    
    #These bits vary depending on volumes on the HDD
    available_media_region_count : int= 0 #byte
    
    #Array of available media
    available_media_list: List[AvailableMedia] = []
    
    working_media_region_count : int = 0 #byte
    
    #List of working media
    working_media_list: List[WorkingMedia] = []

    virtual_volume_count : int = 0 #byte
    
    #Array of volume addresses
    virtual_volume_list: List[VirtualVolumeLabel] = []
    
    def __init__(self):
        #Clear the lists
        self.available_media_list=[]
        self.working_media_list=[]
        self.virtual_volume_list=[]
        
    
    def get_binary_label(self):
        data = DISK_LABEL_FORMAT.pack(self.label_type, self.device_id, self.serial_number, self.sector_size, 
                           self.disk_address, self.load_address, self.load_length, self.code_entry, self.primary_boot_volume)
        data = data + CONTROL_PARAMS_FORMAT.pack(self.cylinders, self.heads, self.reduced_current, self.write_precomp, 
                                  self.data_burst, self.fast_step_control, self.interleave, self.spare_bytes)
        
        data = data + SINGLE_BYTE_FORMAT.pack(self.available_media_region_count)
        
        for mediaitem in self.available_media_list:
            data = data + MEDIA_LIST_FORMAT.pack(mediaitem.address, mediaitem.blocks)
            
        data = data + SINGLE_BYTE_FORMAT.pack(self.working_media_region_count)
        
        for mediaitem in self.working_media_list:
            data = data + MEDIA_LIST_FORMAT.pack(mediaitem.address, mediaitem.blocks)
        
        return data
    
    def set_hdd_labels(self, first_two_sector_data):
        pointer = 0 
        end_of_main_label=DISK_LABEL_FORMAT.size+CONTROL_PARAMS_FORMAT.size
        
        (self.label_type, self.device_id, self.serial_number, self.sector_size, 
         self.disk_address, self.load_address, self.load_length, 
         self.code_entry, self.primary_boot_volume) = DISK_LABEL_FORMAT.unpack(first_two_sector_data[pointer:DISK_LABEL_FORMAT.size])
        
        pointer += DISK_LABEL_FORMAT.size
        
        (self.cylinders, self.heads, self.reduced_current, self.write_precomp, 
         self.data_burst, self.fast_step_control, self.interleave, 
         self.spare_bytes) = CONTROL_PARAMS_FORMAT.unpack(
             first_two_sector_data[pointer:pointer+CONTROL_PARAMS_FORMAT.size])
         
        pointer += CONTROL_PARAMS_FORMAT.size

        #these are the variable elements
        
        #First available media regions
        
        self.available_media_region_count = int.from_bytes(SINGLE_BYTE_FORMAT.unpack(
            first_two_sector_data[pointer:pointer+SINGLE_BYTE_FORMAT.size]))
        pointer += SINGLE_BYTE_FORMAT.size
               
        counter = 0
        while counter < self.available_media_region_count:
            available_media=AvailableMedia()
            available_media.region_number=counter
            (available_media.address,available_media.blocks)=MEDIA_LIST_FORMAT.unpack(first_two_sector_data[pointer:pointer+MEDIA_LIST_FORMAT.size])
            pointer = pointer + MEDIA_LIST_FORMAT.size
            self.available_media_list.append(available_media)
            counter += 1
        
        #Working media regions
        
        self.working_media_region_count = int.from_bytes(SINGLE_BYTE_FORMAT.unpack(
            first_two_sector_data[pointer:pointer+SINGLE_BYTE_FORMAT.size]))
        pointer += SINGLE_BYTE_FORMAT.size
        
        counter = 0
        while counter < self.working_media_region_count:
            working_media = WorkingMedia()
            working_media.region_number=counter
            (working_media.address,working_media.blocks)=MEDIA_LIST_FORMAT.unpack(first_two_sector_data[pointer:pointer+MEDIA_LIST_FORMAT.size])
            pointer += MEDIA_LIST_FORMAT.size
            self.working_media_list.append(working_media)
            counter += 1
        
        #Virtual volume addresses
        
        self.virtual_volume_count = int.from_bytes(SINGLE_BYTE_FORMAT.unpack(
            first_two_sector_data[pointer:pointer+SINGLE_BYTE_FORMAT.size]))
        pointer += SINGLE_BYTE_FORMAT.size
        
        counter = 0
        while counter < self.virtual_volume_count:
            virtual_volume = VirtualVolumeLabel()
            virtual_volume.volume_number = counter
            virtual_volume.address=VOLUME_ADDRESS_FORMAT.unpack(first_two_sector_data[pointer:pointer+VOLUME_ADDRESS_FORMAT.size])[0]
            pointer = pointer + VOLUME_ADDRESS_FORMAT.size
            self.virtual_volume_list.append(virtual_volume)
            counter += 1


    


        
