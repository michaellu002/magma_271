import magma as m
m.set_mantle_target("coreir")
from mantle import Register
from magma import DefineCircuit, DeclareCircuit, Array, In, SInt, Out, wire, EndCircuit
import fault
from bit_vector import BitVector

import dff 
from rast_types import *
from tree_hash import *
import tester

def define_hash_jtree(integer_bits, fractional_bits, vertices, axes, color_channels, pipe_depth):
    
    bits = integer_bits + fractional_bits
    
    assert(vertices >= 3)   
    assert(axes >= 2)
    assert(pipe_depth >= 1)
    assert(integer_bits >= 1)
    assert(fractional_bits >= 0)

    class HashJTree(m.Circuit):
        IO = ["CLK", m.In(m.Clock),
              "RESET", m.In(m.Reset),
              "poly_in", m.In(Polygon(vertices, axes, bits)),
              "color_in", m.In(Colors(color_channels, bits)),
              "is_quad_in", m.In(m.Bits(1)),
              "sample_in", m.In(Point(2, bits)),
              "valid_sample_in", m.In(m.Bits(1)),
              "sample_size", m.In(SampleSize),
              "poly_out", m.Out(Polygon(vertices, axes, bits)),
              "color_out", m.Out(Colors(color_channels, bits)),
              "is_quad_out", m.Out(m.Bits(1)),
              "sample_out", m.Out(Point(2, bits)),
              "valid_sample_out", m.Out(m.Bits(1))]

        @m.circuit.combinational
        def get_hash_mask(sample_size : SampleSize) -> (m.Bits(8)):
            
            if sample_size == SampleSize.ONE_PIXEL:
                hash_mask = m.repeat(m.bit(1), 8)
            elif sample_size == SampleSize.HALF_PIXEL:
                hash_mask = m.concat(m.repeat(m.bit(1), 7), m.repeat(m.bit(0), 1))
            elif sample_size == SampleSize.QUARTER_PIXEL:
                hash_mask = m.concat(m.repeat(m.bit(1), 6), m.repeat(m.bit(0), 2))
            else: #elif sample_size == SampleSize.EIGHTH_PIXEL:
                hash_mask = m.concat(m.repeat(m.bit(1), 5), m.repeat(m.bit(0), 3))

            return (hash_mask)

        @classmethod
        def definition(io):
            hash_in_width = (bits - 4) * 2
            hash_out_width = fractional_bits - 2
            (hash_mask) = io.get_hash_mask(io.sample_size)
            
            jitter = [define_tree_hash(hash_in_width, hash_out_width)() for _ in range(2)]

            subsample1 = io.sample_in[1][4:bits]
            subsample0 = io.sample_in[0][4:bits]

            m.wire(jitter[0].data_in, m.bits(m.concat(subsample0, subsample1)))
            m.wire(jitter[0].mask, hash_mask)
            m.wire(jitter[1].data_in, m.bits(m.concat(subsample1, subsample0)))
            m.wire(jitter[1].mask, hash_mask)

            # Jitter the sample coordinates
            sample_jittered = m.array([m.bits(io.sample_in[i][0:bits]) | m.concat(m.bits(0, fractional_bits - hash_out_width), m.bits(jitter[i].data_out[0:hash_out_width]), m.bits(0, integer_bits)) for i in range(2)])
   
            # Put values into pipeline registers
            def wire_reg (reg, reg_input, reg_output=None):
                m.wire(reg_input, reg.data_in)
                m.wire(reg.clk, io.CLK)
                m.wire(reg.reset, io.RESET)
                m.wire(reg.en, m.bit(1))
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

            is_quad_retime_r = dff.DefineDFF(1, pipe_depth - 1, 1)()
            wire_reg(is_quad_retime_r, m.bits(io.is_quad_in))

            is_quad_r = dff.DefineDFF(1, 1, 0)()
            wire_reg(is_quad_r, is_quad_retime_r.data_out, m.bits(io.is_quad_out))

            valid_sample_retime_r = dff.DefineDFF(1, pipe_depth - 1, 1)()
            wire_reg(valid_sample_retime_r, io.valid_sample_in)

            valid_sample_r = dff.DefineDFF(1, 1, 0)()
            wire_reg(valid_sample_r, valid_sample_retime_r.data_out, io.valid_sample_out)
 
            sample_retime_r = dff.DefineDFF2(2, bits, pipe_depth - 1, 1)()
            wire_reg(sample_retime_r, sample_jittered)

            sample_r = dff.DefineDFF2(2, bits, 1, 0)()
            wire_reg(sample_r, sample_retime_r.data_out, io.sample_out)

    return HashJTree

def define_dut():
    integer_bits = 14
    fractional_bits = 10
    vertices = 3
    axes = 3
    color_channels = 3
    pipe_depth = 2
    
    dut = define_hash_jtree(integer_bits, fractional_bits, vertices, axes, color_channels, pipe_depth)
    return dut

def test_dut():
    dut = define_dut()
    m.compile('build/' + dut.name, dut, output="coreir-verilog")
    #testbench = tester.Tester(dut, tester.pack_vectors(dut, dut.name + '_vector.json', 10000))
    #testbench.compile_and_run(directory="build", target="verilator", flags=["-Wno-fatal", '--trace'])

#test_dut()
