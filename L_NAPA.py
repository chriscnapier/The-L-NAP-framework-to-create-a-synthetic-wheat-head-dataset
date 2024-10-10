#
# SPINA.py   - Synthetic Plant Inference Network of Aristid-lindenmayer
#
# This is a stand-alone Python3.7 script which runs the first synthetic 
# plant pipeline. It implements an L-system specifically for Wheat Heads.
# 
# It outputs drawing commpands, when run by the second Python script 
# SPINB.py will create the synthetic 3D plant models in Blender and 
# SPINB.py will output 3D model files 
# (.obj) and next pipeline SPINC (and SPINC2 ?) will create multiple 
# 2D views of each model. 
#
# Each plten to the cmds file is a Wheat Head variation, 
# created by a mathematical Aristid Lindenmayer system, 
# using variations of the L-system parameters, defined in SPINA_p.py
#
# Random Gaussian distributions are used throughout, which use a seed 
# to endsure full repeatability of plant form on SPINA rerun.
#
# It must first be adjusted to set the L-system base parameters 'P',
# and the number of models to be created 'Some'.
# and other variational details, and then run on Linux to produce a 
# commands file such as "Wheat_001.cmds" thus:
#
# $ python3.7 L_NAPA.py
#

""" Import the L_NAP application and the L_NAPA_p parameters """
from L_NAP import *
from L_NAPA_p import *

""" Initialise plant object L_NAPA with its parameters """
L_NAPA = L_NAP("L_NAPA_p") 

""" Define all the L_NAPA production rules """	
def Axiom():		L_NAPA(Stalk, GrainSpace)

def Stalk():		L_NAPA(Curve) 

def GrainSpace():	L_NAPA(Pitch, Turn, Roll, Draw, Grain, GrainSpace)

def Grain():		L_NAPA(Save, Pitch, Object, Awn, Restore)		 

def Awn():			L_NAPA(Curve)


		
""" 
Grow plants in stages starting at Axiom following L_NAPA rules and
parameters. The parameters also define the number and type of plants.
"""
while L_NAPA.next_plant():
	while L_NAPA.next_stage(Axiom):
		L_NAPA.grow()
		
