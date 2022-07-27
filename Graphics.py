from PyPDF2 import PdfFileReader
import numpy as np
import copy

class Graphics:

    def pdf_transformation_to_matrix (pdf_transformation):
        assert len(pdf_transformation) == 6
        ret = np.zeros((3, 3), dtype=float)
        ret[0:3, 0:2] = np.array(pdf_transformation).reshape((3, 2))
        ret[2, 2] = 1
        return ret

class GraphicsState:

    def __init__ (self):

        self.state = {

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
            "blend_mode" : ('/Normal', None), # Type is name OR array. Make discriminated union? probably doesn't matter too much, though
            "soft_mask" : (None, '/None'), # Dictionary OR name ^
            "alpha_constant" : 1.0,
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

        self.stack = [self.state]

    def q (self): # q operator- push a copy of the entire state onto the stack
        new_state = copy.deepcopy(self.stack[-1])
        self.stack.append(new_state)

    def Q (self): # Q operator- pop one off the stack
        self.stack.pop()

    def cm (self, mat: list[float]): # update CTM by concatenating new transformation mat
        self.update_state('CTM', np.matmul(self.state['CTM'], Graphics.pdf_transformation_to_matrix(mat)))

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

    def gs (self): # update specified params in graphics state 
        # TODO
        pass


    def update_state (self, key, value):
        self.stack[-1][key] = value
        




class PDF:

    def __init__ (self, fname):
        self.reader = PdfFileReader(fname)
        self.graphics_state = GraphicsState()

    def get_indirect_obj (self, obj_num, generation):
        pass

    def get_graphics_state (self):
        pass


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

***************
"""

a = [1, 0, 0, 1, 5, 5]
# print (Graphics.pdf_transformation_to_matrix(a))

gs = GraphicsState()
gs.cm (a)
print (gs.state['CTM'])