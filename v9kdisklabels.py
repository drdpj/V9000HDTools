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

DISK_LABEL_FORMAT = struct.Struct("<HH 16s HIHHIH")
CONTROL_PARAMS_FORMAT = struct.Struct(">HBHHBBB 6s B")
VIRTUAL_VOLUME_LABEL_FORMAT = struct.Struct("<HBIHHIIIHHH 16s B")
VOLUME_ASSIGNMENT_FORMAT = struct.Struct("<HH")


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
    available_media_list = None
    working_media_region_count = 0 #byte
    working_media_list = None
    virtual_volume_count = 0 #byte
    virtual_volume_list = None
    
    def get_binary_label(self):
        data = DISK_LABEL_FORMAT.pack(self.label_type, self.device_id, self.serial_number, self.sector_size, 
                           self.disk_address, self.load_address, self.load_length, self.cod_entry, self.primary_boot_volume)
        data = data + CONTROL_PARAMS_FORMAT.pack(self.cylinders, self.heads, self.reduced_current, self.write_precomp, 
                                  self.data_burst, self.fast_step_control, self.interleave, self.spare_bytes)
        return data
    
    def set_hdd_labels(self, first_two_sector_data):
        (self.label_type, self.device_id, self.serial_number, self.sector_size, 
         self.disk_address, self.load_address, self.load_length, 
         self.cod_entry, self.primary_boot_volume) = DISK_LABEL_FORMAT.unpack(first_two_sector_data[:DISK_LABEL_FORMAT.size])
        (self.cylinders, self.heads, self.reduced_current, self.write_precomp, 
         self.data_burst, self.fast_step_control, self.interleave, 
         self.spare_bytes) = CONTROL_PARAMS_FORMAT.unpack(
             first_two_sector_data[DISK_LABEL_FORMAT.size:DISK_LABEL_FORMAT.size+CONTROL_PARAMS_FORMAT.size])


    


    
