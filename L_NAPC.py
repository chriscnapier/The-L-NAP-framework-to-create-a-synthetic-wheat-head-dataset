#
# A Blender Console only script
# -----------------------------
# Run with Linux commands:
#
# $ cd /home/pi/L_NAP
# $ blender RGB.blend --background --python L_NAPC.py
#
# Since we MUST SET IMAGE OUTPUT TO RGB (NOT default RGBA),
#
# Note:
# RGB.blend,in direcrtory ~/L_NAP, is simply a saved blend file 
# (File > Save) in which the RGB button was pressed 
# instead of the default RGBA.
# 
#
"""
scene = bpy.context.scene

# create the first camera
cam1 = bpy.data.cameras.new("Camera1")
cam1.lens = 18

# create the first camera data object
cam_obj1 = bpy.data.objects.new("Camera1", cam1)
cam_obj1.location = (9.69, -10.85, 12.388)
cam_obj1.rotation_euler = (0.6799, 0, 0.8254)

# Link camera object to scene
scene.objects.link(cam_obj1)

"""
import bpy
import math
import sys
import os

from L_NAPX import *	# Define S,So        as Scene, Scene objects;
					#        D,Do        as Data, Data objects
					#		 O,Oo,Or,Ov  as Ops, objects, render, view3d 
					#        Cx          as Context
					#
					# Define remove_startswith_objects("Wheat_")
					# Define remove_except_objects(["LAMP", "CAMERA"])

"""
#
# Set the Scene and Blender data, ops, and context base addresses.
# In Blender console after import L_NAPc as c, 
# we can refer to c.Do and setup CO as:  >>> CO = c.Do[c.CN]
# or as: >>> c.setup()
#
# Scene
# -----
S  = bpy.context.scene
So = S.objects
Sr = S.render
#
# Data
# ----
D  = bpy.data
Do = D.objects
#
# Ops
# ---
O  = bpy.ops
Oo = O.object
Or = O.render
Ov = O.view3d
#
# Context
# -------
Cx  = bpy.context
#---
"""
from L_NAP_DIRS import *    # MODEL, VIEW


# The Camera name and its setup object CO
# The object CO is set and recovered as needed when this module is
# reloaded
# The object data is at CO.data, since 
# for example CO.data.lens is set to 18 in setup()
#
CN	= 'Camera'	# Fixed name of Camera, MUST be 'Camera',
				# to make Blender work properly (bug?)
CO	= 0			# Camera object not yet created


LN  = 'Lamp'	# Name of light
LO  = [0,0,0.0]	# Light objects not yet created
# Light positions corresponding to LO
Lights = [(1, 1,10), (-1, 1, 10), (1,-1,10), (-1,-1,10)]

#
# Camera locations, leading to plant pose variations
#
Locations = [( 0, 0,9), 
			 ( 0,+1,9), (+1, 0,9), (+1,-1,9),
			 ( 0,-1,9), (-1, 0,9), (-1,-1,9),
			 (-1,+1,9), (+1,-1,9),
			 
			 ( 0,+1.5,9), (+1.5, 0,9), (+1.5,-1.5,9),
			 ( 0,-1.5,9), (-1.5, 0,9), (-1.5,-1.5,9),
			 (-1.5,+1.5,9), (+1,-1.5,9),

			 ( 0,+2,9), (+2, 0,9), (+2,-2,9),
			 ( 0,-2,9), (-2, 0,9), (-2,-2,9),
			 (-2,+2,9), (+2,-2,9),
			]

def setup_camera():
	"""
	If CO is already present in data objects use that if valid, otherwise
		create a new camera object CO of fixed name CN, 
		with its data, and set lens to 18
		and link the new object CO to the Scene objects.
	
	Double check the setup Camera object is a 'CAMERA' type.
	"""
	global CN, CO
	
	if CN in Do:
		if Do[CN].type == "CAMERA":
			CO = Do[CN]
			return "FINISHED"
		else:
			return f"Error: Object {CN} is not a CAMERA, but has type {Do[CN].type}"		
	else:
		data = D.cameras.new(name=CN)
		data.lens = 18

		CO = Do.new(CN, data)
		So.link(CO)
		return "FINISHED"

