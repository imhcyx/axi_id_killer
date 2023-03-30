import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

from cocotbext.axi import AxiBus, AxiMaster, AxiRam
from cocotbext.axi.constants import AxiBurstType

class TB:
    def __init__(self, dut):
        self.dut = dut
        cocotb.fork(Clock(dut.aclk, 10, units='ns').start())
        self.axi_master = AxiMaster(AxiBus.from_prefix(dut, 's_axi'), dut.aclk, dut.aresetn, reset_active_level=False)
        self.axi_ram = AxiRam(AxiBus.from_prefix(dut, 'm_axi'), dut.aclk, dut.aresetn, reset_active_level=False, size=0x10000)

@cocotb.test()
async def run_test(dut):
    tb = TB(dut)

    dut.aresetn = 0
    await ClockCycles(dut.aclk, 10)
    dut.aresetn = 1

    async def read_write_worker_func():
        for step in range(0, 100):
            burst = AxiBurstType.INCR
            size = random.randint(0, 3)
            addr = (2 ** size) * random.randint(0, 16)
            length = random.randint(1, 0x100)
            test_data = bytearray([x % 256 for x in range(length)])
            dut._log.info("STEP %d: address=0x%x, length=0x%x, axsize=%d axburst=%s" %
                          (step, addr, length, size, burst))
            await tb.axi_master.write(addr, test_data, burst=burst, size=size)
            data = await tb.axi_master.read(addr, length, burst=burst, size=size)
            assert data.data == test_data

    await read_write_worker_func()

    await RisingEdge(dut.aclk)
