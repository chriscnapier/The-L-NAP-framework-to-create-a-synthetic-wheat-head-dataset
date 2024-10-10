#
# L_NAPD.py
# --------
# Function: To create Metadata .json files, from synthetic plant view files.
# Metadata files are combined as a Dataset in Detectron2 format.
#
# Can be used in training neural network Detectron2. 
# Json files define the bounding boxes and masks of each and every 
# view file, 
# and additionally create visuals in TEMP which allow us 
# to check if the data are correct.
#
# This script is run from directory L_NAP > Apps
#
# Input:   VIEW   - Synthetic Image view files
# Output:  RESULT - Json Metadata files
#          TEMP   - Png files showing result view images with 
#                   attached bounding boxes, masks and captions
#
# After the run the RESULT files should be moved to META
# 
#
from skimage.io import imread
from skimage.color import rgb2gray, rgba2rgb
from skimage import measure

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import copy

import sys
import os	# Operating system: used for file I/O
import json	# Create a json file

import numpy as np

from L_NAP_DIRS import *    # VIEW, RESULT, TEMP
pass


#THE_ONE != "" means just process the given one file and stop
THE_ONE = "Wheat_0074_131_022.jpg"

# LIMIT means process this given number of files from the first 
# and stop.
LIMIT = -1         # This means NO limit

def save_data(data, out_path):
    """
    Write data as a dict to given json file, at out_path, and
    return number of written dict items
    """
    written = len(data)
    
    if written > 0:
        file = open(out_path, "w")
        file.write(json.dumps(data, indent=4))
        file.close()
        """ or
        with open("out_path", "w") as file:
            json.dump(data, file, indent=4)
        """
    return written
    
def image_data(image_id, in_path, image_width, image_height, 
                box, mask, category):
    """
    Create a dict of the data required by Detectron2 for one image
    which is the image identiry, image path, and image size, 
    followed by the image annotations comprising a category, 
    a bounding box, and a segmentation RLE mask.
    """
    #
    # Each RLE run is a sequence of consecutive pixels from a given
    # flattened-mask-x-start and of a given x-length in pixels.
    # For example runs == array([322,66, 1286,64, 2243,62, ...],
    # dtype=int32) is three runs of (flattened-x-start, x-length) of
    # (322,66), (1283,64), (2243,62).
    #
    flat_mask = np.concatenate([[0], mask.reshape(-1), [0]])
    rle_runs = np.where(flat_mask[1:] != flat_mask[:-1])[0] + 1
    rle_runs[1::2] -= rle_runs[::2]
    rle_runs[0::2] -= 1 # reduce each start index to compensate for 
                        # leading [0] concatenate above
    #
    # NOTE: In fact if a run from one y-row continues onto the next 
    # y-row it is incorrectly taken as the SAME run. 
    # If we expect runs to be separate then this is incorrect, 
    # but if we correctly reverse the process, when the array
    # is unflattened, then the runs are again separate.
    # This "error" is important if we use the runs to show 
    # a mask-outline, as in L_NAPe.py, when we must check for overruns
    # at the end of each run, where pixels would be placed beyond 
    # or at x_width and cause L_NAPe.py to crash!
    # 
    
    rle_str = ' '.join(str(x) for x in rle_runs)
    rle_list = rle_runs.tolist()
    
    #x1, y1 = topleft
    
    in_file = os.path.basename(in_path)
    data = {
		'image_id':  	image_id,
		'file_name': 	in_file,
		'width':     	image_width,
		'height':    	image_height,
		'annotations':  []
		}

    data['annotations'].append(
        {
        'id' : 1,
		'category_id':	category,
        'bbox':         [box[0], box[1], box[2], box[3]],
        'bbox_mode':    0,
        'segmentation': 
            {
            'size':   	[image_height, image_width],
            'counts': 	rle_list 
            }
        })

    return data

