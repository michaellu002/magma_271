import magma as m
m.set_mantle_target("coreir")
from rast_types import *
import bbox
import iterator
import hash_jtree
import sampletest
import tester

def define_rasterizer(integer_bits, fractional_bits, vertices, axes, color_channels, pipe_stages_box, pipe_stages_iter, pipe_stages_hash, pipe_stages_samp, modified_fsm):
    
    bits = integer_bits + fractional_bits
    
    assert(vertices >= 3)   
    assert(axes >= 2)
    assert(pipe_stages_box >= 1)
    assert(pipe_stages_iter >= 1)
    assert(pipe_stages_hash >= 1)
    assert(pipe_stages_samp >= 1)
    assert(integer_bits >= 1)
    assert(fractional_bits >= 0)

    class Rasterizer(m.Circuit):
        IO = ["CLK", m.In(m.Clock),
              "RESET", m.In(m.Reset),
              "valid_in", m.In(m.Bits(1)),
              "poly", m.In(Polygon(vertices, axes, bits)),
              "color_in", m.In(Colors(color_channels, bits)),
              "is_quad", m.In(m.Bits(1)),
              "screen_max", m.In(Point(2, bits)),
              "sample_size", m.In(SampleSize),
              "halt", m.Out(m.Bits(1)),
              "valid_hit", m.Out(m.Bits(1)),
              "hit", m.Out(Point(axes, bits)), 
              "color_out", m.Out(Colors(color_channels, bits))]
         
        @classmethod
        def definition(io):

            bbox_inst = bbox.define_compute_bounding_box(integer_bits, fractional_bits, vertices, axes, color_channels, pipe_stages_box)()
            iterator_inst = iterator.define_iterator(integer_bits, fractional_bits, vertices, axes, color_channels, modified_fsm)()
            hash_jtree_inst = hash_jtree.define_hash_jtree(integer_bits, fractional_bits, vertices, axes, color_channels, pipe_stages_hash)()
            sampletest_inst = sampletest.define_sampletest(integer_bits, fractional_bits, vertices, axes, color_channels, pipe_stages_samp)()

            m.wire(io.CLK, bbox_inst.CLK)
            m.wire(bbox_inst.RESET, io.RESET)
            m.wire(bbox_inst.valid_in, io.valid_in)
            m.wire(bbox_inst.poly_in, io.poly)
            m.wire(bbox_inst.color_in, io.color_in)
            m.wire(bbox_inst.is_quad_in, io.is_quad)
            m.wire(bbox_inst.screen_max, io.screen_max)
            m.wire(bbox_inst.sample_size, io.sample_size)
            m.wire(bbox_inst.halt, iterator_inst.halt)

            m.wire(iterator_inst.CLK, io.CLK)
            m.wire(iterator_inst.RESET, io.RESET)
            m.wire(iterator_inst.poly_in, bbox_inst.poly_out)
            m.wire(iterator_inst.color_in, bbox_inst.color_out)
            m.wire(iterator_inst.valid_in, bbox_inst.valid_out)
            m.wire(iterator_inst.is_quad_in, bbox_inst.is_quad_out)
            m.wire(iterator_inst.sample_size, io.sample_size)
            m.wire(iterator_inst.halt, io.halt)
            m.wire(iterator_inst.box, bbox_inst.box)
            
            m.wire(hash_jtree_inst.CLK, io.CLK)
            m.wire(hash_jtree_inst.RESET, io.RESET)
            m.wire(hash_jtree_inst.poly_in, iterator_inst.poly_out)
            m.wire(hash_jtree_inst.color_in, iterator_inst.color_out)
            m.wire(hash_jtree_inst.is_quad_in, iterator_inst.is_quad_out)
            m.wire(hash_jtree_inst.sample_in, iterator_inst.sample)
            m.wire(hash_jtree_inst.valid_sample_in, iterator_inst.valid_sample)
            m.wire(hash_jtree_inst.sample_size, io.sample_size)

            m.wire(sampletest_inst.CLK, io.CLK)
            m.wire(sampletest_inst.RESET, io.RESET)
            m.wire(sampletest_inst.poly, hash_jtree_inst.poly_out)
            m.wire(sampletest_inst.color_in, hash_jtree_inst.color_out)
            m.wire(sampletest_inst.sample, hash_jtree_inst.sample_out)
            m.wire(sampletest_inst.valid_sample, hash_jtree_inst.valid_sample_out)
            m.wire(sampletest_inst.is_quad_in, hash_jtree_inst.is_quad_out)
            m.wire(sampletest_inst.hit, io.hit)
            m.wire(sampletest_inst.color_out, io.color_out)
            m.wire(sampletest_inst.valid_hit, io.valid_hit)

    return Rasterizer

def define_dut():
    integer_bits = 14
    fractional_bits = 10
    vertices = 3
    axes = 3
    color_channels = 3
    pipe_stages_box = 3
    pipe_stages_iter = 1
    pipe_stages_hash = 2
    pipe_stages_samp = 2
    retime_status = 1
    modified_fsm = 0

    dut = define_rasterizer(integer_bits, fractional_bits, vertices, axes, color_channels, pipe_stages_box, pipe_stages_iter, pipe_stages_hash, pipe_stages_samp, modified_fsm)

    return dut

def test_dut():
    dut = define_dut()
    m.compile('build/' + dut.name, dut, output="coreir-verilog")

test_dut()
