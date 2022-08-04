from PyPDF2 import PdfFileReader
import numpy as np
import copy
from io import BytesIO
import re
import zlib

class Graphics:

    toks = {
        'cm' : re.compile(b'((?:\d+(?:\.\d+)?\s+){6})cm', re.S), # captures the numbers as one group, need to split and cast to ints
        'Do' : re.compile(b'(\/\S+)\sDo', re.S), # captures the name object
        'Q' : re.compile(b'Q', re.S),
        'q' : re.compile(b'q', re.S)
    }

    def pdf_transformation_to_matrix (pdf_transformation):
        assert len(pdf_transformation) == 6
        ret = np.zeros((3, 3), dtype=float)
        ret[0:3, 0:2] = np.array(pdf_transformation).reshape((3, 2))
        ret[2, 2] = 1
        return ret

    def ctm_to_bounding_box(ctm, width, height):
        assert ctm.shape == (3, 3)
        return [ctm[2, 0], ctm[2, 1], width, height]

    def gs_param_dict_convert (ext_gs):
        if '/Type' in ext_gs:
            assert ext_gs['/Type'] == '/ExtGState'
        key_vals = []
        for key in ext_gs.keys():
            if key == '/LW':
                key_vals.append(('line_width', float(ext_gs['/LW'])))
            elif key == '/LC':
                key_vals.append(('line_cap', int(ext_gs['/LC'])))
            elif key == '/LJ':
                key_vals.append(('line_join', int(ext_gs['/LJ'])))
            elif key == '/ML':
                key_vals.append(('miter_limit', float(ext_gs['/ML'])))
            elif key == '/D':
                key_vals.append(('dash_pattern', (ext_gs['/D'][0], ext_gs['/D'][1]))) # TODO cast types here
            elif key == '/RI':
                key_vals.append(('rendering_intent', ext_gs['/RI']))
            elif key == '/OP':
                if '/op' in ext_gs:
                    key_vals.append(('overprint', True if ext_gs['/OP'] == 'true' else False))
                else: # Should do something different if both keys are there, but for now just do the same thing
                    key_vals.append(('overprint', True if ext_gs['/OP'] == 'true' else False))
            elif key == '/op':
                key_vals.append(('overprint', True if ext_gs['/op'] == 'true' else False))
            elif key == '/OPM':
                key_vals.append(('overprint_mode', float(ext_gs['/OPM'])))
            elif key == '/Font':
                # DEAL WITH THIS LATER
                pass
            elif key == '/BG':
                # DEAL WITH THIS LATER - read about functions in pdf
                pass
            elif key == '/BG2':
                pass
            elif key == '/UCR':
                pass
            elif key == '/UCR2':
                pass
            elif key == '/TR':
                pass
            elif key == '/TR2':
                pass
            elif key == '/HT':
                pass
            elif key == '/FL':
                key_vals.append(('flatness', float(ext_gs['/FL'])))
            elif key == '/SM':
                key_vals.append(('smoothness', float(ext_gs['/SM'])))
            elif key == '/SA':
                key_vals.append(('stroke_adjustment', True if ext_gs['/SA'] == 'true' else False))
            elif key == '/BM':
                key_vals.append(('blend_mode', ext_gs['/BM'])) # Will need to handle the case that it's an array
            elif key == '/SMask':
                key_vals.append(('soft_mask', ext_gs('/SMask'))) # Will need to type cast
            elif key == '/CA':
                key_vals.append(('alpha_constant_stroking', float(ext_gs('/CA'))))
            elif key == '/ca':
                key_vals.append(('alpha_constant_non_stroking', float(ext_gs('/ca'))))
            elif key == '/AIS':
                key_vals.append(('alpha_source', True if ext_gs['/AIS'] == 'true' else False))
            elif key == 'TK':
                # This is for text knockout, which is part of the text state
                # I am hoping to add dictionary style indexing to the graphics state object
                # When a key is not in the dictionary, it will check the text state dictionary for a smooth experience
                pass
            else:
                raise Exception ("Not a valid ExtGState key")
    


               



