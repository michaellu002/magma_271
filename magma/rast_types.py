import magma as m

def Coordinate(num_bits):
    return m.SInt(num_bits)

def Point(num_axes, num_bits):
    return m.Array(num_axes, Coordinate(num_bits))

def Polygon(num_vertices, num_axes, num_bits):
    return m.Array(num_vertices, Point(num_axes, num_bits))

def Color(num_bits):
    return m.UInt(num_bits)

def Colors(color_channels, num_bits):
    return m.Array(color_channels, Color(num_bits))

SampleSize = m.Enum(ONE_PIXEL = 8, HALF_PIXEL = 4, QUARTER_PIXEL = 2, EIGHTH_PIXEL = 1)
