import magma as m
import os

def DefineDFF(width, pipe_depth, retime_status):
    decl = m.DeclareFromTemplatedVerilogFile('verilog/dff.v', **dict(width = width, pipe_depth = pipe_depth, retime_status = retime_status), type_map={"clk": m.In(m.Clock)})[0]
    with open(f"build/{decl.name}.v", "w") as f:
        f.write(decl.verilog_source)

    return decl

def make_name_dff2(array_size_1, width, pipe_depth, retime_status):
        return (f"DFF2_array_size_1_{array_size_1}"
                f"_width_{width}_"
                f"_pipe_depth_{pipe_depth}_"
                f"_retime_status_{retime_status}")


def DefineDFF2(array_size_1, width, pipe_depth, retime_status):

    class DFF2(m.Circuit):
        name = make_name_dff2(array_size_1, width, pipe_depth, retime_status)

        IO = ["data_in", m.Array(array_size_1, m.In(m.Bits(width))), 
              "clk", m.In(m.Clock), 
              "reset", m.In(m.Reset), 
              "en", m.In(m.Bit), 
              "data_out", m.Array(array_size_1, m.Out(m.Bits(width)))]
        @classmethod
        def definition(io):
            dffs = m.braid(m.map_(DefineDFF(width, pipe_depth, retime_status), array_size_1), joinargs=["data_in", "data_out"], forkargs=["clk", "en", "reset"])
            m.wire(dffs.data_in, io.data_in)
            m.wire(dffs.data_out, io.data_out)
            m.wire(dffs.clk, io.clk)
            m.wire(dffs.en, io.en)
            m.wire(dffs.reset, io.reset)
    return DFF2

def make_name_dff3(array_size_2, array_size_1, width, pipe_depth, retime_status):
        return (f"DFF3_array_size_2_{array_size_2}_"
                f"_array_size_1_{array_size_1}_"
                f"_width_{width}_"
                f"_pipe_depth_{pipe_depth}_"
                f"_retime_status_{retime_status}")

def DefineDFF3(array_size_2, array_size_1, width, pipe_depth, retime_status):

    class DFF3(m.Circuit):
        name = make_name_dff3(array_size_2, array_size_1, width, pipe_depth, retime_status)

        IO = ["data_in", m.Array(array_size_2, m.Array(array_size_1, m.In(m.Bits(width)))), 
              "clk", m.In(m.Clock), 
              "reset", m.In(m.Reset), 
              "en", m.In(m.Bit), 
              "data_out", m.Array(array_size_2, m.Array(array_size_1, m.Out(m.Bits(width))))]
        @classmethod
        def definition(io):
            dffs = m.braid(m.map_(DefineDFF2(array_size_1, width, pipe_depth, retime_status), array_size_2), joinargs=["data_in", "data_out"], forkargs=["clk", "en", "reset"])
            m.wire(dffs.data_in, io.data_in)
            m.wire(dffs.data_out, io.data_out)
            m.wire(dffs.clk, io.clk)
            m.wire(dffs.en, io.en)
            m.wire(dffs.reset, io.reset)
    return DFF3
