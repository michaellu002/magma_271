import magma as m
m.set_mantle_target("coreir")
from mantle import *
import fault
from bit_vector import BitVector

import dff
from rast_types import *
import tester

def define_sampletest(integer_bits, fractional_bits, vertices, axes, color_channels, pipe_depth):
    
    bits = integer_bits + fractional_bits
    
    assert(vertices >= 3)   
    assert(axes >= 2)
    assert(pipe_depth >= 1)
    assert(integer_bits >= 1)
    assert(fractional_bits >= 0)

    class SampleTest(m.Circuit):
        IO = ["CLK", m.In(m.Clock),
              "RESET", m.In(m.Reset),
              "poly", m.In(Polygon(vertices, axes, bits)),
              "color_in", m.In(Colors(color_channels, bits)),
              "is_quad_in", m.In(m.Bits(1)),
              "sample", m.In(Point(2, bits)),
              "valid_sample", m.In(m.Bits(1)),
              "hit", m.Out(Point(axes, bits)), 
              "valid_hit", m.Out(m.Bits(1)),
              "color_out", m.Out(Colors(color_channels, bits))]

        @classmethod
        def definition(io):
            # -------------------
            # Your code goes here
            # -------------------
            # You may define any combinational functions you may need
            # Finally, assign values to
            #   valid_hit
            #   hit
            # These signals feed into the pipeline registers
            









            # -------------------
            # Your code goes here
            # -------------------

            # Put values into pipeline registers
            def wire_reg (reg, reg_input, reg_output=None):
                m.wire(reg_input, reg.data_in)
                m.wire(reg.clk, io.CLK)
                m.wire(reg.reset, io.RESET)
                m.wire(reg.en, m.bit(1))
                if reg_output is not None:
                    m.wire(reg.data_out, reg_output)
            
            hit_retime_r = dff.DefineDFF2(axes, bits, pipe_depth - 1, 1)()
            wire_reg(hit_retime_r, hit)

            hit_r = dff.DefineDFF2(axes, bits, 1, 0)()
            wire_reg(hit_r, hit_retime_r.data_out, io.hit)

            color_retime_r = dff.DefineDFF2(color_channels, bits, pipe_depth - 1, 1)()
            wire_reg(color_retime_r, io.color_in)

            color_r = dff.DefineDFF2(color_channels, bits, 1, 0)()
            wire_reg(color_r, color_retime_r.data_out, io.color_out)

            valid_hit_retime_r = dff.DefineDFF(1, pipe_depth - 1, 1)()
            wire_reg(valid_hit_retime_r, m.bits(valid_hit))

            valid_hit_r = dff.DefineDFF(1, 1, 0)()
            wire_reg(valid_hit_r, valid_hit_retime_r.data_out, io.valid_hit)
    
    return SampleTest

def define_dut():
    integer_bits = 14
    fractional_bits = 10
    vertices = 3
    axes = 3
    color_channels = 3
    pipe_depth = 2

    dut = define_sampletest(integer_bits, fractional_bits, vertices, axes, color_channels, pipe_depth)
    return dut

def test_dut():
    dut = define_dut()
    m.compile('build/' + dut.name, dut, output="coreir-verilog")
    #testbench = tester.Tester(dut, tester.pack_vectors(dut, dut.name + '_vector.json', 10000))
    #testbench.compile_and_run(directory="build", target="verilator", flags=["-Wno-fatal", '--trace'])

#test_dut()
