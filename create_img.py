#!/usr/bin/env python3
"""
create_v9k_image.py

Generate a Victor 9000 hard-disk image that obeys the boot-ROM limits:
  • every available/working media region is ≤ 65 535 sectors
  • total usable media is < 0x80000 sectors (524 288)

Example:
    python create_v9k_image.py \
        --output v9k-60m.img \
        --cylinders 3800 --heads 8 --spt 17 \
        --serial "chs 3800,8,17" \
        --volume SYS:30:8:400 \
        --volume DATA:30 \
        --boot-volume 0
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from v9kdisklabels import (
    HDLabel,
    AvailableMedia,
    WorkingMedia,
    VirtualVolumeLabel,
    FATbootSector,
    VIRTUAL_VOLUME_LABEL_FORMAT,
    SINGLE_BYTE_FORMAT,
    CONFIGURATION_ASSIGNMENT_FORMAT,
)

SECTOR_SIZE = 512
MAX_REGION_SECTORS = 0x10000 - 1           # 65 535
MAX_TOTAL_SECTORS = 0x80000                # must stay strictly below this
DEFAULT_INTERLEAVE = 5
DEFAULT_FAST_STEP = 7
DEFAULT_ECC_BURST = 11
DEFAULT_REDUCED_CURRENT = 128
DEFAULT_WRITE_PRECOMP = 128


@dataclass(frozen=True)
class VolumeSpec:
    name: str
    size_mib: float
    allocation_unit: int
    root_entries: int

    @property
    def size_sectors(self) -> int:
        sectors = int(round(self.size_mib * (1024 * 1024 / SECTOR_SIZE)))
        if sectors == 0:
            raise ValueError(f"Volume {self.name} size must be > 0 MiB.")
        return sectors


def parse_volume_spec(spec: str) -> VolumeSpec:
    """
    Parse NAME:SIZE_MiB[:AU][:ROOT].
    Defaults: allocation unit = 8 sectors, root entries = 512.
    """
    parts = spec.split(":")
    if len(parts) < 2:
        raise ValueError(f"Invalid volume spec '{spec}'. Expected NAME:SIZE[:AU][:ROOT].")

    name = parts[0][:16]
    size_mib = float(parts[1])
    allocation_unit = int(parts[2]) if len(parts) >= 3 else 8
    root_entries = int(parts[3]) if len(parts) >= 4 else 512

    if allocation_unit <= 0:
        raise ValueError("Allocation unit must be positive.")
    if root_entries <= 0:
        raise ValueError("Root directory entries must be positive.")

    return VolumeSpec(name=name, size_mib=size_mib, allocation_unit=allocation_unit, root_entries=root_entries)


def enforce_geometry_limits(cylinders: int, heads: int, spt: int) -> Tuple[int, int, int]:
    sectors_per_cylinder = heads * spt
    max_cylinders = (MAX_TOTAL_SECTORS - 1) // sectors_per_cylinder
    if cylinders > max_cylinders:
        raise ValueError(
            f"Geometry exceeds ROM limit. Reduce cylinders to <= {max_cylinders} "
            f"for {heads} heads × {spt} sectors/track."
        )
    return cylinders, heads, spt


def chunk_regions(total_sectors: int, heads: int, spt: int) -> List[Tuple[int, int]]:
    """Split the disk into consecutive regions where each length ≤ MAX_REGION_SECTORS."""
    regions: List[Tuple[int, int]] = []
    remaining = total_sectors
    cursor = 0
    sectors_per_cylinder = heads * spt
    max_cylinder_chunk = max(1, MAX_REGION_SECTORS // sectors_per_cylinder)
    max_chunk = max_cylinder_chunk * sectors_per_cylinder or MAX_REGION_SECTORS

    while remaining > 0:
        chunk = min(remaining, max_chunk)  # aligns to whole cylinders except final remainder
        if chunk > MAX_REGION_SECTORS:
            chunk = MAX_REGION_SECTORS
        regions.append((cursor, chunk))
        cursor += chunk
        remaining -= chunk

    return regions


def align_to_cylinder(sector: int, sectors_per_cylinder: int) -> int:
    remainder = sector % sectors_per_cylinder
    if remainder == 0:
        return sector
    return sector + (sectors_per_cylinder - remainder)


def pack_volume_label(volume: VirtualVolumeLabel) -> bytes:
    name = volume.volume_name
    if len(name) < 16:
        name = name + b"\x00" * (16 - len(name))

    header = VIRTUAL_VOLUME_LABEL_FORMAT.pack(
        volume.label_type,
        name,
        volume.disk_address,
        volume.load_address,
        volume.load_length,
        volume.code_entry,
        volume.volume_capacity,
        volume.data_start,
        volume.host_block_size,
        volume.allocation_unit,
        volume.number_of_directory_entries,
        volume.reserved,
    )

    assignments = volume.configuration_assignments_list
    payload = header + SINGLE_BYTE_FORMAT.pack(len(assignments))
    for assignment in assignments:
        payload += CONFIGURATION_ASSIGNMENT_FORMAT.pack(
            assignment.device_unit,
            assignment.volume_index,
        )

    if len(payload) > SECTOR_SIZE:
        raise ValueError("Volume label exceeds one sector.")

    return payload + bytes(SECTOR_SIZE - len(payload))


def build_volumes(
    specs: Sequence[VolumeSpec],
    total_sectors: int,
    sectors_per_cylinder: int,
    start_sector: int,
    align_to_cyl: bool,
) -> List[VirtualVolumeLabel]:
    volumes: List[VirtualVolumeLabel] = []
    cursor = start_sector

    for index, spec in enumerate(specs):
        size_in_sectors = spec.size_sectors
        if size_in_sectors > MAX_REGION_SECTORS:
            raise ValueError(
                f"Volume '{spec.name}' is {size_in_sectors} sectors; "
                f"must be ≤ {MAX_REGION_SECTORS} to satisfy ROM."
            )

        if align_to_cyl and cursor > start_sector:
            cursor = align_to_cylinder(cursor, sectors_per_cylinder)

        end_sector = cursor + size_in_sectors
        if end_sector > total_sectors:
            raise ValueError(f"Volumes exceed disk capacity at '{spec.name}'.")

        volume = VirtualVolumeLabel()
        volume.volume_number = index
        volume.address = cursor
        volume.label_type = 1  # MSDOS
        volume.volume_name = spec.name.encode("latin-1")[:16]
        volume.disk_address = 0
        volume.load_address = 0
        volume.load_length = 0
        volume.code_entry = 0
        volume.volume_capacity = size_in_sectors
        volume.data_start = 1  # first sector after the Victor label
        volume.host_block_size = SECTOR_SIZE
        volume.allocation_unit = spec.allocation_unit
        volume.number_of_directory_entries = spec.root_entries
        volume.reserved = bytes(16)
        volume.configuration_assignments_list = []
        volume.text_label = "MSDOS"
        volume.fat_bootsector = FATbootSector(volume)

        volumes.append(volume)
        cursor = end_sector

    return volumes


def create_disk_image(
    output: Path,
    cylinders: int,
    heads: int,
    spt: int,
    serial: str,
    volume_specs: Sequence[VolumeSpec],
    boot_volume: int,
    align_volumes: bool,
    label_revision: int,
) -> None:
    cylinders, heads, spt = enforce_geometry_limits(cylinders, heads, spt)
    total_sectors = cylinders * heads * spt
    serial_bytes = serial.encode("latin-1")[:16].ljust(16, b"\x00")

    regions = chunk_regions(total_sectors, heads, spt)

    hd_label = HDLabel()
    hd_label.label_type = label_revision
    hd_label.device_id = 1
    hd_label.serial_number = serial_bytes
    hd_label.sector_size = SECTOR_SIZE
    hd_label.disk_address = 0
    hd_label.load_address = 0
    hd_label.load_length = 0
    hd_label.code_entry = 0
    hd_label.primary_boot_volume = boot_volume
    hd_label.cylinders = cylinders
    hd_label.heads = heads
    hd_label.reduced_current = DEFAULT_REDUCED_CURRENT
    hd_label.write_precomp = DEFAULT_WRITE_PRECOMP
    hd_label.data_burst = DEFAULT_ECC_BURST
    hd_label.fast_step_control = DEFAULT_FAST_STEP
    hd_label.interleave = DEFAULT_INTERLEAVE
    hd_label.spare_bytes = bytes(6)

    hd_label.available_media_region_count = len(regions)
    hd_label.available_media_list = [
        AvailableMedia(region_number=i, address=start, blocks=length) for i, (start, length) in enumerate(regions)
    ]

    hd_label.working_media_region_count = len(regions)
    hd_label.working_media_list = [
        WorkingMedia(region_number=i, address=start, blocks=length) for i, (start, length) in enumerate(regions)
    ]

    volumes = build_volumes(
        specs=volume_specs,
        total_sectors=total_sectors,
        sectors_per_cylinder=heads * spt,
        start_sector=2,               # leave room for label sector(s)
        align_to_cyl=align_volumes,
    )

    if boot_volume >= len(volumes):
        raise ValueError("--boot-volume index is out of range.")

    hd_label.virtual_volume_count = len(volumes)
    hd_label.virtual_volume_list = volumes

    image_size = total_sectors * SECTOR_SIZE
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("wb") as f:
        f.truncate(image_size)

        label_bytes = hd_label.get_binary_label()
        if len(label_bytes) > SECTOR_SIZE:
            raise ValueError("Disk label won’t fit in one sector.")
        f.write(label_bytes + bytes(SECTOR_SIZE - len(label_bytes)))

        for volume in volumes:
            f.seek(volume.address * SECTOR_SIZE)
            f.write(pack_volume_label(volume))

    print(f"Created {output} ({image_size // (1024 * 1024)} MiB)")
    print(f"  Geometry: {cylinders} cylinders, {heads} heads, {spt} sectors/track")
    print(f"  Total sectors: {total_sectors} (≤ {MAX_TOTAL_SECTORS - 1})")
    for media in hd_label.available_media_list:
        print(f"  Media region {media.region_number}: start={media.address} length={media.blocks}")
    for volume in volumes:
        print(
            f"  Volume {volume.volume_number:02d} '{volume.volume_name.decode('latin-1').rstrip()}': "
            f"start={volume.address} sectors={volume.volume_capacity}"
        )


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Create a Victor 9000 hard-disk image with safe labels.")
    parser.add_argument("--output", required=True, type=Path, help="Disk image to create.")
    parser.add_argument("--cylinders", type=int, required=True, help="Total cylinders (<= ROM limit).")
    parser.add_argument("--heads", type=int, default=8, help="Heads (default 8).")
    parser.add_argument("--spt", type=int, default=17, help="Sectors per track (default 17).")
    parser.add_argument("--serial", default="V9000", help="Drive serial (max 16 chars).")
    parser.add_argument("--volume", action="append", required=True,
                        help="Volume spec NAME:SIZE_MiB[:AU][:ROOT]. Repeat for multiple volumes.")
    parser.add_argument("--boot-volume", type=int, default=0, help="Primary boot volume index (default 0).")
    parser.add_argument("--align-volumes", action="store_true",
                        help="Align volumes (after the first) to cylinder boundaries.")
    parser.add_argument(
        "--label-revision",
        type=int,
        choices=(1, 2),
        default=2,
        help="Disk-label revision bitfield (1 = original, 2 = revised). "
             "Use 2 to satisfy MS-DOS hdsetup; older boot ROMs may require 1.",
    )

    args = parser.parse_args(argv)

    specs = [parse_volume_spec(v) for v in args.volume]

    create_disk_image(
        output=args.output,
        cylinders=args.cylinders,
        heads=args.heads,
        spt=args.spt,
        serial=args.serial,
        volume_specs=specs,
        boot_volume=args.boot_volume,
        align_volumes=args.align_volumes,
        label_revision=args.label_revision,
    )


if __name__ == "__main__":
    main()
