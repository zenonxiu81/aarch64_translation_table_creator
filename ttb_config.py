#!/usr/bin/env python3
"""
User Configuration for AArch64 Translation Table Creator

Edit this file to configure granule size, TTB base address,
and the memory map regions.

Autor: Zenon Zhilong Xiu
"""

# =============================================================================
# Granule Size Configuration (set exactly one to True)
# =============================================================================
GRANULES_4KB = True
GRANULES_16KB = False
GRANULES_64KB = False

# =============================================================================
# Table Configuration 
# =============================================================================

# Maximum number of translation tables 
MAX_XLAT_TABLES = 16
# Maximum number of memory map regions
MAX_MMAP_REGIONS = 8

# =============================================================================
# TTB Base Address
# =============================================================================
TTB_BASE_ADDR = 0x80010000

# =============================================================================
# User-defined Memory Map Blocks
# =============================================================================
# Import is deferred to avoid circular dependency; the function below
# is called after aarch64_ttb_creator has been loaded.
# import more constants from aarch64_ttb_creator as needed for defining memory map regions.


def get_user_blocks():
    """Return the list of user-defined memory map regions and their count."""
    from aarch64_ttb_creator import (
        MmapRegion,
        Inner_Shareable, Outer_Shareable,
        MT_SECURE, MT_NS, MT_RW, MT_RO, MT_nG, MT_Global,
        Normal_inner_WBWA_outer_WBWA,
        Normal_inner_noncacheable_outer_noncacheable,
        Device_nGRE,
        PXN, nPXN, nXN, XN,
        PXN_TABLE_LV2, XN_TABLE_LV2,
        Block_1GB,
    )

    user_block = [
        MmapRegion(
            0x0000002f000000, 0x0000002f000000, 0x8000,
            Inner_Shareable | MT_SECURE | MT_RW |
            Normal_inner_WBWA_outer_WBWA | PXN_TABLE_LV2 | XN_TABLE_LV2 | XN | MT_Global
        ),  # RAM

        MmapRegion(
            0x0000002f100000, 0x0000002f100000, 0x8000,
            PXN | nXN | MT_nG | MT_NS | MT_RO | Inner_Shareable | Device_nGRE
        ),  # GIC

        MmapRegion(
            0x1c000000, 0x1c000000, 0x9000,
            nPXN | nXN | MT_nG | MT_NS | MT_RW | Normal_inner_noncacheable_outer_noncacheable | Outer_Shareable
        ),  #SRAM

        MmapRegion(
            0x0000000080000000, 0x0000000080000000, Block_1GB,
            nPXN | nXN | MT_nG | MT_NS | MT_RW | Normal_inner_noncacheable_outer_noncacheable | Outer_Shareable
        ),  
    ]

    return user_block, len(user_block)
