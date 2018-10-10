//////////////////////////////////////////////////////////////////////////////
// This file is part of 'EPIX Development Firmware'.
// It is subject to the license terms in the LICENSE.txt file found in the 
// top-level directory of this distribution and at: 
//    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
// No part of 'EPIX Development Firmware', including this file, 
// may be copied, modified, propagated, or distributed except according to 
// the terms contained in the LICENSE.txt file.
//////////////////////////////////////////////////////////////////////////////
#define BUS_OFFSET         (0x80000000)


#define SYSTEM_REGS_OFFSET (BUS_OFFSET+0x00100000)
#define SYSTEM_DCDCEN      (SYSTEM_REGS_OFFSET+0x00000004)
#define SYSTEM_ANAEN       (SYSTEM_REGS_OFFSET+0x00000008)
#define SYSTEM_DIGEN       (SYSTEM_REGS_OFFSET+0x0000000C)
#define SYSTEM_VTTEN       (SYSTEM_REGS_OFFSET+0x00000010)
#define SYSTEM_ADCCLKRST   (SYSTEM_REGS_OFFSET+0x00000500)
#define SYSTEM_ADCTESTDONE (SYSTEM_REGS_OFFSET+0x0000050C)
#define SYSTEM_ADCTESTFAIL (SYSTEM_REGS_OFFSET+0x00000510)
#define SYSTEM_ADCCHANFAIL (SYSTEM_REGS_OFFSET+0x00000514)
#define SYSTEM_IDRST       (SYSTEM_REGS_OFFSET+0x00000024)
#define SYSTEM_ASICMASK    (SYSTEM_REGS_OFFSET+0x00000028)


#define ADC0_CFG_OFFSET    (BUS_OFFSET+0x02A00000)
#define ADC1_CFG_OFFSET    (BUS_OFFSET+0x02A00800)
#define ADC2_CFG_OFFSET    (BUS_OFFSET+0x02A01000)
#define ADC3_CFG_OFFSET    (BUS_OFFSET+0x02A01800)
#define ADC4_CFG_OFFSET    (BUS_OFFSET+0x02B00000)
#define ADC5_CFG_OFFSET    (BUS_OFFSET+0x02B00800)
#define ADC6_CFG_OFFSET    (BUS_OFFSET+0x02B01000)
#define ADC7_CFG_OFFSET    (BUS_OFFSET+0x02B01800)
#define ADC8_CFG_OFFSET    (BUS_OFFSET+0x02C00000)
#define ADC9_CFG_OFFSET    (BUS_OFFSET+0x02C00800)

static unsigned int adcPdwnModeAddr[10] = {
   ADC0_CFG_OFFSET+0x20,
   ADC1_CFG_OFFSET+0x20,
   ADC2_CFG_OFFSET+0x20,
   ADC3_CFG_OFFSET+0x20,
   ADC4_CFG_OFFSET+0x20,
   ADC5_CFG_OFFSET+0x20,
   ADC6_CFG_OFFSET+0x20,
   ADC7_CFG_OFFSET+0x20,
   ADC8_CFG_OFFSET+0x20,
   ADC9_CFG_OFFSET+0x20
};

static unsigned int adcOutTestModeAddr[10] = {
   ADC0_CFG_OFFSET+(0x0D*4),
   ADC1_CFG_OFFSET+(0x0D*4),
   ADC2_CFG_OFFSET+(0x0D*4),
   ADC3_CFG_OFFSET+(0x0D*4),
   ADC4_CFG_OFFSET+(0x0D*4),
   ADC5_CFG_OFFSET+(0x0D*4),
   ADC6_CFG_OFFSET+(0x0D*4),
   ADC7_CFG_OFFSET+(0x0D*4),
   ADC8_CFG_OFFSET+(0x0D*4),
   ADC9_CFG_OFFSET+(0x0D*4)
};

