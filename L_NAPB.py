#
# A Blender Console only script
# -----------------------------
#
# L_NAPB.py - 
#
# Use Blender to execute L-system turtle commands held in the given
# cmds file to produce 3D plant models (.obj, .mtl)
# 
# Setup instructions:
# In /usr/share/blender/scripts/modules
# we need to have L_NAPB.py, L_NAPC.py and L_NAPX.py, turtle.py 
# which must be copied by "sudo cp" from ~/L_NAP/Apps
#
# We run Blender 2.79, clear splash screen by left-clicking on it, and
# remove cube by left-click on it and press x and select delete.
#
# File Import, filetype Wavefront (.obj) , into the Blender scene 
# the file /home/pi/Seedgreen2.obj. (We select the .obj file only, and 
# Blender inports data from .obj and .mtl files.) 
# Right click on Seed and hold and move it to bottom of screen and 
# drop the seed by releasing the right mouse button, and 
# click left button to keep it there.
#
# Start a blender python console by clicking in the bottom left corner
# the small up/down arrows and selecting Blender Console. Them slide 
# the bottom of the upper window up to expose more of the 
# PYTHON INTERACIVE CONSOLE 3.7.3 (Jan 22, 2021)
#
# Ensure that the output device is available as defined on the 
# last program line (215)
# Currently this is set to /home/pi/L_NAP/models/
#
# On that console type python commands, then wait a minute):
# >>> import L_NAPB as B
# >>> B.Draw("~/L_NAP/Draw/wh_01_020.cmds")
# >>> 
#
# OR, when I modify L_NAPb suiably, just run (TODO)
# $  blender L_NAPb.blend --background --python L_NAPb.py --draw "wh200.cmds:
#
# This creates .obj amd .mtl files for models in /home/pi/L_NAP/models/
# or in directory set on last script line. 
#
#
import bpy
import math
import os
from turtle	import DrawingTurtle 	# Leopold's Drawing turtle 
import L_NAPC

from mathutils import Vector, Matrix

from L_NAPX import * # Define S,So        as Scene, Scene objects;
					#        D,Do        as Data, Data objects
					#		 O,Oo,Or,Ov  as Ops, objects, render, view3d 
					#        Cx          as Context
					#
					# Define remove_startswith_objects("Wheat_")
					# Define remove_except_objects(["LAMP", "CAMERA"])

from L_NAP_DIRS import *    # Out: RESULT


#
# Convert drawing cmd to Leopold drawing turtle dt with log comment
#

""" Move stepsize from current cursor location 
	in the turtle direction, without drawing. """
""" Draw an 'F' cylinder object from the current cursor location 
	    in the turtle direction, and move cursor to end of F cylinder. """
dt = DrawingTurtle(1, 0);
scale = Vector((1,1,1))
PlantNr = 0
PlantNrx = 0
ClassNr = 0

Parameters = []

def parameters(pars): Parameters = pars; #print(f"Parameters: {Parameters}")
def plantnr(pn): global PlantNr; PlantNr= pn; print(f"This PlantNr is: {PlantNr:04}");
def classnr(cn): global ClassNr; ClassNr= cn; bpy.context.scene.bool_no_hierarchy = True;	print(f"ClassNr: {ClassNr:03}")
def finish(fn): global PlantNr; print(f"Finish PlantNr is: {PlantNr:04} {ClassNr:03}");
	
def views(v):	global PlantNr; PlantNr = v; #print(f"Views of PlantNr: {PlantNr:03}")

def draw(length=1, width=0):dt.draw_internode_module(length=length, width=width); dt.move(stepsize=length);	print(f"F: {length}, {width}")	
def move(stepsize=1):		dt.move(stepsize=stepsize);		print(f"f {stepsize}")
def draw_obj(name="",scale=scale): dt.draw_module_from_custom_object(objname=name, objscale=scale); #print(f"~: {name}")
def turn_left(angle=0.0):	dt.turn(angle_degrees=angle);	#print(f"+: {angle}")
def turn_right(angle=0.0):	dt.turn(angle_degrees=-angle);	#print(f"-: {angle}")
def turn_around():			dt.turn(angle_degrees=180.0);	#print(f"+: 180")
def pitch_down(angle=0.0):	dt.pitch(angle_degrees=-angle);	print(f"&: {angle}")
def pitch_up(angle=0.0):	dt.pitch(angle_degrees=angle);	print(f"^: {angle}")
def roll_left(angle=0.0):	dt.roll(angle_degrees=angle);	print(f"\\: {angle}")
def roll_right(angle=0.0):	dt.roll(angle_degrees=-angle);	print(f"/: {angle}")
def look_at(target):		dt.look_at(target=target);		#print(f">: {target}")
def save(): 				dt.push();						#print(f"[ Save")
def restore():				dt.pop();						#print(f"] Restore")
		
