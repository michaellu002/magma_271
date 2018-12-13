import magma as m
m.set_mantle_target("coreir")
from mantle import Register
from magma import DefineCircuit, DeclareCircuit, Array, In, SInt, Out, wire, EndCircuit
import fault
from bit_vector import BitVector
import sys
import mantle

import dff 
from rast_types import *
import tester

def define_compute_bounding_box(integer_bits, fractional_bits, vertices, axes, color_channels, pipe_depth):
    
    bits = integer_bits + fractional_bits
    
    assert(vertices == 3)   
    assert(axes >= 2)
    assert(pipe_depth >= 1)
    assert(integer_bits >= 1)
    assert(fractional_bits >= 0)

    class ComputeBoundingBox(m.Circuit):

        IO = ["RESET", m.In(m.Reset),
              "valid_in", m.In(m.Bits(1)),
              "poly_in", m.In(Polygon(vertices, axes, bits)),
              "color_in", m.In(Colors(color_channels, bits)),
              "screen_max", m.In(Point(2, bits)),
              "sample_size", m.In(SampleSize),
              "halt", m.In(m.Bits(1)),
              "valid_out", m.Out(m.Bits(1)),
              "poly_out", m.Out(Polygon(vertices, axes, bits)), 
              "color_out", m.Out(Colors(color_channels, bits)),
              "box", m.Out(Polygon(2, 2, bits)),
              "is_quad_in", m.In(m.Bits(1)),
              "is_quad_out", m.Out(m.Bits(1)),
              "CLK", m.In(m.Clock)]
        
        @m.circuit.combinational
        def return_ll_ur(I: m.Bits(3), S: m.Bit) -> (m.Bits(bits), m.Bits(bits)):
            if ~I[0]:
                if ~I[1]:
                    if ~I[2]:
                        ll = io.poly_in[2][S];
                        ur = io.poly_in[0][S];
                    else:
                        ll = io.poly_in[2][S];
                        ur = io.poly_in[0][S];
                else:
                    if ~I[2]: 
                        ll = io.poly_in[1][S];
                        ur = io.poly_in[0][S];
                    else:
                        ll = io.poly_in[1][S];
                        ur = io.poly_in[2][S];
            else:
                if ~I[1]:
                    if ~I[2]:
                        ll = io.poly_in[2][S];
                        ur = io.poly_in[1][S];
                    else:
                        ll = io.poly_in[0][S];
                        ur = io.poly_in[1][S];
                else:
                    if ~I[2]:
                        ll = io.poly_in[0][S];
                        ur = io.poly_in[2][S];
                    else:
                        ll = io.poly_in[0][S];
                        ur = io.poly_in[2][S];

            return ll, ur
        
        @m.circuit.combinational
        def get_hash_mask(sample_size : SampleSize) -> (m.Bits(4)):
            if sample_size == SampleSize.ONE_PIXEL:
                hash_mask = m.repeat(m.bit(0), 4)
            elif sample_size == SampleSize.HALF_PIXEL:
                hash_mask = m.concat(m.bit(1), m.repeat(m.bit(0), 3));
            elif sample_size == SampleSize.QUARTER_PIXEL:
                hash_mask = m.concat(m.repeat(m.bit(1), 2), m.repeat(m.bit(0), 2));
            else:
                hash_mask = m.concat(m.repeat(m.bit(1), 3), m.bit(0));

            return (hash_mask)

        @classmethod
        def definition(io):
            # -------------------
            # Your code goes here
            # -------------------
            # You may define any combinational functions you may need
            # Finally, assign values to
            #   box_clamped
            #   box_valid
            # These signals feed into the pipeline registers

            x_comp = m.concat(\
                    m.bits(io.poly_in[0][0]) <= m.bits(io.poly_in[1][0]), \
                    m.bits(io.poly_in[1][0]) <= m.bits(io.poly_in[2][0]), \
                    m.bits(io.poly_in[0][0]) <= m.bits(io.poly_in[2][0]))
            
            y_comp = m.concat(\
                    m.bits(io.poly_in[0][1]) <= m.bits(io.poly_in[1][1]), \
                    m.bits(io.poly_in[1][1]) <= m.bits(io.poly_in[2][1]), \
                    m.bits(io.poly_in[0][1]) <= m.bits(io.poly_in[2][1]))

            (ll_x, ur_x) = io.return_ll_ur(x_comp, m.bit(0))
            (ll_y, ur_y) = io.return_ll_ur(y_comp, m.bit(1))

            (hash_mask) = io.get_hash_mask(io.sample_size)
            
            box_init = Polygon(2, 2, bits)
            rounded_box = Polygon(2, 2, bits)
            box_clamped = Polygon(2, 2, bits)
            box_init[0][0] = ll_x
            box_init[1][0] = ur_x
            box_init[0][1] = ll_y
            box_init[1][1] = ur_y

            m.wire(box_init[0][0][fractional_bits:bits-1], rounded_box[0][0][fractional_bits:bits-1])  
            m.wire(box_init[0][1][fractional_bits:bits-1], rounded_box[0][1][fractional_bits:bits-1]) 
            m.wire(box_init[1][0][fractional_bits:bits-1], rounded_box[1][0][fractional_bits:bits-1]) 
            m.wire(box_init[1][1][fractional_bits:bits-1], rounded_box[1][1][fractional_bits:bits-1]) 

            m.wire(box_init[0][0][0:fractional_bits-1], m.concat(m.repeat(m.bit(0), 6), (rounded_box[0][0][6:fractional_bits-1] & hash_mask))) 
            m.wire(box_init[0][1][0:fractional_bits-1], m.concat(m.repeat(m.bit(0), 6), (rounded_box[0][1][6:fractional_bits-1] & hash_mask))) 
            m.wire(box_init[1][0][0:fractional_bits-1], m.concat(m.repeat(m.bit(0), 6), (rounded_box[1][0][6:fractional_bits-1] & hash_mask))) 
            m.wire(box_init[1][1][0:fractional_bits-1], m.concat(m.repeat(m.bit(0), 6), (rounded_box[1][1][6:fractional_bits-1] & hash_mask))) 

            box_clamped[0][0] = mux(rounded_box[0][0], m.repeat(m.bit(0), bits), (rounded_box[0][0] < 0))
            box_clamped[1][0] = mux(rounded_box[1][0], io.screen_max[0], (rounded_box[1][0] > io.screen_max[0]))
            box_clamped[0][1] = mux(rounded_box[0][1], m.repeat(m.bit(0), bits), (rounded_box[0][1] < 0))
            box_clamped[1][1] = mux(rounded_box[1][1], io.screen_max[1], (rounded_box[1][1] > io.screen_max[1]))

            box_valid = io.valid_in & ~((rounded_box[0][0] < 0) | (rounded_box[1][0] > io.screen_max[0]) | (rounded_box[0][1] < 0) | (rounded_box[1][1] > io.screen_max[1]))
            # -------------------
            # Your code goes here
            # -------------------

            # Put values into pipeline registers
            def wire_reg (reg, reg_input, reg_output=None):
                m.wire(reg_input, reg.data_in)
                m.wire(reg.clk,io.CLK)
                m.wire(reg.reset, io.RESET)
                m.wire(reg.en, io.halt[0])
                if reg_output is not None:
                    m.wire(reg.data_out, reg_output)
            
            poly_retime_r = dff.DefineDFF3(axes, vertices, bits, pipe_depth - 1, 1)()
            wire_reg(poly_retime_r, io.poly_in)
            
            poly_r = dff.DefineDFF3(axes, vertices, bits, 1, 0)()
            wire_reg(poly_r, poly_retime_r.data_out, io.poly_out)
            
            color_retime_r = dff.DefineDFF2(color_channels, bits, pipe_depth - 1, 1)()
            wire_reg(color_retime_r, io.color_in)

            color_r = dff.DefineDFF2(color_channels, bits, 1, 0)()
            wire_reg(color_r, color_retime_r.data_out, io.color_out)

            box_retime_r = dff.DefineDFF3(2, 2, bits, pipe_depth - 1, 1)()
            wire_reg(box_retime_r, box_clamped)
            
            box_r = dff.DefineDFF3(2, 2, bits, 1, 0)()
            wire_reg(box_r, box_retime_r.data_out, io.box)
 
            valid_retime_r = dff.DefineDFF(1, pipe_depth - 1, 1)()
            wire_reg(valid_retime_r, box_valid)

            valid_r = dff.DefineDFF(1, 1, 0)()
            wire_reg(valid_r, valid_retime_r.data_out, io.valid_out)

            is_quad_retime_r = dff.DefineDFF(1, pipe_depth - 1, 1)()
            wire_reg(is_quad_retime_r, m.bits(io.is_quad_in))

            is_quad_r = dff.DefineDFF(1, 1, 0)()
            wire_reg(is_quad_r, is_quad_retime_r.data_out, m.bits(io.is_quad_out))

    return ComputeBoundingBox

def define_dut():
    integer_bits = 14
    fractional_bits = 10
    vertices = 3
    axes = 3
    color_channels = 3
    pipe_depth = 3

    dut = define_compute_bounding_box(integer_bits, fractional_bits, vertices, axes, color_channels, pipe_depth)
    return dut

def test_dut():
    dut = define_dut()
    m.compile('build/' + dut.name, dut, output="coreir-verilog")
    #testbench = tester.Tester(dut, tester.pack_vectors(dut, dut.name + '_vector.json', 10000))
    #testbench.compile_and_run(directory="build", target="verilator", flags=["-Wno-fatal", '--trace'])

test_dut()