static unsigned int adcOutModeAddr[10] = {
   ADC0_CFG_OFFSET+(0x14*4),
   ADC1_CFG_OFFSET+(0x14*4),
   ADC2_CFG_OFFSET+(0x14*4),
   ADC3_CFG_OFFSET+(0x14*4),
   ADC4_CFG_OFFSET+(0x14*4),
   ADC5_CFG_OFFSET+(0x14*4),
   ADC6_CFG_OFFSET+(0x14*4),
   ADC7_CFG_OFFSET+(0x14*4),
   ADC8_CFG_OFFSET+(0x14*4),
   ADC9_CFG_OFFSET+(0x14*4)
};

#define ADC0_RDO_OFFSET    (BUS_OFFSET+0x02000000)
#define ADC1_RDO_OFFSET    (BUS_OFFSET+0x02100000)
#define ADC2_RDO_OFFSET    (BUS_OFFSET+0x02200000)
#define ADC3_RDO_OFFSET    (BUS_OFFSET+0x02300000)
#define ADC4_RDO_OFFSET    (BUS_OFFSET+0x02400000)
#define ADC5_RDO_OFFSET    (BUS_OFFSET+0x02500000)
#define ADC6_RDO_OFFSET    (BUS_OFFSET+0x02600000)
#define ADC7_RDO_OFFSET    (BUS_OFFSET+0x02700000)
#define ADC8_RDO_OFFSET    (BUS_OFFSET+0x02800000)
#define ADC9_RDO_OFFSET    (BUS_OFFSET+0x02900000)

static unsigned int adcDelayAddr[10][9] = {
    {ADC0_RDO_OFFSET+0x20, ADC0_RDO_OFFSET+0x00, ADC0_RDO_OFFSET+0x04, ADC0_RDO_OFFSET+0x08, ADC0_RDO_OFFSET+0x0C, ADC0_RDO_OFFSET+0x10, ADC0_RDO_OFFSET+0x14, ADC0_RDO_OFFSET+0x18, ADC0_RDO_OFFSET+0x1C},
    {ADC1_RDO_OFFSET+0x20, ADC1_RDO_OFFSET+0x00, ADC1_RDO_OFFSET+0x04, ADC1_RDO_OFFSET+0x08, ADC1_RDO_OFFSET+0x0C, ADC1_RDO_OFFSET+0x10, ADC1_RDO_OFFSET+0x14, ADC1_RDO_OFFSET+0x18, ADC1_RDO_OFFSET+0x1C},
    {ADC2_RDO_OFFSET+0x20, ADC2_RDO_OFFSET+0x00, ADC2_RDO_OFFSET+0x04, ADC2_RDO_OFFSET+0x08, ADC2_RDO_OFFSET+0x0C, ADC2_RDO_OFFSET+0x10, ADC2_RDO_OFFSET+0x14, ADC2_RDO_OFFSET+0x18, ADC2_RDO_OFFSET+0x1C},
    {ADC3_RDO_OFFSET+0x20, ADC3_RDO_OFFSET+0x00, ADC3_RDO_OFFSET+0x04, ADC3_RDO_OFFSET+0x08, ADC3_RDO_OFFSET+0x0C, ADC3_RDO_OFFSET+0x10, ADC3_RDO_OFFSET+0x14, ADC3_RDO_OFFSET+0x18, ADC3_RDO_OFFSET+0x1C},
    {ADC4_RDO_OFFSET+0x20, ADC4_RDO_OFFSET+0x00, ADC4_RDO_OFFSET+0x04, ADC4_RDO_OFFSET+0x08, ADC4_RDO_OFFSET+0x0C, ADC4_RDO_OFFSET+0x10, ADC4_RDO_OFFSET+0x14, ADC4_RDO_OFFSET+0x18, ADC4_RDO_OFFSET+0x1C},
    {ADC5_RDO_OFFSET+0x20, ADC5_RDO_OFFSET+0x00, ADC5_RDO_OFFSET+0x04, ADC5_RDO_OFFSET+0x08, ADC5_RDO_OFFSET+0x0C, ADC5_RDO_OFFSET+0x10, ADC5_RDO_OFFSET+0x14, ADC5_RDO_OFFSET+0x18, ADC5_RDO_OFFSET+0x1C},
    {ADC6_RDO_OFFSET+0x20, ADC6_RDO_OFFSET+0x00, ADC6_RDO_OFFSET+0x04, ADC6_RDO_OFFSET+0x08, ADC6_RDO_OFFSET+0x0C, ADC6_RDO_OFFSET+0x10, ADC6_RDO_OFFSET+0x14, ADC6_RDO_OFFSET+0x18, ADC6_RDO_OFFSET+0x1C},
    {ADC7_RDO_OFFSET+0x20, ADC7_RDO_OFFSET+0x00, ADC7_RDO_OFFSET+0x04, ADC7_RDO_OFFSET+0x08, ADC7_RDO_OFFSET+0x0C, ADC7_RDO_OFFSET+0x10, ADC7_RDO_OFFSET+0x14, ADC7_RDO_OFFSET+0x18, ADC7_RDO_OFFSET+0x1C},
    {ADC8_RDO_OFFSET+0x20, ADC8_RDO_OFFSET+0x00, ADC8_RDO_OFFSET+0x04, ADC8_RDO_OFFSET+0x08, ADC8_RDO_OFFSET+0x0C, ADC8_RDO_OFFSET+0x10, ADC8_RDO_OFFSET+0x14, ADC8_RDO_OFFSET+0x18, ADC8_RDO_OFFSET+0x1C},
    {ADC9_RDO_OFFSET+0x20, ADC9_RDO_OFFSET+0x00, ADC9_RDO_OFFSET+0x04, ADC9_RDO_OFFSET+0x08, ADC9_RDO_OFFSET+0x0C, ADC9_RDO_OFFSET+0x10, ADC9_RDO_OFFSET+0x14, ADC9_RDO_OFFSET+0x18, ADC9_RDO_OFFSET+0x1C}
};


