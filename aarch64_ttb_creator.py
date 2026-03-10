#!/usr/bin/env python3
"""
AArch64 Translation Table Creator with Python

Autor: Zenon Zhilong Xiu
"""

import struct

from ttb_config import GRANULES_4KB, GRANULES_16KB, GRANULES_64KB, TTB_BASE_ADDR, MAX_XLAT_TABLES, MAX_MMAP_REGIONS


# =============================================================================
# Memory Attribute Flags 
# =============================================================================

# Memory type (bits [2:0])
Device_nGnRnE = 0 << 0
Device_nGnRE = 1 << 0
Device_nGRE = 2 << 0
Device_GRE = 3 << 0
Normal_inner_noncacheable_outer_noncacheable = 4 << 0
Normal_inner_WBWA_outer_noncacheble = 5 << 0
Normal_inner_WBWA_outer_WBWA = 6 << 0
Normal_inner_noncacheble_outer_WBWA = 7 << 0

# Security (bit 3)
MT_SECURE = 0 << 3
MT_NS = 1 << 3

# Read/Write (bit 4)
MT_RW = 0 << 4
MT_RO = 1 << 4

# Shareability (bits [7:6])
N_Shareable = 0 << 6
Outer_Shareable = 2 << 6
Inner_Shareable = 3 << 6

# Global/Non-Global (bit 8)
MT_Global = 0 << 8
MT_nG = 1 << 8

# PXN/XN (bits 9-10)
nPXN = 0 << 9
PXN = 1 << 9
nXN = 0 << 10
XN = 1 << 10

# Table-level PXN/XN attributes
nPXN_TABLE_LV2 = 0 << 11
PXN_TABLE_LV2 = 1 << 11
nXN_TABLE_LV2 = 0 << 12
XN_TABLE_LV2 = 1 << 12
nPXN_TABLE_LV1 = 0 << 13
PXN_TABLE_LV1 = 1 << 13
nXN_TABLE_LV1 = 0 << 14
XN_TABLE_LV1 = 1 << 14
nPXN_TABLE_LV0 = 0 << 15
PXN_TABLE_LV0 = 1 << 15
nXN_TABLE_LV0 = 0 << 16
XN_TABLE_LV0 = 1 << 16


# =============================================================================
# Architecture Constants
# =============================================================================

# Block sizes
Block_4KB = 0x0000000000001000
Block_2MB = 0x0000000000200000
Block_1GB = 0x0000000040000000
Block_16KB = 0x0000000000004000
Block_32MB = 0x0000000002000000
Block_64GB = 0x0000001000000000
Block_64KB = 0x0000000000010000
Block_512MB = 0x0000000020000000

UNSET_DESC = 0xFFFFFFFFFFFFFFFF
ADDR_SPACE_SIZE = 1 << 32

# Descriptor types
INVALID_DESC = 0x0
BLOCK_DESC = 0x1
TABLE_DESC = 0x3

# Shifts
SHIFT_4KB = 12
SHIFT_16KB = 14
SHIFT_64KB = 16

PXN_SHIFT = 53
XN_SHIFT = 54
PXN_TABLE_SHIFT = 59
XN_TABLE_SHIFT = 60

# AP bits
AP_RO = 0x1 << 5
AP_RW = 0x0 << 5
NS = 0x1 << 3
NG = 0x1 << 9
ACCESS_FLAG = 1 << 8

# Granule-dependent constants
if GRANULES_4KB:
    PAGE_SIZE_SHIFT = SHIFT_4KB
    TG0_bit = 0
    TG1_bit = 2
    L0_XLAT_ADDRESS_SHIFT = 39
elif GRANULES_16KB:
    PAGE_SIZE_SHIFT = SHIFT_16KB
    TG0_bit = 2
    TG1_bit = 1
    L0_XLAT_ADDRESS_SHIFT = 47
elif GRANULES_64KB:
    PAGE_SIZE_SHIFT = SHIFT_64KB
    TG0_bit = 1
    TG1_bit = 3
    L0_XLAT_ADDRESS_SHIFT = None  # Not used for 64KB

PAGE_SIZE = 1 << PAGE_SIZE_SHIFT
PAGE_SIZE_MASK = PAGE_SIZE - 1