class GraphicsState:

    def __init__ (self):

        self.current_resource_dict = {}
        self._init_state = {
            ### These are device independent ###
            "CTM" : Graphics.pdf_transformation_to_matrix([1, 0, 0, 1, 0, 0]), # Current transformation matrix- initialized to the identity matrix
            "clipping_path" : 0, # TODO: Should be the boundary of the entire imageable portion of the output page, not entirely sure of type
            "color_space" : 'DeviceGray', # Maybe make an enum however you do that in python
            "color" : 'black', # Same as above ^
            "text_state" : [], # TODO
            "line_width" : 1.0, # expressed in user space units
            "line_cap" : 0,
            "line_join" : 0,
            "miter_limit" : 10.0,
            "dash_pattern" : ([], 0), # This represents a solid line
            "rendering_intent" : '/RelativeColorimetric', # Technically a name, not a string. Should define a type alias probably
            "stroke_adjustment" : False,
            "blend_mode" : '/Normal', # Type is name OR array. Make discriminated union? probably doesn't matter too much, though
            "soft_mask" : (None, '/None'), # Dictionary OR name ^
            "alpha_constant_stroking" : 1.0,
            "alpha_constant_non_stroking" : 1.0,
            "alpha_source" : False,
            ### These are device dependent ###
            "overprint" : False,
            "overprint_mode" : 0,
            "black_generation" : None, # This should be a function, but no idea what yet. Not very important
            "undercolor_removal" : None, # Same as above ^
            "transfer" : None, # Same as above ^
            "halftone" : None, # Should be dict, stream, or name, but idk what to initialize to yet
            "flatness" : 1.0,
            "smoothness" : 0 # Shouldn't necessarily be 0 for slower machines. 0 Should be fine for what we are doing, though
        }
        self.stack = [self._init_state]

    def q (self): # q operator- push a copy of the entire state onto the stack
        new_state = copy.deepcopy(self.stack[-1])
        self.stack.append(new_state)

    def Q (self): # Q operator- pop one off the stack
        self.stack.pop()

    def cm (self, mat: list[float]): # update CTM by concatenating new transformation mat
        self.update_state('CTM', np.matmul(self.get_value('CTM'), Graphics.pdf_transformation_to_matrix(mat)))

    def w (self, new_width: float): # update line width
        self.update_state('line_width', new_width)

    def J (self, new_cap_style: float): # update line cap style
        self.update_state('line_cap', new_cap_style)

    def j (self, new_join_style): # update line join style
        self.update_state('line_join', new_join_style)

    def M (self, new_miter_limit): # update miter limit
        self.update_state('miter_limit', new_miter_limit)

    def d (self, dash_array: list[int], dash_phase: int): # update dash pattern
        self.update_state('dash_pattern', (dash_array, dash_phase))

    def ri (self, new_intent: str): # update rendering intent
        self.update_state('rendering_intent', new_intent)

    def i (self, new_flatness: float): # update flatness tolerance
        self.update_state('flatness', new_flatness)

    def gs (self, dict_name: str): # update specified params in graphics state 
        for key, val in self.current_resource_dict['/ExtGState']:
            self.update_state(key, val)
        # This is basically pseudocode. Will need to look into this more deeply later
        # Reference page 128 https://opensource.adobe.com/dc-acrobat-sdk-docs/standards/pdfstandards/pdf/PDF32000_2008.pdf


    def update_state (self, key, value):
        self.stack[-1][key] = value

    def get_value (self, key):
        return self.stack[-1][key]
        