#define ASIC00_SACI_OFFSET (BUS_OFFSET+0x04000000)
#define ASIC01_SACI_OFFSET (BUS_OFFSET+0x04400000)
#define ASIC02_SACI_OFFSET (BUS_OFFSET+0x04800000)
#define ASIC03_SACI_OFFSET (BUS_OFFSET+0x04C00000)
#define ASIC04_SACI_OFFSET (BUS_OFFSET+0x05000000)
#define ASIC05_SACI_OFFSET (BUS_OFFSET+0x05400000)
#define ASIC06_SACI_OFFSET (BUS_OFFSET+0x05800000)
#define ASIC07_SACI_OFFSET (BUS_OFFSET+0x05C00000)
#define ASIC08_SACI_OFFSET (BUS_OFFSET+0x06000000)
#define ASIC09_SACI_OFFSET (BUS_OFFSET+0x06400000)
#define ASIC10_SACI_OFFSET (BUS_OFFSET+0x06800000)
#define ASIC11_SACI_OFFSET (BUS_OFFSET+0x06C00000)
#define ASIC12_SACI_OFFSET (BUS_OFFSET+0x07000000)
#define ASIC13_SACI_OFFSET (BUS_OFFSET+0x07400000)
#define ASIC14_SACI_OFFSET (BUS_OFFSET+0x07800000)
#define ASIC15_SACI_OFFSET (BUS_OFFSET+0x07C00000)

