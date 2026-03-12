
                // Create page tables
ttb_setup:     
                ADRP X0, ttb0_base        // Load the page address into X0
                ADD X0, X0, :lo12:ttb0_base  // Add the offset within the page

                msr     ttbr0_el3, x0

 
                ADRP X1, tcr_value        // Load the page address into X1
                ADD X1, X1, :lo12:tcr_value  // Add the offset within the page
                ldr x1, [x1]

                msr     TCR_EL3, x1

                ADRP X1, mair_value        // Load the page address into X1
                ADD X1, X1, :lo12:mair_value  // Add the offset within the page
                ldr x1,[x1]

                msr     MAIR_EL3, x1


                // Enable caches and MMU
                mrs     x0, sctlr_el3
                orr     x0, x0, #(0x1 << 2)     // C bit (data cache)
                orr     x0, x0, #(0x1 << 12)    // I bit (instruction cache)
                orr     x0, x0, #0x1            // M bit (MMU)
                msr     sctlr_el3, x0
                isb







      .align 3

mair_value:
        .quad  0xf4ff4f440c080400

tcr_value:
        .quad  0x801f351f
		
      .end
