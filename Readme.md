The project aims to create aarch64 Translation table binary file, which can be used to build the translation table for SoC verification.
The required memory mapping and memory attribute can be simplely specified in "user_block" in ttb_config.py, then run the script.

You also need to specify the Translation table base address in TTB_BASE_ADDR, it is where you want to put the generation translation table.
4KB, 16KB and 64KB granule is supported, select one of them with GRANULES_4KB, GRANULES_16KB or GRANULES_64KB in ttb_config.py.
You can set the max input regions in "user_block" with MAX_MMAP_REGIONS.
If the number of translation tables including Level1, level2, level3 tables required exceeds MAX_XLAT_TABLES, you will need to adjust it.

The program calcuates the best translation lookup start level by going through all input memory regions, to reduce possible translation levels.
When building translation table, it tries block mapping first, if the input memory region or remaining memory region is smaller than a block, next level page or block mapping is used.

The program output a translation table binary along with MMU register settings. For example,
```text
start level 1
MAIR reg value 0xf4ff4f440c080400
TCR reg value 0x0000000080203520
TTBR reg value 0x0000000080010000
Translation table written to ttb.bin
```

The example assembly code to use those value to setup MMU registers is provided in ttb_setup.s


## Test

With the example mapping in user_block
```C
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
```

With debugger tools to dump the translation table and mapping, we can confirm that the translation table generated is correct.

