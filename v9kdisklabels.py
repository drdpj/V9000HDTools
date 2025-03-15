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

class HDLabel:
    label_type=2 #word
    device_id=0 #word
    serial_number= bytearray(16)
    sector_size=512 #word
    disk_address=4 #dword
    load_address=5 #word
    load_length=3 #word
    cod_entry=1 #dword
    primary_boot_volume=4 #word
    cylinders=0 #word big endian
    heads=0 #byte
    reduced_current=128 #word big endian
    write_precomp=128 #word big endian
    data_burst=0 #byte
    fast_step_control=0 #byte
    interleave=0 #byte
    spare_bytes = bytearray(6)
   
    
    def get_binary_label(self):
        data = struct.pack("<HH 16s HIHHIH", self.label_type, self.device_id, self.serial_number, self.sector_size, 
                           self.disk_address, self.load_address, self.load_length, self.cod_entry, self.primary_boot_volume)
        data = data + struct.pack(">HBHHBBB 6s", self.cylinders, self.heads, self.reduced_current, self.write_precomp, 
                                  self.data_burst, self.fast_step_control, self.interleave, self.spare_bytes)
        return data

    


    