class PDF:

    def __init__ (self, fname):
        self.file = BytesIO(open(fname, "rb").read())
        #self.reader = PdfFileReader(fname)
        self.graphics_state = GraphicsState()

        self._fp = 0
        self._block_size = 4096
        self.toks = {
            "stream": re.compile(b'stream', re.S),
            "endstream": re.compile(b'endstream', re.S),
            "stream_data": re.compile(b'stream([\s\S]*?)endstream', re.S),
            "indirect_object": re.compile(b'\/\S+\s(\d+)\s0\sR', re.S),
            "page_dict": re.compile(b'<<([\s\S]*\/Type\s\/Page[\s\S]*)', re.S),
            "xobj_dict": re.compile(b'<<([\s\S]*\/Type\s\/XObject[\s\S]*)>>', re.S)
        }
    
    def search_for_regex(self, exp, save_spot=False):
        eof = False
        spot = self.file.tell()
        read_data = b''
        block = self.file.read(self._block_size)
        if len(block) != self._block_size:
            eof = True
        read_data += block
        match = re.search(exp, read_data)
        while not match and not eof:
            block = self.file.read(self._block_size)
            if len(block) != self._block_size:
                eof = True
            read_data += block
            match = re.search(self.toks['stream_data'], read_data)
        if not match:
            raise Exception ("No match found in file")
        if save_spot:
            self.file.seek(spot, 0)
        else:
            self.file.seek(spot, 0)
            self.file.seek(match.start(), 1)
        return match

    def get_image_id (self, name, data):
        spot = self.file.tell()
        self.file.seek(0, 0)
        pattern = b"\/"+name[1:]+b"\s\d+\s0\sR"
        a = re.findall(pattern, self.file.read())
        print (a)
        id = a[0] # Use xref table or something in future
        self.file.seek(spot, 0)
        return id

    def get_dimensions (self, name, image_id=-1, data=None):
        spot = self.file.tell()
        if image_id == -1:
            if data == None:
                raise Exception ("Must supply dictionary to search")
            image_id = self.get_image_id(name, data)
        w_pattern = bytes(image_id)+b'\s0\sobj[\s\S]+<<[\s\S]+\/Width\s(\d+)'
        h_pattern = bytes(image_id)+b'\s0\sobj[\s\S]+<<[\s\S]+\/Height\s(\d+)'
        width = re.findall(bytes(w_pattern), self.file.read())[0]
        self.file.seek(0, 0)
        height = re.findall(bytes(h_pattern), self.file.read())[0] # Lol do better later
        self.file.seek(spot, 0)
        return (width, height)


    def get_xobj_metadata ():
        pass

    def get_page_resource_dictionary ():
        pass

    def _read_backwards (self, size):
        if self.file.tell() < size:
            raise Exception ("Can't read past the beginning") # TODO: Make better exceptions
        self.file.seek(-size, 1)
        ret = self.file.read(size)
        self.file.seek(-size, 1)
        return ret
    
    def _read_previous_line(self):
        line = []
        new_line = False
        at_eol = False
        if self.file.tell() == 0:
            raise Exception("Can't read past the beginning")
        self.file.seek(-1, 1)
        if self.file.read(1) in b'\r\n':
            at_eol = True
        while True:
            size = min(self._block_size, self.file.tell())
            if size == 0:
                break
            block = self._read_backwards(size)
            if at_eol:
                cur = len(block) - 2
            else:
                cur = len(block) - 1
            if not new_line:
                while cur >= 0 and block[cur] not in b'\r\n':
                    cur -= 1
                if cur >= 0:
                    new_line = True
            if new_line:
                if at_eol:
                    line.append(block[cur+1:-1])
                else:
                    line.append(block[cur+1:])
                while cur >= 0 and block[cur] in b'\r\n':
                    cur -= 1
            else:
                line.append(block)
            if cur >= 0:
                self.file.seek(cur+1, 1)
                break
        return b"".join(line[::-1])

    def seek_stream_start (self): 
        size = min(self._block_size, self.file.tell())
        match = re.search(self.toks['stream'], self._read_backwards(size))
        while not match:
            size = min(self._block_size, self.file.tell())
            match = re.search(self.toks['stream'], self._read_backwards(size))
        self.file.seek(match.start(), 1)

    def get_stream_data (self):
        stream = b''
        stream += self.file.read(self._block_size)
        match = re.search(self.toks['stream_data'], stream)
        while not match:
            stream += self.file.read(2 * self._block_size)
            match = re.search(self.toks['stream_data'], stream)
        return zlib.decompress(match.group(1).strip(b'\r\n')).decode('UTF-8')

    def get_image_bbox (self):
        bboxes = {}
        def filter_late (match, index): # Filter out any instances that come after the do operator
            return match.start() < index
        stream = re.search(self.toks['stream_data'], self.file.read()) # TODO: write re to extract length object and only load that into memory
        data = zlib.decompress(stream.group(1).strip(b'\r\n'))
        ims = re.finditer(Graphics.toks['Do'], data)
        for image in ims:
            ops = []
            self.graphics_state = GraphicsState()
            name = image.group(1)
            self.file.seek(image.start())
            self.seek_stream_start()
            do_index = image.start() - stream.start()
            for q in filter(lambda x: filter_late(x, do_index), re.finditer(Graphics.toks['q'], data)):
                ops.append((q, 'q'))
            for Q in filter(lambda x: filter_late(x, do_index), re.finditer(Graphics.toks['Q'], data)):
                ops.append((Q, 'Q'))
            for cm in filter(lambda x: filter_late(x, do_index), re.finditer(Graphics.toks['cm'], data)):
                ops.append((cm, 'cm'))
            ops.sort(key = lambda t: t[0].start())
            for op in ops:
                if op[1] == 'q':
                    self.graphics_state.q()
                elif op[1] == 'Q':
                    self.graphics_state.Q()
                else:
                    cg = op[0].group(1)
                    arr = list(map(lambda x: float(x), cg.split()))
                    self.graphics_state.cm(arr)
            bboxes[name] = self.graphics_state.get_value('CTM')
            print (f"{name} dimensions: {self.get_dimensions(name)}")
        return bboxes