static unsigned int  cfg4Asic[16] = {
   ASIC00_SACI_OFFSET+(0x1004<<2),
   ASIC01_SACI_OFFSET+(0x1004<<2),
   ASIC02_SACI_OFFSET+(0x1004<<2),
   ASIC03_SACI_OFFSET+(0x1004<<2),
   ASIC04_SACI_OFFSET+(0x1004<<2),
   ASIC05_SACI_OFFSET+(0x1004<<2),
   ASIC06_SACI_OFFSET+(0x1004<<2),
   ASIC07_SACI_OFFSET+(0x1004<<2),
   ASIC08_SACI_OFFSET+(0x1004<<2),
   ASIC09_SACI_OFFSET+(0x1004<<2),
   ASIC10_SACI_OFFSET+(0x1004<<2),
   ASIC11_SACI_OFFSET+(0x1004<<2),
   ASIC12_SACI_OFFSET+(0x1004<<2),
   ASIC13_SACI_OFFSET+(0x1004<<2),
   ASIC14_SACI_OFFSET+(0x1004<<2),
   ASIC15_SACI_OFFSET+(0x1004<<2)
};

static unsigned int  cfg6Asic[16] = {
   ASIC00_SACI_OFFSET+(0x1006<<2),
   ASIC01_SACI_OFFSET+(0x1006<<2),
   ASIC02_SACI_OFFSET+(0x1006<<2),
   ASIC03_SACI_OFFSET+(0x1006<<2),
   ASIC04_SACI_OFFSET+(0x1006<<2),
   ASIC05_SACI_OFFSET+(0x1006<<2),
   ASIC06_SACI_OFFSET+(0x1006<<2),
   ASIC07_SACI_OFFSET+(0x1006<<2),
   ASIC08_SACI_OFFSET+(0x1006<<2),
   ASIC09_SACI_OFFSET+(0x1006<<2),
   ASIC10_SACI_OFFSET+(0x1006<<2),
   ASIC11_SACI_OFFSET+(0x1006<<2),
   ASIC12_SACI_OFFSET+(0x1006<<2),
   ASIC13_SACI_OFFSET+(0x1006<<2),
   ASIC14_SACI_OFFSET+(0x1006<<2),
   ASIC15_SACI_OFFSET+(0x1006<<2)
};

static unsigned int  cfg10Asic[16] = {
   ASIC00_SACI_OFFSET+(0x1010<<2),
   ASIC01_SACI_OFFSET+(0x1010<<2),
   ASIC02_SACI_OFFSET+(0x1010<<2),
   ASIC03_SACI_OFFSET+(0x1010<<2),
   ASIC04_SACI_OFFSET+(0x1010<<2),
   ASIC05_SACI_OFFSET+(0x1010<<2),
   ASIC06_SACI_OFFSET+(0x1010<<2),
   ASIC07_SACI_OFFSET+(0x1010<<2),
   ASIC08_SACI_OFFSET+(0x1010<<2),
   ASIC09_SACI_OFFSET+(0x1010<<2),
   ASIC10_SACI_OFFSET+(0x1010<<2),
   ASIC11_SACI_OFFSET+(0x1010<<2),
   ASIC12_SACI_OFFSET+(0x1010<<2),
   ASIC13_SACI_OFFSET+(0x1010<<2),
   ASIC14_SACI_OFFSET+(0x1010<<2),
   ASIC15_SACI_OFFSET+(0x1010<<2)
};

#define ADC_TEST_OFFSET    (BUS_OFFSET+0x02D00000)
#define ADC_TEST_CHAN      (ADC_TEST_OFFSET+0x00)
#define ADC_TEST_MASK      (ADC_TEST_OFFSET+0x04)
#define ADC_TEST_PATT      (ADC_TEST_OFFSET+0x08)
#define ADC_TEST_SMPL      (ADC_TEST_OFFSET+0x0C)
#define ADC_TEST_TOUT      (ADC_TEST_OFFSET+0x10)
#define ADC_TEST_REQ       (ADC_TEST_OFFSET+0x14)
#define ADC_TEST_PASS      (ADC_TEST_OFFSET+0x18)
#define ADC_TEST_FAIL      (ADC_TEST_OFFSET+0x1C)