valid_cmds = ['para', 'plan', 'clas', 'fini', 'draw','move', 'turn','pitc','roll','look','save','rest']
#-----------------------------------------------------------------------

def export(dir="", name="", deselect=False):
	""" Export currently selected objects by name to given directory,
	    such as dir="/tmp/", as '.obj' and '.mtl' files """

	objects = bpy.context.selected_objects
	
	# Select each of the input selected object in turn and
	# export it as .obj file
	bpy.ops.object.select_all(action='DESELECT')
	for obj in objects:
		bpy.context.scene.objects.active = obj
		obj.select = True

		name = os.path.join(dir, obj.name)
		name = name + ".obj"
		#f"{dir}{obj.name}.obj"

		print(f"Export: {name}")
		
		bpy.ops.export_scene.obj(filepath=name, use_selection=True)
		#--NOT bpy.ops.export_mesh.stl(filepath=name2, use_selection=True)
		
		obj.select = False
		
	# Reselect objects as they were on input, unless deselect=True
	if not deselect:
		for obj in objects:
			obj.select = True
		
#
# Draw the plants defined in drawing cmds. for which the plantNr
# is >= from_plantnr.
#
def Draw(cmds="", from_plantnr=1):
	
	""" Draw a 3D plant as a series of connected objects by 
	executing all the turtle commands, which follow a tab character,
	from the given cmds file. The commands are executed/visualised 
	by calling functions of Leopold's drawing turtle dt 
	"""
	global dt, PlantNr, ClassNr, Parameters
	

	#if bpy.context.object.mode == 'EDIT':
	#    bpy.ops.object.mode_set(mode='OBJECT')
	finished = False
	
	# Start from given plantnr
	Skipping = False

	with open(cmds) as commands:
		
		for command in commands:
			if not finished and len(command) > 1 and command[0] == '\t':
				cmd = command[1:]
						
				if len(cmd) >= 4 and cmd[0:4] in valid_cmds:
					#
					# A valid comand, but only execute it if 
					# its a EITHER a plantnr command (so that we
					#              know what plant we are at,
					#	    OR     We are not Skipping
					#
					if cmd.startswith("plantnr") or not Skipping:
						#
						# Actually execute this cmd, so that
						# EITHER a command is given to blender 
						#        to draw and object,
						# OR internal information is extracted 
						# from the cmd, such as the PlantNr or
						# the ClassNr which are globals here.
						# (This is how we know to which plantnr 
						# the cmds apply, and so we can Skip
						# until the given from_plantnr) 
						#
						exec(cmd)
					#
					# If we just set a new PlantNr with exec(cmd), then
					# reload turtle module and DrawTurtle, preparing
					# to draw the new plant with the following cmds,
					# unless we have not reaced the required start plant
					# at from_plantnr
					#
					if cmd.startswith("plantnr"):
						
						Skipping = PlantNr < from_plantnr
						if Skipping:
							# Skip until finish of current plant model
							pass
						else:
							
							import turtle, imp
							imp.reload(turtle)
							from turtle import DrawingTurtle
							dt = DrawingTurtle(1, 0)
							print(f"PlantNr: {PlantNr:04}")
							#
							# Remove all previous "Wheat_" objects from the Scene
							# so as to clear their data usage, before processing
							# this new plantnr cmds.
							#
							remove_startswith_objects(startswith="Wheat_")
						
					#
					# On the finish cmd of a Plant, we can process 
					# the whole plant, as plant number 'PlantNr'.
					#											
					elif cmd.startswith("finish"):
						
						if Skipping:
							pass
						else:
							# Select just-created plant and rename as
							# Wheat_'PlantNr'
							obj = bpy.context.active_object
							if obj.name.startswith("Plan"):
								obj.select = True
								old_name = f"{obj.name}"
								obj.name = f"Wheat_{PlantNr:03}"
								export(dir=RESULT, deselect=True)

								print(f"{RESULT} {obj.name} created from {old_name}")
					
	
							

