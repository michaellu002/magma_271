import sys
import bit_vector as bv
import magma as m
import mantle
import fault
import json

def reverse_hex(s):
    return hex(int("{0:b}".format(int(s, 16))[::-1], 2))

def pack_arg(arg):
    if isinstance(arg, str):
        return arg[::-1]
    elif isinstance(arg, list):
        s = ''
        for item in arg:
            s = s + pack_arg(item)
        return s

def pack_vectors(dut, json_vector_file, n=None):
    vector_data = open(json_vector_file).read()
    vectors = json.loads(vector_data)
   
    packed_vectors = []
    for vector in (vectors if n is None else vectors[0:n]):
        v = ''
        for name, port in dut.interface.ports.items():
            if not isinstance(port, m.ClockType):
                v = v + pack_arg(vector[name])
        #print(v)
        v = v + '\n'
        packed_vectors = packed_vectors + [v]
    return packed_vectors

def str2bit(b):
    return 1 if b == '1' else 0

def str2bits(bs):
    return [str2bit(b) for b in bs]

def _cast(bits, T):
    if isinstance(T, (m.BitKind, m.ClockKind, m.ResetKind)):
        return bits[0]
    elif isinstance(T, m.UIntKind):
        return bv.UIntVector(bits)
    elif isinstance(T, m.SIntKind):
        return bv.SIntVector(bits)
    elif isinstance(T, m.BitsKind):
        return bv.BitVector(bits)
    elif isinstance(T, m.ArrayKind):
        return [_cast(bits[i*T.T.size():(i+1)*T.T.size()], T.T) for i in range(0, T.N)]
    assert False

def cast(bits, T):
    assert isinstance(T, m.TupleKind)
    ts = {}
    i = 0
    j = 0
    #print("T.Ts", T.Ts)
    #print("len(T.Ts)", len(T.Ts))
    for i in range(len(T.Ts)):
        if not isinstance(T.Ts[i], m.ClockKind):
             k = T.Ks[i]
             t = T.Ts[i]
             n = t.size()
             #print("j", j, "j+n", j+n)
             ts[k] = _cast(bits[j:j+n], t)
             j = j + n
    return ts

def process_inputs(circuit, tester, args):
    for name, port in circuit.interface.ports.items():
        if port.isoutput():
            if not isinstance(port, m.ClockType):
                print(f'tester.poke({name},{args[name]})')
                tester.poke(getattr(circuit, name), args[name])

def process_outputs(circuit, tester, args):
    for name, port in circuit.interface.ports.items():

        print(f'tester.print({name})')
        tester.print(getattr(circuit, name))
        
        if port.isinput():
            print(f'tester.expect({name},{args[name]})')           
            tester.expect(getattr(circuit, name), args[name])

def Tester(circuit, lines):
    args = { name:type(port) for name, port in circuit.interface.ports.items() }
    args = m.Tuple(args)
    print(circuit)
    print(args)

    clock = None
    for name, port in circuit.interface.ports.items():
        if isinstance(port, m.ClockType):
            clock = port

    #print(clock)
    tester = fault.Tester(circuit, clock=clock )

    for line in lines:
        #print("line", line[:-1])
        testargs = cast( str2bits(line[:-1]), args )
        if clock:

            process_inputs(circuit, tester, testargs)
            print('tester.eval()')
            tester.eval()
            process_outputs(circuit, tester, testargs)
            print('tester.step()')
            tester.step()
            print('tester.eval()')
            tester.eval()
            print('tester.step()')
            tester.step()

        else:
            process_inputs(circuit, tester, testargs)
            tester.eval()
            print('tester.eval()')
            process_outputs(circuit, tester, testargs)
     
    #tester.compile_and_run(target='python')
    #tester.compile_and_run(directory="build", target="verilator", flags=["-Wno-fatal"])
    return tester
