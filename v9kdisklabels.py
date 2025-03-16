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
VOLUME_TYPES=['Undefined,','MSDOS','CP/M','UNIX','Custom 4', 'Custom 5', 'Custom 6','Custom 7', 'Custom 8']

@dataclass
class AvailableMedia:
    region_number: int = 0
    address: int = 0
    blocks: int = 0

@dataclass        
class WorkingMedia:
    region_number: int = 0
    address: int = 0
    blocks: int = 0

@dataclass    
class Assignments:
    device_unit = 0 # word
    volume_index = 0 # word
    
class VirtualVolumeLabel:
    volume_number = 0
    
    #This is from the main disk label
    address = 0
    
    #These are the virtual label values
    label_type = 0 # word
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
    
    def setVolumeLabel(self, bootsector):
        # print(bootsector)  
        pointer = 0
        (self.label_type, self.volume_name, self.disk_address, self.load_address,
         self.load_length, self.code_entry, self.volume_capacity, self.data_start, self.host_block_size,
         self.allocation_unit, self.number_of_directory_entries, 
         self.reserved) = VIRTUAL_VOLUME_LABEL_FORMAT.unpack(bootsector[pointer:VIRTUAL_VOLUME_LABEL_FORMAT.size])
        pointer = pointer + VIRTUAL_VOLUME_LABEL_FORMAT.size
        
        if self.label_type <= 8:
            self.text_label = VOLUME_TYPES[self.label_type]
        else:
            self.text_label = str(self.label_type)
        
        # Configuration assignments...
        configuration_assignment_count = int.from_bytes(SINGLE_BYTE_FORMAT.unpack(
            bootsector[pointer:pointer+SINGLE_BYTE_FORMAT.size]))
        pointer = pointer + SINGLE_BYTE_FORMAT.size
        
        counter = 0
        while counter < configuration_assignment_count:
            configuration_assignment = Assignments()
            (configuration_assignment.device_unit, 
             configuration_assignment.volume_index) = CONFIGURATION_ASSIGNMENT_FORMAT.unpack(
                 bootsector[pointer:pointer+CONFIGURATION_ASSIGNMENT_FORMAT.size])
            pointer = pointer + CONFIGURATION_ASSIGNMENT_FORMAT.size
            self.configuration_assignments_list.append(configuration_assignment)
            counter = counter + 1
            
    
    

class HDLabel:
    #This is the main hard disk label in sector 0
    label_type = 0 #word
    device_id = 0 #word
    serial_number = bytearray(16) #16 byte string
    sector_size = 0  #word
    disk_address = 0 #dword
    load_address = 0 #word
    load_length = 0 #word
    cod_entry = 0 #dword
    primary_boot_volume = 0 #word
    cylinders = 0 #word big endian
    heads = 0 #byte
    reduced_current = 0 #word big endian
    write_precomp = 0 #word big endian
    data_burst = 0 #byte
    fast_step_control = 0 #byte
    interleave = 0 #byte
    spare_bytes = bytearray(6) # 6 bytes
    
    #These bits vary depending on volumes on the HDD
    available_media_region_count = 0 #byte
    
    #Array of available media
    available_media_list: List[AvailableMedia] = []
    
    working_media_region_count = 0 #byte
    
    #List of working media
    working_media_list: List[WorkingMedia] = []

    virtual_volume_count = 0 #byte
    
    #Array of volume addresses
    virtual_volume_list: List[VirtualVolumeLabel] = []
    
    def get_binary_label(self):
        data = DISK_LABEL_FORMAT.pack(self.label_type, self.device_id, self.serial_number, self.sector_size, 
                           self.disk_address, self.load_address, self.load_length, self.cod_entry, self.primary_boot_volume)
        data = data + CONTROL_PARAMS_FORMAT.pack(self.cylinders, self.heads, self.reduced_current, self.write_precomp, 
                                  self.data_burst, self.fast_step_control, self.interleave, self.spare_bytes)
        return data
    
    def set_hdd_labels(self, first_two_sector_data):
        pointer = 0 
        end_of_main_label=DISK_LABEL_FORMAT.size+CONTROL_PARAMS_FORMAT.size
        
        (self.label_type, self.device_id, self.serial_number, self.sector_size, 
         self.disk_address, self.load_address, self.load_length, 
         self.cod_entry, self.primary_boot_volume) = DISK_LABEL_FORMAT.unpack(first_two_sector_data[pointer:DISK_LABEL_FORMAT.size])
        
        pointer=pointer+DISK_LABEL_FORMAT.size
        
        (self.cylinders, self.heads, self.reduced_current, self.write_precomp, 
         self.data_burst, self.fast_step_control, self.interleave, 
         self.spare_bytes) = CONTROL_PARAMS_FORMAT.unpack(
             first_two_sector_data[pointer:pointer+CONTROL_PARAMS_FORMAT.size])
         
        pointer=pointer+CONTROL_PARAMS_FORMAT.size

        #these are the variable elements
        
        #First available media regions
        
        self.available_media_region_count = int.from_bytes(SINGLE_BYTE_FORMAT.unpack(
            first_two_sector_data[pointer:pointer+SINGLE_BYTE_FORMAT.size]))
        pointer = pointer + SINGLE_BYTE_FORMAT.size
               
        counter = 0
        while counter < self.available_media_region_count:
            available_media=AvailableMedia()
            available_media.region_number=counter
            (available_media.address,available_media.blocks)=MEDIA_LIST_FORMAT.unpack(first_two_sector_data[pointer:pointer+MEDIA_LIST_FORMAT.size])
            pointer = pointer + MEDIA_LIST_FORMAT.size
            self.available_media_list.append(available_media)
            counter = counter + 1
        
        #Working media regions
        
        self.working_media_region_count = int.from_bytes(SINGLE_BYTE_FORMAT.unpack(
            first_two_sector_data[pointer:pointer+SINGLE_BYTE_FORMAT.size]))
        pointer = pointer + SINGLE_BYTE_FORMAT.size
        
        counter = 0
        while counter < self.working_media_region_count:
            working_media = WorkingMedia()
            working_media.region_number=counter
            (working_media.address,working_media.blocks)=MEDIA_LIST_FORMAT.unpack(first_two_sector_data[pointer:pointer+MEDIA_LIST_FORMAT.size])
            pointer = pointer + MEDIA_LIST_FORMAT.size
            self.working_media_list.append(working_media)
            counter = counter + 1
        
        #Virtual volume addresses
        
        self.virtual_volume_count = int.from_bytes(SINGLE_BYTE_FORMAT.unpack(
            first_two_sector_data[pointer:pointer+SINGLE_BYTE_FORMAT.size]))
        pointer = pointer + SINGLE_BYTE_FORMAT.size
        
        counter = 0
        while counter < self.virtual_volume_count:
            virtual_volume = VirtualVolumeLabel()
            virtual_volume.volume_number = counter
            virtual_volume.address=VOLUME_ADDRESS_FORMAT.unpack(first_two_sector_data[pointer:pointer+VOLUME_ADDRESS_FORMAT.size])[0]
            pointer = pointer + VOLUME_ADDRESS_FORMAT.size
            self.virtual_volume_list.append(virtual_volume)
            counter=counter + 1


    


        