``` text
Input Address   | Type           | Next Level            | Output Address        | Properties
-------------------------------------------------------------------------------------------------------------------------------------------------
+ 0x00000000    | TTBR0_EL3      | SP:0x0000000080010000 |                       | TBI=0, PS=4GB, TG0=4KB, SH0=0x3, ORGN0=0x1, IRGN0=0x1, T0SZ=32
 + 0x00000000   | Level 1 Table  | SP:0x0000000080011000 |                       | NSTable=0, APTable=0x0, XNTable=0, PXNTable=0
  - 0x00000000  | Invalid (x224) |                       |                       | 
  + 0x1C000000  | Level 2 Table  | SP:0x0000000080012000 |                       | NSTable=0, APTable=0x0, XNTable=0, PXNTable=0
   - 0x1C000000 | Level 3 Page   |                       | NP:0x000000001C000000 | XN=0, Contiguous=0, AF=1, SH=0x2, AP=0x0, NS=1, AttrIndx=0x4
   - 0x1C001000 | Level 3 Page   |                       | NP:0x000000001C001000 | XN=0, Contiguous=0, AF=1, SH=0x2, AP=0x0, NS=1, AttrIndx=0x4
   - 0x1C002000 | Level 3 Page   |                       | NP:0x000000001C002000 | XN=0, Contiguous=0, AF=1, SH=0x2, AP=0x0, NS=1, AttrIndx=0x4
   - 0x1C003000 | Level 3 Page   |                       | NP:0x000000001C003000 | XN=0, Contiguous=0, AF=1, SH=0x2, AP=0x0, NS=1, AttrIndx=0x4
   - 0x1C004000 | Level 3 Page   |                       | NP:0x000000001C004000 | XN=0, Contiguous=0, AF=1, SH=0x2, AP=0x0, NS=1, AttrIndx=0x4
   - 0x1C005000 | Level 3 Page   |                       | NP:0x000000001C005000 | XN=0, Contiguous=0, AF=1, SH=0x2, AP=0x0, NS=1, AttrIndx=0x4
   - 0x1C006000 | Level 3 Page   |                       | NP:0x000000001C006000 | XN=0, Contiguous=0, AF=1, SH=0x2, AP=0x0, NS=1, AttrIndx=0x4
   - 0x1C007000 | Level 3 Page   |                       | NP:0x000000001C007000 | XN=0, Contiguous=0, AF=1, SH=0x2, AP=0x0, NS=1, AttrIndx=0x4
   - 0x1C008000 | Level 3 Page   |                       | NP:0x000000001C008000 | XN=0, Contiguous=0, AF=1, SH=0x2, AP=0x0, NS=1, AttrIndx=0x4
   - 0x1C009000 | Invalid (x503) |                       |                       | 
  - 0x1C200000  | Invalid (x151) |                       |                       | 
  + 0x2F000000  | Level 2 Table  | SP:0x0000000080013000 |                       | NSTable=0, APTable=0x0, XNTable=1, PXNTable=1
   - 0x2F000000 | Level 3 Page   |                       | SP:0x000000002F000000 | XN=1, Contiguous=0, AF=1, SH=0x3, AP=0x0, NS=0, AttrIndx=0x6
   - 0x2F001000 | Level 3 Page   |                       | SP:0x000000002F001000 | XN=1, Contiguous=0, AF=1, SH=0x3, AP=0x0, NS=0, AttrIndx=0x6
   - 0x2F002000 | Level 3 Page   |                       | SP:0x000000002F002000 | XN=1, Contiguous=0, AF=1, SH=0x3, AP=0x0, NS=0, AttrIndx=0x6
   - 0x2F003000 | Level 3 Page   |                       | SP:0x000000002F003000 | XN=1, Contiguous=0, AF=1, SH=0x3, AP=0x0, NS=0, AttrIndx=0x6
   - 0x2F004000 | Level 3 Page   |                       | SP:0x000000002F004000 | XN=1, Contiguous=0, AF=1, SH=0x3, AP=0x0, NS=0, AttrIndx=0x6
   - 0x2F005000 | Level 3 Page   |                       | SP:0x000000002F005000 | XN=1, Contiguous=0, AF=1, SH=0x3, AP=0x0, NS=0, AttrIndx=0x6
   - 0x2F006000 | Level 3 Page   |                       | SP:0x000000002F006000 | XN=1, Contiguous=0, AF=1, SH=0x3, AP=0x0, NS=0, AttrIndx=0x6
   - 0x2F007000 | Level 3 Page   |                       | SP:0x000000002F007000 | XN=1, Contiguous=0, AF=1, SH=0x3, AP=0x0, NS=0, AttrIndx=0x6
   - 0x2F008000 | Invalid (x248) |                       |                       | 
   - 0x2F100000 | Level 3 Page   |                       | NP:0x000000002F100000 | XN=0, Contiguous=0, AF=1, SH=0x3, AP=0x2, NS=1, AttrIndx=0x2
   - 0x2F101000 | Level 3 Page   |                       | NP:0x000000002F101000 | XN=0, Contiguous=0, AF=1, SH=0x3, AP=0x2, NS=1, AttrIndx=0x2
   - 0x2F102000 | Level 3 Page   |                       | NP:0x000000002F102000 | XN=0, Contiguous=0, AF=1, SH=0x3, AP=0x2, NS=1, AttrIndx=0x2
   - 0x2F103000 | Level 3 Page   |                       | NP:0x000000002F103000 | XN=0, Contiguous=0, AF=1, SH=0x3, AP=0x2, NS=1, AttrIndx=0x2
   - 0x2F104000 | Level 3 Page   |                       | NP:0x000000002F104000 | XN=0, Contiguous=0, AF=1, SH=0x3, AP=0x2, NS=1, AttrIndx=0x2
   - 0x2F105000 | Level 3 Page   |                       | NP:0x000000002F105000 | XN=0, Contiguous=0, AF=1, SH=0x3, AP=0x2, NS=1, AttrIndx=0x2
   - 0x2F106000 | Level 3 Page   |                       | NP:0x000000002F106000 | XN=0, Contiguous=0, AF=1, SH=0x3, AP=0x2, NS=1, AttrIndx=0x2
   - 0x2F107000 | Level 3 Page   |                       | NP:0x000000002F107000 | XN=0, Contiguous=0, AF=1, SH=0x3, AP=0x2, NS=1, AttrIndx=0x2
   - 0x2F108000 | Invalid (x248) |                       |                       | 
  - 0x2F200000  | Invalid (x135) |                       |                       | 
 - 0x40000000   | Invalid        |                       |                       | 
 - 0x80000000   | Level 1 Block  |                       | NP:0x0000000080000000 | XN=0, Contiguous=0, AF=1, SH=0x2, AP=0x0, NS=1, AttrIndx=0x4
 - 0xC0000000   | Invalid        |                       |                       | 
 ```
 
 
 
 ```text
 	EL3:0x00000000-0x1BFFFFFF	<unmapped>					
	EL3:0x1C000000-0x1C008FFF	NP:0x1C000000-0x1C008FFF	Normal	RW			
	EL3:0x1C009000-0x2EFFFFFF	<unmapped>					
	EL3:0x2F000000-0x2F007FFF	SP:0x2F000000-0x2F007FFF	Normal	RW			
	EL3:0x2F008000-0x2F0FFFFF	<unmapped>					
	EL3:0x2F100000-0x2F107FFF	NP:0x2F100000-0x2F107FFF	Device-nGRE	RO			
	EL3:0x2F108000-0x7FFFFFFF	<unmapped>					
	EL3:0x80000000-0xBFFFFFFF	NP:0x80000000-0xBFFFFFFF	Normal	RW			
	EL3:0xC0000000-0xFFFFFFFF	<unmapped>					
```