XLAT_ENTRY_SIZE_SHIFT = 3  # Each MMU table entry is 8 bytes (1 << 3)
XLAT_ENTRY_SIZE = 1 << XLAT_ENTRY_SIZE_SHIFT

XLAT_TABLE_SIZE_SHIFT = PAGE_SIZE_SHIFT
XLAT_TABLE_SIZE = 1 << XLAT_TABLE_SIZE_SHIFT

# Values for number of entries in each MMU translation table
XLAT_TABLE_ENTRIES_SHIFT = XLAT_TABLE_SIZE_SHIFT - XLAT_ENTRY_SIZE_SHIFT
XLAT_TABLE_ENTRIES = 1 << XLAT_TABLE_ENTRIES_SHIFT
XLAT_TABLE_ENTRIES_MASK = XLAT_TABLE_ENTRIES - 1

# Values to convert a memory address to an index into a translation table
L3_XLAT_ADDRESS_SHIFT = PAGE_SIZE_SHIFT
L2_XLAT_ADDRESS_SHIFT = L3_XLAT_ADDRESS_SHIFT + XLAT_TABLE_ENTRIES_SHIFT
L1_XLAT_ADDRESS_SHIFT = L2_XLAT_ADDRESS_SHIFT + XLAT_TABLE_ENTRIES_SHIFT

# TCR physical address size bits
TCR_PS_BITS_4GB = 0x0
TCR_PS_BITS_64GB = 0x1
TCR_PS_BITS_1TB = 0x2
TCR_PS_BITS_4TB = 0x3
TCR_PS_BITS_16TB = 0x4
TCR_PS_BITS_256TB = 0x5

ADDR_MASK_48_TO_63 = 0xFFFF000000000000
ADDR_MASK_44_TO_47 = 0x0000F00000000000
ADDR_MASK_42_TO_43 = 0x00000C0000000000
ADDR_MASK_40_TO_41 = 0x0000030000000000
ADDR_MASK_36_TO_39 = 0x000000F000000000
ADDR_MASK_32_TO_35 = 0x0000000F00000000

# TCR field definitions
TCR_RGN_INNER_NC = 0x0 << 8
TCR_RGN_INNER_WBA = 0x1 << 8
TCR_RGN_INNER_WT = 0x2 << 8
TCR_RGN_INNER_WBNA = 0x3 << 8

TCR_RGN_OUTER_NC = 0x0 << 10
TCR_RGN_OUTER_WBA = 0x1 << 10
TCR_RGN_OUTER_WT = 0x2 << 10
TCR_RGN_OUTER_WBNA = 0x3 << 10

TCR_SH_NON_SHAREABLE = 0x0 << 12
TCR_SH_OUTER_SHAREABLE = 0x2 << 12
TCR_SH_INNER_SHAREABLE = 0x3 << 12

# MAIR attribute values
ATTR_DEVICE_NGNRNE = 0x00
ATTR_DEVICE_NGNRE = 0x04
ATTR_DEVICE_NGRE = 0x08
ATTR_DEVICE_GRE = 0x0C
ATTR_NORMAL_INC_ONC = 0x44
ATTR_NORMAL_IWBWA_ONC = 0x4F
ATTR_NORMAL_IWBWA_OWBWC = 0xFF
ATTR_NORMAL_INC_OWBWC = 0xF4

# MAIR attribute indices
ATTR_DEVICE_NGNRNE_INDEX = 0
ATTR_DEVICE_NGNRE_INDEX = 1
ATTR_DEVICE_NGRE_INDEX = 2
ATTR_DEVICE_GRE_INDEX = 3
ATTR_NORMAL_INC_ONC_INDEX = 4
ATTR_NORMAL_IWBWA_ONC_INDEX = 5
ATTR_NORMAL_IWBWA_OWBWC_INDEX = 6
ATTR_NORMAL_INC_OWBWC_INDEX = 7


# =============================================================================
# Helper functions 
# =============================================================================

def LOWER_ATTRS(x):
    return ((x) & 0xFFF) << 2

def INDX_ATTR(x):
    return ((x) & 0x7) << 2

def SH_ATTR(x):
    return ((x) & 0xC0) << 2

def MAIR_ATTR_SET(attr, index):
    return attr << (index << 3)

def IS_PAGE_ALIGNED(addr):
    return (addr & PAGE_SIZE_MASK) == 0

