#
# Evaluate the Dataset
#
# import required libraries
import os
import math
import numpy as np
import cv2
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from L_NAP_DIRS import *    # In: VIEW, META, GWCD; Out: RESULT
pass

#
# Globals
#     
threshold = 0.50	# Minimum iscore
step = 10			# Pixel step on comparing real and synthetic images
case = 1			# Remove smaller overlap region, 
					# as opposed to removing lower score (case 2)
log = False

#real_file = "tr_0056_036_01"
real_file = "tr_0063_023_01"
#
#real_file = "tr_0122_028_02"

#[("Wheat_0096_123_016", "Large") ]

synt_files = [
	("Wheat_001_022", "Medium"),
	("Wheat_002_022", "Medium"),
	("Wheat_003_022", "Medium"),
	("Wheat_004_022", "Medium"),
	#("Wheat_005_022", "Medium"),
	#("Wheat_0007_131_014", "Long"),	#~/L_NAP/views/wheat/ (json hand-made)
]
		
"""		
("Wheat_0093_160_019", "Large"),
("Wheat_0095_102_005", "Medium"),
("Wheat_0086_103_009", "Large"),
("Wheat_0085_090_010", "Medium"),
#("Wheat_0094_078_024", "Part_bot"),
"""				 


#
# Pre-read Gwcd image data, (TODO: add x and y reflections/rotations)
#   
maxi = []
rf = os.path.join(GWCD, real_file+".png")
real = cv2.imread(rf, 0)	#Grayscale


#real = (real-0).clip(50,None)

rx_max, ry_max = real.shape
N = rx_max//step
M = ry_max//step

def data_get(filename): 
	#
	# Must remove /dir/ from filename and 
	# add META INSTEAD ! 
	#
	i = filename.rfind('/')
	if i >= 0:
		filename = filename[i+1:]
	in_path = os.path.join(META, filename+".json")
	with open(in_path, "r") as file:
		data = file.read()
		if len(data) > 0:
			data = eval(data)
			return data
	return None
			
def local_maxima_get():
	maxima = []
	
	return maxima

def rgb2gray(rgb):
    r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray
    			 
