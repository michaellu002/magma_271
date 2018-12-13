import magma as m
m.set_mantle_target("coreir")
from mantle import Register
from magma import DefineCircuit, DeclareCircuit, Array, In, SInt, Out, wire, EndCircuit
import fault
from bit_vector import BitVector

import dff
from rast_types import *
import tester

IteratorState = m.Enum(WAIT_STATE = 0, TEST_STATE = 1)

def define_iterator(integer_bits, fractional_bits, vertices, axes, color_channels, modified_fsm):
    
    bits = integer_bits + fractional_bits
    
    assert(vertices >= 3)   
    assert(axes >= 2)
    assert(integer_bits >= 1)
    assert(fractional_bits >= 0)
    assert(modified_fsm in [0, 1])

    class Iterator(m.Circuit):
        IO = ["CLK", m.In(m.Clock),
              "RESET", m.In(m.Reset),
              "poly_in", m.In(Polygon(vertices, axes, bits)),
              "color_in", m.In(Colors(color_channels, bits)),
              "valid_in", m.In(m.Bits(1)),
              "is_quad_in", m.In(m.Bits(1)),
              "box", m.In(Polygon(2, 2, bits)),
              "sample_size", m.In(SampleSize),
              "halt", m.Out(m.Bits(1)),
              "poly_out", m.Out(Polygon(vertices, axes, bits)),
              "color_out", m.Out(Colors(color_channels, bits)),
              "is_quad_out", m.Out(m.Bits(1)),
              "sample", m.Out(Point(2, bits)),
              "valid_sample", m.Out(m.Bits(1))]
       
        @classmethod
        def definition(io):
            def wire_reg (reg, reg_input, reg_output=None):
                m.wire(reg_input, reg.data_in)
                m.wire(reg.clk, io.CLK)
                m.wire(reg.reset, io.RESET)
                m.wire(reg.en, 1)
                if reg_output is not None:
                    m.wire(reg.data_out, reg_output)

            box_r = dff.DefineDFF3(2, 2, bits, 1, 0)()
            state_r = dff.DefineDFF(1, 1, 0)()
            poly_r = dff.DefineDFF3(axes, vertices, bits, 1, 0)()
            color_r = dff.DefineDFF2(color_channels, bits, 1, 0)()
            sample_r = dff.DefineDFF2(2, bits, 1, 0)()
            valid_sample_r = dff.DefineDFF(1, 1, 0)()
            is_quad_r = dff.DefineDFF(1, 1, 0)()
            halt_r = dff.DefineDFF(1, 1, 0)()

            # -------------------
            # Your code goes here
            # -------------------
            # You may define any combinational functions you may need
            # Finally, assign values to
            #   next_box
            #   next_state
            #   next_poly
            #   next_color
            #   next_sample
            #   next_valid_sample
            #   next_is_quad
            #   next_halt 
            # These signals feed into the pipeline registers










            # -------------------
            # Your code goes here
            # -------------------

            # Put values into pipeline registers
            wire_reg(box_r, next_box)
            wire_reg(state_r, next_state)
            wire_reg(poly_r, next_poly, io.poly_out)
            wire_reg(color_r, next_color, io.color_out)
            wire_reg(sample_r, next_sample, io.sample)
            wire_reg(valid_sample_r, next_valid_sample, io.valid_sample)
            wire_reg(is_quad_r, next_is_quad, io.is_quad_out)
            wire_reg(halt_r, next_halt, io.halt)
        
    return Iterator

def define_dut():
    integer_bits = 14
    fractional_bits = 10
    vertices = 3
    axes = 3
    color_channels = 3
    modified_fsm = 0
    
    dut = define_iterator(integer_bits, fractional_bits, vertices, axes, color_channels, modified_fsm)
 
    return dut

def test_dut():
    dut = define_dut()
    m.compile('build/' + dut.name, dut, output="coreir-verilog")
    #testbench = tester.Tester(dut, tester.pack_vectors(dut, dut.name + '_vector.json', 10000))
    #testbench.compile_and_run(directory="build", target="verilator", flags=["-Wno-fatal", '--trace'])

#test_dut()