def locate_camera(location):
	"""
	Locate the Camera object in the 3D Scene at given location
	"""
	global CO
	
	# Recover to same object CO after imp.reload(L_NAPc) using fixed CN
	if CO == 0:
		setup()
	
	# Place the Camera named CN at 3D locatiom
	if CO != 0:	
		CO.location = location
	
def rotate_camera(re):
	"""
	Rotate the Camera object by given 3-tuple euler rotation Re
	"""
	global CO
	if CO == 0:
		setup()

	if CO != 0:
		print(f"Re: {re}")
		CO.rotation_euler = re

		
def still_camera(out_dir, filename):
	"""
	Take a still camera view to 'filename'.jpg in out_dir
	"""
	global CN, CO

	if CO == 0:
		setup()

	if CO != 0:
		
		#--Oo.select_all(action='DESELECT')

		# Make CO THE active object in the Scene objects
		So.active = CO
		
		CO.select = True
		#--Ov.camera_to_view_selected()
		filepath = out_dir + filename
		print(f"Still photo by {So.active.name} to {filepath}")
		#
		# Take a still photograph to 'filepath'.jpg
		#
		Sr.image_settings.file_format='JPEG'
		Sr.filepath = filepath
		Or.render(write_still=True) 
		
#-----------------------------------------------------------

def setup_lights():
	global LN, LO
	
	if LN in Do:
		if Do[LN].type == "LAMP":
			for n in range(len(LO)):
				if n == 0:
					LO[n] = Do[LN]
				else:
					ln = f"{LN}.{n:03}"
					if ln in Do:
						LO[n] = Do[ln]
					else:
						data = D.lamps.new(name=ln, type='POINT')
				
						LO[n] = Do.new(ln, data)
						So.link(LO[n])
						
				LO[n].location = Lights[n]
						
			return "FINISHED"
		else:
			return f"Error: Object {LN} is not a CAMERA, but has type {Do[LN].type}"		
	


#
# Run the L_NAPC pipeline
# ---------------------- 
def run_pipeline(in_dir, out_dir):
	"""
	Read models from in_dir compute and write view image files to out_dir.
	"""
	global CO	#Camera Object
	
	import os	#Operating system: used for file I/O
	
	#
	# Remove objects from scene except types CAMERA and LAMP, since some
	# unnecessary objects may be loaded from the loaded blend file.
	#
	remove_except_objects(except_types=['CAMERA', 'LAMP'])

	#
	# Import each sorted-by-name model mn in_file (.obj,.mtl) in in_dir, 
	# and take multiple still views of it to view files.
	#
	N = 0
	for mn, in_file in enumerate(sorted(os.listdir(in_dir)), start=1):
		if in_file.endswith(".obj"):
			N += 1

			in_file_name = os.path.splitext(in_file)[0]
			print(f"Importing: {in_file_name}")
			O.import_scene.obj(filepath=f"{in_dir}{in_file}")

            #    
			# Place Camera at each of the vn 3-tuple Locations in turn 
			# pointing downwards, and record still images to .png files
			#
			for vn, location in enumerate(Locations, start=1):
				if len(location) == 3:
					locate_camera(location)
					rotate_camera((0,0,0))	
					still_camera(out_dir, f"{in_file_name}_{vn:03}")
			#
			# Remove all imported "Wheat_" objects from scene
			# before next model processing
			# 
			remove_startswith_objects("Wheat_")
	return N
			 
			
def main():
	"""
	Start the L_NAPC pipeline:
	"""
	#
	# Set up the Camera and Lampss, and run the pipiline from
	# models to views
	#  
	if setup_camera() == "FINISHED":
		print("SETUP CAMERA FINISHED")
		#--Do[CN].data.lens = 18
		if setup_lights() == "FINISHED":
			print("SETUP LIGHTS FINISHED")
			N = run_pipeline(MODEL, VIEW)
			print(f"Read {N} model object files")
			
	return 0
	

	
if __name__ == '__main__':
	sys.exit(main())
	

