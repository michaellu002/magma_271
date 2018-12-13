import magma as m
m.set_mantle_target("coreir")

def define_tree_hash(in_width, out_width):
    class TreeHash(m.Circuit):
        IO = ["data_in", m.In(m.Bits(in_width)),
              "mask", m.In(m.Bits(out_width)),
              "data_out", m.Out(m.Bits(out_width))]

        @classmethod
        def definition(io):
 
            arr32 = m.concat(\
                    m.bits(io.data_in[0:8]) ^ m.bits(io.data_in[8:16]),\
                    m.bits(io.data_in[8:16]) ^ m.bits(io.data_in[16:24]),\
                    m.bits(io.data_in[16:24]) ^ m.bits(io.data_in[24:32]),\
                    m.bits(io.data_in[24:32]) ^ m.bits(io.data_in[32:40]))

            arr16 = m.concat(m.bits(arr32[0:8]) ^ m.bits(arr32[16:24]),\
                             m.bits(arr32[8:16]) ^ m.bits(arr32[24:32]))
               
            m.wire(io.data_out, (m.bits(arr16[0:8]) ^ m.bits(arr16[8:16])) & m.bits(io.mask[0:8]))
       
    return TreeHash