def MASK64(val):
    """Keep value within 64 bits."""
    return val & 0xFFFFFFFFFFFFFFFF


# =============================================================================
# Memory Map Region
# =============================================================================

class MmapRegion:
    """Represents a single memory region with VA, PA, size, and attributes."""

    def __init__(self, base_va=0, base_pa=0, size=0, attr=0):
        self.base_va = base_va
        self.base_pa = base_pa
        self.size = size
        self.attr = attr

    def copy(self):
        return MmapRegion(self.base_va, self.base_pa, self.size, self.attr)

    def __repr__(self):
        return (f"MmapRegion(va=0x{self.base_va:x}, pa=0x{self.base_pa:x}, "
                f"size=0x{self.size:x}, attr=0x{self.attr:x})")


# =============================================================================
# Translation Table Builder
# =============================================================================

class XlatTableBuilder:
    """Builds AArch64 translation tables from a user-defined memory map."""

    def __init__(self):
        self.base_xlation_table = [0] * XLAT_TABLE_ENTRIES
        self.xlat_tables = [[0] * XLAT_TABLE_ENTRIES for _ in range(MAX_XLAT_TABLES)]
        self.next_xlat = 0
        self.max_pa = 0
        self.max_va = 0
        self.min_size = 0
        self.tcr_ps_bits = 0
        self.va_bit = 0
        self.mmap = [MmapRegion() for _ in range(MAX_MMAP_REGIONS + 1)]

    def mmap_add_region(self, base_pa, base_va, size, attr):
        """Insert a memory region into the sorted mmap list."""
        assert IS_PAGE_ALIGNED(base_pa), f"base_pa 0x{base_pa:x} not page aligned"
        assert IS_PAGE_ALIGNED(base_va), f"base_va 0x{base_va:x} not page aligned"
        assert IS_PAGE_ALIGNED(size), f"size 0x{size:x} not page aligned"

        if not size:
            return

        # Find correct place in mmap to insert new region (sorted by base_va)
        idx = 0
        while self.mmap[idx].base_va < base_va and self.mmap[idx].size:
            idx += 1

        # Make room for new region by shifting entries up
        last_idx = len(self.mmap) - 1
        for i in range(last_idx, idx, -1):
            self.mmap[i] = self.mmap[i - 1].copy()

        # Check we haven't lost the empty sentinel
        assert self.mmap[last_idx].size == 0

        self.mmap[idx] = MmapRegion(base_va, base_pa, size, attr)

    def mmap_add(self, user_blocks, add_num):
        """Add multiple user-defined memory regions to the mmap list."""
        for i in range(add_num):
            blk = user_blocks[i]
            self.mmap_add_region(blk.base_pa, blk.base_va, blk.size, blk.attr)

        # Clear remaining entries beyond the added regions
        for i in range(add_num, MAX_MMAP_REGIONS + 1):
            if i < len(self.mmap):
                self.mmap[i] = MmapRegion()

    def _mmap_desc(self, attr, addr_pa, level):
        """Build a block/page descriptor from attributes and physical address."""
        desc = addr_pa

        desc |= TABLE_DESC if level == 3 else BLOCK_DESC

        desc |= INDX_ATTR(attr)

        desc |= LOWER_ATTRS(MT_NS) if (attr & MT_NS) else 0
        desc |= LOWER_ATTRS(AP_RO) if (attr & MT_RO) else 0

        desc |= SH_ATTR(attr)

        desc |= LOWER_ATTRS(ACCESS_FLAG)

        desc |= LOWER_ATTRS(NG) if (attr & MT_nG) else 0

        desc |= (1 << PXN_SHIFT) if (attr & PXN) else 0
        desc |= (1 << XN_SHIFT) if (attr & XN) else 0

        return MASK64(desc)

    def _mmap_region_attr(self, mm_idx, base_va, size):
        """Determine the combined attributes for a region of memory."""
        attr = self.mmap[mm_idx].attr

        while True:
            mm_idx += 1
            mm = self.mmap[mm_idx]

            if not mm.size:
                return attr  # Reached end of list

            if mm.base_va >= base_va + size:
                return attr  # Next region is after area

            if mm.base_va + mm.size <= base_va:
                continue  # Next region already overtaken

            if (mm.attr & attr) == attr:
                continue  # Region doesn't override attribs

            attr &= mm.attr

            if mm.base_va > base_va or mm.base_va + mm.size < base_va + size:
                return -1  # Region doesn't fully cover area

    def _init_xlation_table(self, mm_idx, base_va, table, level):
        """Recursively fill in a translation table level."""
        level_size_shift = (L1_XLAT_ADDRESS_SHIFT -
                            (level - 1) * XLAT_TABLE_ENTRIES_SHIFT)
        level_size = 1 << level_size_shift
        level_index_mask = XLAT_TABLE_ENTRIES_MASK << level_size_shift

        assert level <= 3

        table_idx = 0

        while True:
            desc = UNSET_DESC

            if self.mmap[mm_idx].base_va + self.mmap[mm_idx].size <= base_va:
                # Area now after the region so skip it
                mm_idx += 1
                # In C do-while, continue goes to the bottom condition check
                if not (self.mmap[mm_idx].size and
                        (base_va & level_index_mask)):
                    break
                continue

            if self.mmap[mm_idx].base_va >= base_va + level_size:
                # Next region is after area so nothing to map yet
                desc = INVALID_DESC

            elif (self.mmap[mm_idx].base_va <= base_va and
                  self.mmap[mm_idx].base_va + self.mmap[mm_idx].size >=
                  base_va + level_size):
                # Next region covers all of area
                attr = self._mmap_region_attr(mm_idx, base_va, level_size)
                if attr >= 0:
                    desc = self._mmap_desc(
                        attr,
                        base_va - self.mmap[mm_idx].base_va +
                        self.mmap[mm_idx].base_pa,
                        level
                    )

                assert level > 0, "level 0 has no Block entry"
                if GRANULES_64KB:
                    assert level > 1, "level 1 of 64k granules has no Block entry"

            # else: Next region only partially covers area

            if desc == UNSET_DESC:
                # Area not covered by a region so need finer table
                nn_idx = mm_idx
                new_table_idx = self.next_xlat
                self.next_xlat += 1

                if self.next_xlat >= MAX_XLAT_TABLES:
                    print("error! more translation tables are needed")
                    break

                desc = TABLE_DESC | (TTB_BASE_ADDR +
                                     self.next_xlat * PAGE_SIZE)

                # Recurse to fill in new table
                mm_idx = self._init_xlation_table(
                    mm_idx, base_va,
                    self.xlat_tables[new_table_idx], level + 1
                )

                # Apply table-level PXN/XN attributes
                if level == 0:
                    if self.mmap[nn_idx].attr & PXN_TABLE_LV0:
                        desc |= 1 << PXN_TABLE_SHIFT
                    if self.mmap[nn_idx].attr & XN_TABLE_LV0:
                        desc |= 1 << XN_TABLE_SHIFT
                elif level == 1:
                    if self.mmap[nn_idx].attr & PXN_TABLE_LV1:
                        desc |= 1 << PXN_TABLE_SHIFT
                    if self.mmap[nn_idx].attr & XN_TABLE_LV1:
                        desc |= 1 << XN_TABLE_SHIFT
                elif level == 2:
                    if self.mmap[nn_idx].attr & PXN_TABLE_LV2:
                        desc |= 1 << PXN_TABLE_SHIFT
                    if self.mmap[nn_idx].attr & XN_TABLE_LV2:
                        desc |= 1 << XN_TABLE_SHIFT

                desc = MASK64(desc)

            table[table_idx] = desc
            table_idx += 1
            base_va += level_size

            # do-while condition: mm->size && (base_va & level_index_mask)
            if not (self.mmap[mm_idx].size and (base_va & level_index_mask)):
                break

        return mm_idx

    def _calc_physical_addr_size_bits(self, max_addr):
        """Calculate TCR physical address size bits from max physical address."""
        assert (max_addr & ADDR_MASK_48_TO_63) == 0, \
            "Physical address exceeds 48 bits"

        if max_addr & ADDR_MASK_44_TO_47:
            return TCR_PS_BITS_256TB
        if max_addr & ADDR_MASK_42_TO_43:
            return TCR_PS_BITS_16TB
        if max_addr & ADDR_MASK_40_TO_41:
            return TCR_PS_BITS_4TB
        if max_addr & ADDR_MASK_36_TO_39:
            return TCR_PS_BITS_1TB
        if max_addr & ADDR_MASK_32_TO_35:
            return TCR_PS_BITS_64GB
        return TCR_PS_BITS_4GB

    def _cal_startlevel(self):
        """Calculate the starting translation table level from the memory map."""
        for mm in self.mmap:
            if not mm.size:
                break

            if mm.base_pa > self.max_pa:
                self.max_pa = mm.base_pa

            if mm.base_va + mm.size > self.max_va:
                self.max_va = mm.base_va + mm.size - 1

            if not self.min_size:
                self.min_size = mm.size
            elif mm.size < self.min_size:
                self.min_size = mm.size

        va_region = self.max_va + 1
        self.va_bit = 0

        while va_region:
            self.va_bit += 1
            va_region >>= 1

        start_level = 3 - (self.va_bit - PAGE_SIZE_SHIFT) // \
            XLAT_TABLE_ENTRIES_SHIFT

        if GRANULES_64KB:
            assert start_level > 0

        assert start_level <= 3
        print(f"start level {start_level}")
        return start_level

    def init_xlat_tables(self, user_blocks, mmap_num):
        """Initialize translation tables from user-defined memory map blocks."""
        assert mmap_num <= MAX_MMAP_REGIONS

        self.mmap_add(user_blocks, mmap_num)

        start_level = self._cal_startlevel()

        self._init_xlation_table(0, 0, self.base_xlation_table, start_level)
        self.tcr_ps_bits = self._calc_physical_addr_size_bits(self.max_pa)

    def print_sys_reg(self):
        """Print the system register values (MAIR, TCR, TTBR)."""
        mair = MAIR_ATTR_SET(ATTR_NORMAL_INC_OWBWC, ATTR_NORMAL_INC_OWBWC_INDEX)
        mair |= MAIR_ATTR_SET(ATTR_NORMAL_IWBWA_OWBWC, ATTR_NORMAL_IWBWA_OWBWC_INDEX)
        mair |= MAIR_ATTR_SET(ATTR_NORMAL_IWBWA_ONC, ATTR_NORMAL_IWBWA_ONC_INDEX)
        mair |= MAIR_ATTR_SET(ATTR_NORMAL_INC_ONC, ATTR_NORMAL_INC_ONC_INDEX)
        mair |= MAIR_ATTR_SET(ATTR_DEVICE_GRE, ATTR_DEVICE_GRE_INDEX)
        mair |= MAIR_ATTR_SET(ATTR_DEVICE_NGRE, ATTR_DEVICE_NGRE_INDEX)
        mair |= MAIR_ATTR_SET(ATTR_DEVICE_NGNRE, ATTR_DEVICE_NGNRE_INDEX)
        mair |= MAIR_ATTR_SET(ATTR_DEVICE_NGNRNE, ATTR_DEVICE_NGNRNE_INDEX)

        print(f"MAIR reg value 0x{mair:016x}")

        tcr = (TCR_SH_INNER_SHAREABLE | TCR_RGN_OUTER_WBA |
               TCR_RGN_INNER_WBA |
               ((64 - self.va_bit) << 16) | (64 - self.va_bit) |
               (TG1_bit << 30) | (TG0_bit << 14))

        print(f"TCR reg value 0x{tcr:016x}")

        print(f"TTBR reg value 0x{TTB_BASE_ADDR:016x}")

    def write_ttb_to_file(self, filename="ttb_python.bin"):
        """Write the translation tables to a binary file."""
        try:
            with open(filename, "wb") as f:
                # Write base translation table (one page)
                for entry in self.base_xlation_table:
                    f.write(struct.pack("<Q", MASK64(entry)))

                # Write additional translation tables
                for i in range(self.next_xlat):
                    for entry in self.xlat_tables[i]:
                        f.write(struct.pack("<Q", MASK64(entry)))

            print(f"Translation table written to {filename}")
            return 0
        except IOError:
            print(f"{filename} open failed")
            return -1


# =============================================================================
# Main - User-defined memory map
# =============================================================================

def main():
    from ttb_config import get_user_blocks

    user_block, mmap_num = get_user_blocks()

    builder = XlatTableBuilder()
    builder.init_xlat_tables(user_block, mmap_num)

    builder.print_sys_reg()
    builder.write_ttb_to_file()


if __name__ == "__main__":
    main()