"""
*****NOTES*****

# All sampled images shall be defined in image space. The transformation from image space to user space
# shall be predefined and cannot be changed. All images shall be 1 unit wide by 1 unit high in user space,

# A form XObject (discussed in 8.10, "Form XObjects") is a self-contained content stream that can be treated
# as a graphical element within another content stream. The space in which it is defined is called form space.
# The transformation from form space to user space shall be specified by a form matrix contained in the form
# XObject.

# Translations shall be specified as [ 1 0 0 1 tx ty ], where tx and ty shall be the distances to translate the
# origin of the coordinate system in the horizontal and vertical dimensions, respectively.

# Scaling shall be obtained by [ sx 0 0 sy 0 0 ]. This scales the coordinates so that 1 unit in the horizontal
# and vertical dimensions of the new coordinate system is the same size as sx and sy units, respectively, in
# the previous coordinate system.

# Rotations shall be produced by [ cos q sin q -sin q cos q 0 0 ], which has the effect of rotating the
# coordinate system axes by an angle q counter clockwise.

# Skew shall be specified by [ 1 tan a tan b 1 0 0 ], which skews the x axis by an angle a and the y axis by
# an angle b.

#  Order: Translate, Rotate, Scale or Skew.

# [x^prime y^prime 1] = [x y 1] x pdf_transformation_to_matrix ([a, b, c, d, e, f])

# Some graphics state parameters are set with specific PDF operators, some are set by including a particular
# entry in a graphics state parameter dictionary, and some can be specified either way.

# Graphics state is a stack

# Occurrences of the q and Q operators shall be balanced within a given content stream
# ^ this means that when we 'Do' an XObject, we can just search through the same content stream for all 
# occurrences of operators that change the gs, and then calculate where the image will be rendered
# from the gs right before 'Do'

# The implicit transformation from image space to
# user space, if specified explicitly, would be described by the matrix [ (1/w) 0 0 (-1/h) 0 1 ]

***************
"""


pdf = PDF('2207.06409.pdf')
#pdf.seek_stream_start()
# for i in range(10):
#     pdf.file.readline()

# # print ("### BACKWARD ###")

# # for i in range(8):
# #     print (f"{i}. {pdf._read_previous_line()}")

# pdf.seek_stream_start()
# print (pdf.get_stream_data())

# for i in range(8):
#     print (pdf.file.readline())

# pdf.seek_stream_start()
#print (pdf.get_image_bbox())

print (pdf.search_for_regex(pdf.toks['xobj_dict']).group(1))