# Victor 9000 Hard-Disk Image Creation Workflow

This document outlines
- creating a bootable Victor 9000 hard-disk image using the create_imp.py script in this repo 
- the firmware limits you need to respect
- how to initialise the disk under MS-DOS with `HDSETUP`/`HDFORMAT`
- how to move between raw `.img` files for piscsi and the CHD containers that MAME prefers.

## 1. Prerequisites

- Python 3 with the modules listed in `requirements.txt` (activate the bundled virtualenv or install `click` manually).
- The helper script `create_img.py` and companion library `v9kdisklabels.py` from this folder.
- The Victor MS-DOS utilities (`HDSETUP`, `HDFORMAT`, etc.) available inside the emulator.
- `chdman` (ships with MAME) if you want CHD containers.

From this directory you can run the tools via the virtualenv, e.g.:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Victor Disk Label Primer

The Victor 9000 stores its hard-disk topology in the first two sectors of the drive. Appendix K of the *Victor 9000 Hardware Reference Manual* documents the layout in detail (see [bitsavers.org/pdf/victor/victor9000/Victor_9000_Hardware_Reference_Rev_0_19831005.pdf](https://bitsavers.org/pdf/victor/victor9000/Victor_9000_Hardware_Reference_Rev_0_19831005.pdf)).

At a high level the label contains:

- **Header fields**
  - `label_type` — revision flags (bit 0 = qualified, bit 1 = MS-DOS revision); MS-DOS requires bit 1 set.
  - `device_id` — identifies the controller/drive family.
  - `serial_number` — 16 bytes of ASCII.
  - `sector_size` — always 512 for Victor hard disks.
  - `ipl_vector` — Initial Program Load [IPL] vector comprises (`disk_address`, `load_address`, `load_length`, `code_entry`) copied from the primary boot volume. These fields identify the boot loader the machine should read from disk before handing control to MS‑DOS:
    - `disk_address` – the logical sector where the boot image begins.
    - `load_address` – the paragraph in RAM where it should be loaded (0 means “load at top of memory”).
    - `load_length` – size of the boot image in paragraphs.
    - `code_entry` – the far address to jump to after loading.
  - `primary_boot_volume` — index of the virtual volume whose label contains the system IPL data.
- **Controller parameters**
  16 bytes describing the cylinder/head geometry, reduced-current and write-precompensation tracks, ECC burst length, option bits, interleave, and six spare bytes.
- **Available media list**
  - `region_count`
  - For each region: a `<physical_address, block_count>` describing the raw usable spans reported by the formatter (before considering bad-track replacement).
- **Working media list**
  Mirrors the available list but reflects the working regions currently in service. Each entry becomes a “band” the boot ROM’s `hd_read` walks through; therefore each `block_count` must stay below 65 536 sectors to avoid the 16-bit overflow in the ROM.
- **Virtual volume list**
  - `volume_count`
  - For each volume: the logical sector address of the virtual volume label. Those per-volume labels contain the FAT geometry, cluster size, root directory length, and optional drive-letter assignments. Together the addresses in this list define the partition structure that tools such as `HDSETUP` present.

Understanding these fields helps explain why the region limits in the next section matter: they map directly to the working-media entries consumed by the boot firmware.

## 3. Firmware Limits You Must Respect

The Victor boot ROM imposes two hard limits which the generator enforces:

| Limit | Impact | Workaround |
| ----- | ------ | ---------- |
| **Per-region size < 65 536 sectors** (~32 MiB at 512 B/sector) | If any working-region entry in the label exceeds this, the loader’s 16-bit math wraps and the machine hangs during boot. | Split the disk into multiple regions/volumes; `create_img.py` automatically chunks the media for you, and individual volumes must not exceed 65 535 sectors (~31.5 MiB). |
| **Total usable sectors < 0x80000** (524 288) | The label stores only 21 address bits; crossing 0x80000 makes lengths wrap to zero. | Keep the overall geometry at or below 3 800 cylinders × 8 heads × 17 sectors/track = 516,800 sectors. If you use different geometry, make sure `cylinders × heads × spt < 524,288`. |


## 4. Generate the Raw Image

Run `create_img.py` to carve out the disk. Example: seven 30 MiB volumes plus a 10 MiB tail, with a bootable 30 MiB system volume:

```bash
python3 create_img.py \
  --output victor_256.img \
  --cylinders 3800 --heads 8 --spt 17 \
  --serial "chs 3800,8,17" \
  --volume BOOT:30:8:640 \
  --volume APPS:30 \
  --volume DATA1:30 \
  --volume DATA2:30 \
  --volume DATA3:30 \
  --volume DATA4:30 \
  --volume DATA5:30 \
  --volume TAIL:10 \
  --boot-volume 0 \
  --align-volumes \
  --label-revision 2
```

Key flags:

- `--boot-volume` selects the virtual volume whose IPL data is copied into the master label (typically volume 0).
- `--volume` can be repeated; keep each SIZE ≤ 31.5 MiB (≈ 65 535 sectors). Volume specifications can tailor FAT parameters: `[VOLUME NAME]:[SIZE IN MIB][:ALLOCATION_UNIT][:ROOT_ENTRIES]`. Example: `DATA:30:8:1024` creates a 30 MiB volume named DATA with 8-sector clusters and a 1024-entry root directory.

- `--label-revision 2` makes `HDSETUP` happy; leave this unless you have a ROM that insists on revision 1.
- `--spt` means sectors per track and should always be 17 for the victor
- `--label-revision` should be left at the default value `2`. MS-DOS `HDSETUP` rejects labels that do not have the revision bits set.
- `--align-volumes` snaps each volume (after the first) to the next cylinder boundary. This keeps the OEM utilities happy but costs a few dozen sectors between slices. Disable it if you need every sector or are hand-editing the label later.

Verify the label before taking it into the emulator:

```bash
python3 showstat.py victor_256.img
```

You should see the geometry, region list, and virtual volumes you requested.

## 5. Initialise the Drive in MS-DOS

In MAME, mount the raw `.img` or a CHD created from it (see § 6). Boot from a floppy containing the Victor MS-DOS tools and run:

1. **HDSETUP**
   - The tool reads the label; if it reports “Invalid drive label type,” you are probably pointing it at a CHD header or the label lacks revision bit 2.
   - Assign drive letters in the *configuration assignment* section. A common mapping is:
     - `A:` – boot hard-disk volume (the Victor default for hard drives)
     - `B:` / `C:` – left/right floppies
     - Higher letters (`D:`, `E:`, …) – remaining hard-disk volumes
   - If desired, reserve headroom by leaving one of the listed volumes unassigned or over-writing an entry with `NONE`.

After running HDSETUP reboot the machine with an operating system that has HD support. Then you can use the disks as normal. Once you copy the OS over like `sys b: a:` copying the OS from floppy B: to hard disk A:, you can reboot directly from the hard disk.

## 6. Growing or Adjusting Volumes

- To leave “free” space visible to `HDSETUP`, reduce the last volume’s size or disable `--align-volumes` so the 32-sector alignment gaps aren’t consumed automatically.
- For bigger root directories, set the fourth field in the `--volume` spec (e.g. `BOOT:30:8:640`).
- Drive-letter assignments live inside each virtual volume’s label. The script currently leaves them blank; you must assign them in `HDSETUP`. (You can extend the script to populate `configuration_assignments_list` if you’d like a fixed mapping.)

## 7. Convert Between `.img` and `.chd`

### 7.1. Raw image → CHD (for MAME)

```bash
/path/to/chdman createhd \
    -i victor_256.img \
    -o victor_256.chd \
    -chs 3800,8,17 \
    -ss 512
```

Use `chs` and `ss` values that match the geometry you passed to `create_img.py`. MAME presents only the raw sectors inside the CHD; the emulated machine never sees the CHD header.

### 7.2. CHD → raw image (for RaSCSI, logic analysers, etc.)

```bash
/path/to/chdman extracthd \
    -i victor_256.chd \
    -o victor_256_extracted.img
```

Verify the first sector if you like:

```bash
xxd -l 32 victor_256_extracted.img
# should start with: 02 00 01 00 … (“label type 2, device ID 1”)
```

The extracted `.img` can be mounted directly by RaSCSI, Disk2FDI, or any other tool that expects a linear SASI disk image.

## 8. Quick Checklist

1. Generate the image with `create_img.py`, keeping per-volume size ≤ 65 535 sectors and total ≤ 0x80000 sectors.
2. Verify with `showstat.py` that the label looks sane.
3. In MAME, run `HDSETUP` → assign drive letters; `HDFORMAT` → format each volume; copy the system files.
4. (Optional) Convert to CHD for MAME (`chdman createhd`) or back to raw for other tools (`chdman extracthd`).

Following this process gives you a bootable Victor 9000 disk image that obeys the ROM’s constraints and can be moved between emulators and hardware-friendly formats without surprises.