#
# Create a new_filename from old_filename with the given bounding boxes 
# placed on it for view 
#	   
def save_with_box_and_mask(image_id, in_path, out_base, 
                             box, mask, grain_rows):
	
    # get coordinates as int type
    # and calculate width and height of the box
    x1, y1, x2, y2 = box
    box_width, box_height = x2 - x1, y2 - y1
    
    # load the image (zero indicates png file with no header checking)
    # and make a real copy to data2, which will become a mask in a moment
    data = plt.imread(in_path, 0)
    data2 = copy.deepcopy(data)
    
    (image_height, image_width, channels) = data.shape
    #--print (f"Image_width: {image_width}, Image_height: {image_height}")
    
    # Offset the mask image 10 pixels left or right of the view image
    off = box_width+10
    if x1-off < 0:
        off = -off
    #
    # Place a white mask as data2 beside data (for each y-column),
    #
    y = y1
    while y <= y2:
        x = x1
        while x <= x2:
            if mask[y][x] == 1:
                data2[y][x-off][0] = 255
                data2[y][x-off][1] = 255
                data2[y][x-off][2] = 255
            x += 1
        y += 1
    
    # load the extended image (mask beside view image)
    plt.imshow(data2)
    # get the context for drawing boxes
    cx = plt.gca()

    # plot box on image
    
    data = {}

    # if possible create the shape, and add box view image in the context
    if box_width > 0 and box_height > 0:
        rect = Rectangle((x1, y1), box_width, box_height, fill=False, color='red')
    
        # draw the box with view number as caption
        cx.add_patch(rect)
        caption = f"{grain_rows}"
        
        # Add view number onto image context top left, for identification
        cx.text(x1, y1, caption, size=7.5, verticalalignment='top',
                color='w', backgroundcolor="none")
 
        # Write out to Json file for Detectron2 data
        category = int(grain_rows)
        
        data = image_data(
                image_id, in_path, image_width, image_height, 
                box, mask, category)
		
    # (show)save the plot, and remove the figure and the plot - 
    # Must use plt.close('all') here - I found eventually.'
    out_mask = os.path.join(TEMP, out_base + "_mask.png")
    plt.savefig(out_mask)
    fig = plt.figure()
    fig.clear()
    plt.clf()
    plt.close('all')
    
    out_json = os.path.join(RESULT, out_base + ".json")
    save_data(data, out_json)
    
#
# Run the L_NAPD pipeline
# ---------------------- 
def run_pipeline(in_dir):
    """
    Read view files from in_dir compute and write bbox and masks to out_dir,
    to the LIMIT number
    """
    image_id = 0
    print(f"\n\nin_dir: {in_dir}")
    
    #
    # Import each sorted-by-name vn view in_file (.png) in in_dir, 
    # and calculate bbox and Mask and save to json file,
    # and to new validatation data .png files.
    #
    nfiles = 0
    one_done = False
    for mn, in_file in enumerate(sorted(os.listdir(in_dir)), start=1):
        
        i = in_file.rfind('.')
        ext = in_file[i:]
        if ext == '.jpg':
            out_base = in_file[:i]
        
            #if in_file.endswith(".png"):
            # Next view vn of model
            
            if LIMIT != -1 and nfiles >= LIMIT:
                break
		
            if THE_ONE != "":
                 if one_done:		# Finish now since THE_ONE is processed
                     break
                 elif in_file == THE_ONE:
                     one_done = True	# Finish after doing THE_ONE file
                 else:
                     continue		# Skip this not THE_ONE file
		
            nfiles += 1
            in_path = os.path.join(in_dir, in_file)	    
            print(f"In:  {in_path}")
	    
            original = imread(in_path)
            #--python warnimg on: 
            img = rgb2gray(original)
            #img = rgb2gray(rgba2rgb(original))
	    
            ylen, xlen = img.shape
	    
            threshold = (img[0][0] + img[ylen-1][0] + img[ylen-1][xlen-1] + img[0][xlen-1])/4 
            mask_bool = img > threshold
            mask = np.multiply(mask_bool, 1)
	    
            # bbox itself
            ybmin = ylen
            ybmax = 0
            xbmin = xlen
            xbmax = 0
	    
            vmax = 0
            vmin = 0
	    
            # for each x
            for x in range(xlen):
                ymin = ylen
                ymax = 0
                for y in range(ylen):
                    value = img[y][x]
                    if value > threshold:
                        if y < ymin:
                           ymin = y
                        elif y > ymax:
                            ymax = y
			    
                        if x < xbmin:
                            xbmin = x
                        elif x > xbmax:
                            xbmax = x
			    
                        if vmin == 0 or value < vmin:
                            vmin = value
                        elif value > vmax:
                            vmax = value
			    
                if ymin < ybmin:
                    ybmin = ymin
                elif ymax > ybmax:
                    ybmax = ymax
            #
            # The grain-count is in the filename Wheat_WHNR_GRC_VN.png
            # where WHNR is wheat head number, GRC is grain count, 
            # and VN is the view number
            #
            box = (xbmin, ybmin, xbmax, ybmax)
	    
            grains = int(in_file[11:14])
            grain_rows = grains / 10.0
	    
            image_id += 1
            save_with_box_and_mask(image_id, in_path, out_base, 
                                    box, mask, grain_rows)
            pass
            
    return nfiles

			
def main():
    """
    Start the L_NAPm pipeline:
    """
    #
    # Run the pipiline from views to annotations in RESULT,
    # and png visuals in TEMP.
    #  
    nfiles = run_pipeline(VIEW)
    print(f"The number of data files is: {nfiles}")
    
    return 0
	
if __name__ == '__main__':
    sys.exit(main())
	