def display(images, titles=None, cols=4, cmap=None, norm=None,
                   interpolation=None):
    """Display the given set of images, optionally with titles.
    images: list or array of image tensors in HWC format.
    titles: optional. A list of titles to display with each image.
    cols: number of images per row
    cmap: Optional. Color map to use. For example, "Blues".
    norm: Optional. A Normalize instance to map values to colors.
    interpolation: Optional. Image interpolation to use for display.
    """
    titles = titles if titles is not None else [""] * len(images)
    rows = len(images) // cols + 1
    plt.figure(figsize=(14, 14 * rows // cols))
    i = 1
    for image, title in zip(images, titles):
        plt.subplot(rows, cols, i)
        N = title[0:4]
        Grains = title[5:8]
        Pose = title[9:12]
        Itype = title[12:]
        t = f"{i}: N:{N}, Grains:{Grains}, Pose:{Pose}{Itype}"
        plt.title(t, fontsize=9)
        plt.axis('off')
        plt.imshow(image.astype(np.uint8), cmap=cmap,
                   norm=norm, interpolation=interpolation)
        i += 1
    plt.show()

def x_limit_plus(limit, x_mid, y_mid, step, x_min, x_max):
	x_found = x_mid
	for x in range(x_mid+step, x_max, step):
		if x > x_max:
			return x_found 
		x_found = x
		if real[x, y_mid] < limit:
			return x_found
	return x_found
			
def x_limit_minus(limit, x_mid, y_mid, step, x_min, x_max):
	x_found = x_mid
	for x in range(x_mid-step, x_min, -step):
		if x < x_min:
			return x_found 
		x_found = x
		if real[x, y_mid] < limit:
			return x_found
	return x_found
			
def y_limit_plus(limit, x_mid, y_mid, step, y_min, y_max):
	y_found = y_mid
	for y in range(y_mid+step, y_max, step):
		if y > y_max:
			return y_found 
		y_found = y
		if real[x_mid, y] < limit:
			return y_found
	return y_found

def y_limit_minus(limit, x_mid, y_mid, step, y_min, y_max):
	y_found = y_mid
	for y in range(y_mid-step, y_min, -step):
		if y < y_min:
			return y_found 
		y_found = y
		if real[x_mid, y] < limit:
			return y_found
	return y_found
#
# Create a new tb_ file from old file with the given bounding boxes 
# placed on it.
#	   
def save_with_boxes(new_file, boxes_list, removed):
	
     #data = plt.imread(old_file, 0)
     plt.imshow(real, cmap="gray")
     #gray = rgb2gray(data)
     
     ax = plt.gca()
     nbox = 1
     for m, box in enumerate(boxes_list):
         if m not in removed: 
             x1_str, y1_str, x2_str, y2_str, score, name, area, ms = box
             y1,x1,y2,x2 = int(y1_str),int(x1_str),int(y2_str),int(x2_str)
             
             gray_mean = np.mean(real[y1:y2, x1:x2])
          
             width, height = x2 - x1, y2 - y1
             rect = Rectangle((x1, y1), width, height, fill=False, color='red')
			
             ax.add_patch(rect)
             caption = f"{ms+1}: {score}%"
             ax.text(x1, y1-25, caption, size=8, verticalalignment='top',
				  color='yellow', backgroundcolor="none")

			 # add extent_box out from from mid point on real
             x_mid = x1 + width//2
             y_mid = y1 + height//2
			 
             limit = gray_mean * 0.8
			   
             x2 = x_limit_plus (limit, x_mid, y_mid, 10, 0, rx_max)
             x1 = x_limit_minus(limit, x_mid, y_mid, 10, 0, rx_max)
             y2 = y_limit_plus (limit, x_mid, y_mid, 10, 0, ry_max)
             y1 = y_limit_minus(limit, x_mid, y_mid, 10, 0, ry_max)
			 
             width, height = (x2 - x1, y2 - y1)
             rect = Rectangle((x1, y1), width, height, fill=False, color='green')
			
             ax.add_patch(rect)
			 
             nbox += 1
             #if nbox > 3:
             #    break 
             
             #if m > 3:
             #    break #xxxx
		 
     plt.savefig(new_file)
     fig = plt.figure()
     fig.clear()
     plt.clf()
     plt.close('all')


def get_mask(segmentatiom):

	counts, y_height, x_width = (0,0,0)
	
	if 'counts' in segmentation:
		counts = segmentation['counts']
	if 'size' in segmentation:
		y_height, x_width = segmentation["size"] 
			
	if counts == 0 or y_height == 0 or x_width == 0:
		return None
	
	mask = np.zeros([y_height, x_width, 1], dtype=np.uint8) 
	#ones = np.ones(x_width, dtype=np.uint8)
	
	i = 0
	while i < len(counts):
		
		x_flat = counts[i]
		i += 1
		lrun = counts[i]
		i += 1
		#np.put(mask, [x_flat, x_flat+lrun], ones[0:lrun], mode='clip')
		y = x_flat//x_width
		x = x_flat - y*x_width
		
		# Skip 2 edge pixels all round
		if y == 0 or y == 1 or y == y_height-1 or y == y_height-2:
			continue
		
		if x == 0 or x == 1:
			x = 2
		 
		if x+lrun >= x_width:
			lrun = x_width - x - 1
		if lrun <= 0:
			continue	
		
		mask[y][x:x+lrun][0] = 1
 	
	return mask

#
# Read synthetic data View file(s) (.jpg)
#
synts = []
titles = []
for synt_file, itype in synt_files:
	sf = os.path.join(VIEW, synt_file+".jpg")
	synt = cv2.imread(sf, 0)
	
	data = data_get(synt_file)	
	if data and 'annotations' in data:
		annotations = data['annotations']
		if isinstance(annotations, list):
			for annotation in annotations:
				mask = []
				if 'segmentation' in annotation:
					mask = get_mask(segmentation)
				elif 'bbox' in annotation: 
					y1,x1, y2,x2 = annotation['bbox']
					if y2 >= y1 and x2 >= x1:
						mask = synt[x1:x2, y1:y2]
				if len(mask) > 0:
					synts.append(mask)
					name = f"{synt_file[6:]}"
					if itype != "":
						name += " --" + itype
					titles.append(name)
		
print("All image data has been read")

display(synts, titles=titles, cmap="gray", cols=4) 

First = True
#
# Process images
#     The value m+1 will show in the recognised image caption which 
#     synt_file was matched (1-based)
#
for ms, (synt_file, itype) in enumerate(synt_files):
	#data = data_get(synt_file)
	
	#y1,x1, y2,x2 = data["annotations"][0]["bbox"]
	
	#name = "("+synt_file[0] + synt_file[7:10]+")"	#(W100)
	
	synt = synts[ms]
	
	#synt = synt[x1:x2, y1:y2] / 2
	synt = synt / 2
	
	synt = (synt -32).clip(0,None)
	sx_max, sy_max = synt.shape 
	box_area = sx_max * sy_max
	
	synt_mean = np.mean(synt)
	
	synt_max = synt_mean * box_area
	if First:
		synt_maximus = synt_max
		#First = False
		
	
	
	if synt_max <= 0:
		synt_max = 1
		
	if log:
		print(f"Synt max: {synt_max:0.2f}\n")
	synt += 32
	
	
	# Skip partial images for now, but allow Large through
	#--if itype == "Large":
	#--	pass
	#--elif itype != "":
	#--	break
	
	#
	# Compare this synt image to every sliding window position n x m 
	# on the real image, at x positions from 0 to rx_max, 
	# and at y positions 0 to ry_max, with step and stopping short 
	# of edges, by adding pixel values,on all positions of that real
	# image sliding window with corresponding synt poisitions, and
	# setting a score as the mean of the clipped sum.
	# Skip this position when its score is below the threshold,
	# otherwise record an iscore percentage (can exceed 100%)
	#
	iscore = np.zeros((N, M), dtype=np.uint8)
	"""
	for n, x in enumerate(range(0, rx_max-step-sx_max, step)):
		if log:
			print(f"\n {x}:", end="")
		for m, y in enumerate(range(0, ry_max-step-sy_max, step)):
			real_x = real[x:x+sx_max, y:y+sy_max]/2
	"""
	for n, x in enumerate(range(0, rx_max-step, step)):
		if log:
			print(f"\n {x}:", end="")
		for m, y in enumerate(range(0, ry_max-step, step)):
			if x+sx_max <= rx_max and y+sy_max <= ry_max:
				real_x = real[x:x+sx_max, y:y+sy_max]/2
			else:
				# at the right edge and bottom edge we move only valid
				# pixels into a pre-filled zero array real_x
				real_x = np.zeros((sx_max,sy_max), dtype=np.uint8)
				sx_m = sx_max
				if x+sx_m > rx_max:
					sx_m = rx_max - x
				sy_m = sy_max
				if y+sy_m > ry_max:
					sy_m = ry_max - y
				real_x[0:sx_m, 0:sy_m] = real[x:x+sx_m, y:y+sy_m]/2
				
			combine = real_x + synt
			clipped = combine - 128
			clipped = clipped.clip(0, None)
			score = np.mean(clipped) * box_area
	
			if score < threshold * synt_max:
				pass	#iscore[x,y] = 0		
				if log:
					print("    ", end ="")
			else:
				iscore[n,m] = int(score/synt_maximus*100)
				i = iscore[n,m]
				if log:
					print(f"{i:03} ", end ="")
				
				#plt.imshow(combine, cmap="gray", vmin=0, vmax=255), plt.show()
	if log:
		print("")
	
	#
	# Find local maxima into maxi of the iscore matrix, by comparing 
	# each value with its above and below, and its diagonally adjacent
	# scores. (8 comparsons), after checking that ii is not zero.
	# Then compute the bounding yxbox, with score, name, and box area.
	# thrown in for good measure. 
	#
	# TODO: We must use a proper numpy np.where function here instead
	# of individual comparisons.
	#
	for n in range(1,N-1):
		for m in range(1,M-1):
			i = iscore[n,m]
			if i > 0 and \
				i >= iscore[n,m+1]   and i >= iscore[n,m-1] and \
				i >= iscore[n+1,m]   and i >= iscore[n-1,m] and \
				i >= iscore[n+1,m+1] and i >= iscore[n+1,m-1] and \
				i >= iscore[n-1,m+1] and i >= iscore[n-1,m-1]:

				box = (step*n, step*m, step*n + sx_max, step*m + sy_max)
				yxbox = box[1], box[0], box[3], box[2], i, name, box_area, ms
				maxi.append(yxbox)
				
	xxx=1
	
	#---plt.imshow(synt, cmap="gray", vmin=0, vmax=127), plt.show()

	#plt.imshow(combine, cmap="gray", vmin=0, vmax=255), plt.show()

xxx=2

def IoU(box1, box2):
	
	box1_height = box1[2] - box1[0]
	box1_width  = box1[3] - box1[1]
	box1_area   = box1[6]

	box2_height = box2[2] - box2[0]
	box2_width  = box2[3] - box2[1]
	box2_area   = box2[6]
	
	union = box1_area + box2_area
	if union <= 0:
		return 0
		
	x1 = box1[0]
	x2 = box2[0]
	
	y1 = box1[1]
	y2 = box2[1]
	
	if x1 < x2:
		h = (x1 + box1_height) - x2
	else:
		h = (x2 + box2_height) - x1
		
	if y1 < y2:
		w = (y1 + box1_width) - y2
	else:
		w = (y2 + box2_width) - y1
		
	if h > 0 and w > 0:
		inter = h * w
		IoU = inter / union 
		return IoU
	else:
		return 0
	
	

#
# Remove overlapping boxes (more than allowed_overlap)
# with lower scores (NOT considering their area (somehow))
# TODO: Instead we always compare large synt images first and REMOVE 
# them from the real image, and then proceed to small sized 
# (smaller box area) synt images, removing then and moving on to yet 
# Thus we hope to find even quite smnall real wheat heads, when we 
# can also reduce the threshold, to "scrape-in" the last wheat heads.
#
allowed_IoU = 0.2
removed = []
for m1, maxi1 in enumerate(maxi):
	for m2, maxi2 in enumerate(maxi):
		if m2 == m1:
			break
		# 
		# If too much intersection over union then 
		# remoive either smaller region
		#		      or lower scoring region
		#             or a combination of the two factors
		#
		if IoU(maxi1, maxi2) > allowed_IoU:

			#
			# decide on either case 1 or case 2, 
			# based on product of score and area
			#
			
			
			if case == 3:
				s1 = math.sqrt(maxi1[6]) * maxi1[4]	#score bias
				s2 = math.sqrt(maxi2[6]) * maxi2[4]
				if s1 > s2:
					if m2 not in removed:
						removed.append(m2)
				else:
					if m1 not in removed:
						removed.append(m1)

			elif case == 1:
			
				# Remove smaller region
				if maxi1[6] > maxi2[6]:
					if m2 not in removed:
						removed.append(m2)
				else:
					if m1 not in removed:
						removed.append(m1)
			elif case == 2:
				# Remove lower score
				if maxi1[4] > maxi2[4]:
					if m2 not in removed:
						removed.append(m2)
				else:
					if m1 not in removed:
						removed.append(m1)
			xc=1
					
 

rf_in  = os.path.join(GWCD, real_file+".png")
rf_out = os.path.join(RESULT, real_file+"_EVAL.png")
save_with_boxes(rf_out, maxi, removed)
print(f"Produced: {rf_out}")


