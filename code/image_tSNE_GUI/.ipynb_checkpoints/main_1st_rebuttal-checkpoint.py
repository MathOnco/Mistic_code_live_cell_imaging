### Code for Mistic 
### Image t-SNE viewer for multiplexed images
### 
### code author Sandhya Prabhakaran
###
### Revision history
### FoV code ###
### Jan 29th 2021
### 25th June 2021
### github version
### 19th Jan 2022
### added Patient id live canvas
### 26th Jan 2022 ###
### merging the stack montage code 
### prior version is main_rollback. 
### 14th Feb 2022
### adding codex, tcycif, vectra option 
### prior version is main_rollback_1
### 14th mar 2022
### added the user tsne as well 'arrange in rows' (seeall) tsne generation code 
### so now with a shuffle as 'yes' at onset all options would work. (with no predefined tsne) 
### also in predefined case, both random and arrange in rows coords are available so that part is commented out from no-shuffle option. Both no-shuffle and shuffle options just read the corresponding files per options chosen by user. 

#### code for github is in main_for_github.py
#### any changes here or there should reflect in either place!!

###5th April -8th April 2022
### this code has everything we did for the 1st rebuttal
### refer to main.py for 2nd rebuttal updates


import os
import sys
import random
import warnings

import numpy as np
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from matplotlib.figure import Figure 

from matplotlib import cm

from scipy import ndimage

from sklearn.manifold import TSNE

import phenograph as pg
from scipy.stats import zscore

from skimage.color import rgb2gray

from matplotlib.patches import Polygon

from skimage import io

from skimage import data
from skimage.filters import threshold_otsu
from skimage.segmentation import clear_border
from skimage.measure import label, regionprops
from skimage.morphology import closing, square
from skimage.color import label2rgb
from skimage.io import imread, imshow, imread_collection, concatenate_images
from skimage.transform import resize
from skimage.morphology import label

import seaborn as sns

import scipy.spatial

from scipy.spatial import distance


import seaborn as sns


import matplotlib.image as mpimg 


import matplotlib.colors as colors 

from matplotlib import colors as mcolors

colors = dict(mcolors.BASE_COLORS, **mcolors.CSS4_COLORS)

from PIL import Image, ImageOps

from bokeh.layouts import column, row
from bokeh.models import (Select, Button)
from bokeh.palettes import Spectral5
from bokeh.plotting import curdoc, figure
from bokeh.models.widgets import Div
from bokeh.layouts import column, layout

from bokeh.models import (HoverTool, ColumnDataSource)
from bokeh.models.widgets import RadioButtonGroup
from bokeh.models import CheckboxGroup
from bokeh.models import CustomJS
from bokeh.models import BoxSelectTool
from bokeh.themes import Theme

from bokeh.models.widgets import Panel, Tabs
from bokeh.io import output_file, show

## 26th Jan 2022
##
import skimage.io as io
import tifffile
from PIL import TiffImagePlugin




### image-tSNE

width = 5000 #15000
height = 5000
max_dim = 500
tw =1200 # 1344
th = 900 #1008

full_image_1 = Image.new('RGBA', (width, height))



##############################################################
 
################## Function definitions ######################

##############################################################


#######################################################################
#####  get_cell_coords(), get_neighbours(), point_valid(),         ####
#####  get_point() are functions to generate random points         ####
#####  functions modified from:                                    ####
#####  https://scipython.com/blog/poisson-disc-sampling-in-python/ ####
#######################################################################



def get_cell_coords(pt,a):
    """Get the coordinates of the cell that pt = (x,y) falls in."""

    return int(pt[0] // a), int(pt[1] // a)

def get_neighbours(coords,nx,ny,cells):
    """Return the indexes of points in cells neighbouring cell at coords.
    For the cell at coords = (x,y), return the indexes of points in the cells
    with neighbouring coordinates illustrated below: ie those cells that could 
    contain points closer than r.
                                     ooo
                                    ooooo
                                    ooXoo
                                    ooooo
                                     ooo
    """

    dxdy = [(-1,-2),(0,-2),(1,-2),(-2,-1),(-1,-1),(0,-1),(1,-1),(2,-1),
            (-2,0),(-1,0),(1,0),(2,0),(-2,1),(-1,1),(0,1),(1,1),(2,1),
            (-1,2),(0,2),(1,2),(0,0)]
    neighbours = []
    for dx, dy in dxdy:
        neighbour_coords = coords[0] + dx, coords[1] + dy
        if not (0 <= neighbour_coords[0] < nx and
                0 <= neighbour_coords[1] < ny):
            # We're off the grid: no neighbours here.
            continue
        neighbour_cell = cells[neighbour_coords]
        if neighbour_cell is not None:
            # This cell is occupied: store this index of the contained point.
            neighbours.append(neighbour_cell)
    return neighbours

def point_valid(pt,a,nx,ny,cells,samples,r):
    """Is pt a valid point to emit as a sample?
    It must be no closer than r from any other point: check the cells in its
    immediate neighbourhood.
    """

    cell_coords = get_cell_coords(pt,a)
    for idx in get_neighbours(cell_coords,nx,ny,cells):
        nearby_pt = samples[idx]
        # Squared distance between or candidate point, pt, and this nearby_pt.
        distance2 = (nearby_pt[0]-pt[0])**2 + (nearby_pt[1]-pt[1])**2
        if distance2 < r**2:
            # The points are too close, so pt is not a candidate.
            return False
    # All points tested: if we're here, pt is valid
    return True

def get_point(k, refpt,r,a,nx,ny,cells,samples):
    """Try to find a candidate point relative to refpt to emit in the sample.
    We draw up to k points from the annulus of inner radius r, outer radius 2r
    around the reference point, refpt. If none of them are suitable (because
    they're too close to existing points in the sample), return False.
    Otherwise, return the pt.
    """
    i = 0
    while i < k:
        rho, theta = np.random.uniform(r, 2*r), np.random.uniform(0, 2*np.pi)
        pt = refpt[0] + rho*np.cos(theta), refpt[1] + rho*np.sin(theta)
        if not (0 <= pt[0] < width and 0 <= pt[1] < height):
            # This point falls outside the domain, so try again.
            continue
        if point_valid(pt,a,nx,ny,cells,samples,r):
            return pt
        i += 1
    # We failed to find a suitable point in the vicinity of refpt.
    return False

###############################################################
### draw_tSNE_scatter()                                    ####
### a) creates the metadata-based tSNE scatter plots       #### 
### b) populates the hover functionality for each tSNE dot ####
###############################################################

def draw_tSNE_scatter(tsne1, file_name_hover,cluster_ms_list ):
    tsne=np.asarray(tsne1)    
    
    source = ColumnDataSource(data=dict(
        x=tsne[:,0],
        y=tsne[:,1],
        pat_list = pat_ind_list, 
        res_list = resp_list,
        fov_list = pat_fov_list,
        color_vec_list = color_vec,
        tx_list = tx_list,
        color_vec_tx_list = color_vec_tx,
        clust_asgn_list = clust_asgn_list,
        color_vec_clasgn_list = color_vec_clasgn,
        cluster_anno_list = cluster_anno_list,
        cluster_ms_list = cluster_ms_list, #20th jan 2022
        cluster_pat_list = cluster_pat_list, #19th Jan 2022
        color_vec_patid_list = color_vec_patid, #19th Jan 2022
        file_name_hover_list = file_name_hover #19th Jan 2022
        #legend_p11 = legend_p1
    ))
    TOOLS="hover,pan,crosshair,wheel_zoom,zoom_in,zoom_out,box_zoom,undo,redo,reset,tap,save,box_select,poly_select,lasso_select,"

    TOOLTIPS = [
        ("index", "$index"),
        ("(x,y)", "($x, $y)"),
        ("Pat_id", "@pat_list"),
        ("Response", "@res_list"),
        ("Treatment", "@tx_list"), #19th Jan 2022
        ("Cluster id", "@clust_asgn_list"), #19th Jan 2022
        ("Channel", "@cluster_ms_list"), #20th jan 2022
        ("Thumbnail", "@file_name_hover_list"), #19th Jan 2022
        ("FoV","@fov_list")
    ]




    p1 = figure(plot_width=400, plot_height=400, tooltips=TOOLTIPS,tools = TOOLS,
               title="Patient response")
    #26th Feb 2021
    p1.scatter('x', 'y', size=10, source=source, legend= 'res_list', color = 'color_vec_list',fill_alpha=0.6)
    p1.legend.location = "bottom_left"

    #8th June 2021
    p2 = figure(plot_width=400, plot_height=400, tooltips=TOOLTIPS,tools = TOOLS,
               title="Treatment category")
    p2.scatter('x', 'y', size=10, source=source, legend= 'tx_list', color = 'color_vec_tx_list',fill_alpha=0.6)
    p2.legend.location = "bottom_left"
    
    #8th June 2021
    p3 = figure(plot_width=400, plot_height=400, tooltips=TOOLTIPS,tools = TOOLS,
               title="Cluster annotations")
    p3.scatter('x', 'y', size=10, source=source, legend= 'cluster_anno_list', color = 'color_vec_clasgn_list',fill_alpha=0.6)
    p3.legend.location = "bottom_left"

    
    #19th Jan 2022
    p4 = figure(plot_width=400, plot_height=400, tooltips=TOOLTIPS,tools = TOOLS,
               title="Patient id")
    p4.scatter('x', 'y', size=10, source=source, legend= 'cluster_pat_list', color = 'color_vec_patid_list',fill_alpha=0.6)
    p4.legend.location = "bottom_left"

    
    return ([p1,p2,p3,p4, source])


###

                            







##############################################################################################
### generate_stack_montage()                                                              ####
### a) reads in and processes the image channels                                          ####
### b) generates evenly-spaced points on the static canvas to arrange the images in rows  ####
### c) generates thumbnails, and pastes these onto the static canvas                      ####
### d) stores the thumbnails in the output folder                                         ####
### e) updates the hover tool with thumbnail paths, marker names and metadata             ####
##############################################################################################  
    
    
################## 26th jan 2022
def generate_stack_montage(chk_box_marker_sm, rb_imtech_val, LABELS_MARKERS):
    

    
    full_image = Image.new('RGBA', (width, height))
    size = [256,256]

    file_name_hover = [] # 19th Jan 2022
    file_name_hover_list = [] # 19th Jan 2022    

    # Choose up to k points around each reference point as candidates for a new
    # sample point
    k = 10

    # Minimum distance between samples
    r = 2

    width_1, height_1 = 20, 22

    print('Arrange images side-by-side')

    # Cell side length
    a = r/np.sqrt(2)
    # Number of cells in the x- and y-directions of the grid
    nx, ny = int(width_1 / a) + 1, int(height_1 / a) + 1

    # A list of coordinates in the grid of cells
    coords_list = [(ix, iy) for ix in range(nx) for iy in range(ny)]


    #logic to get grid points - 29th March 2021
    m = np.int(np.floor(nx*ny/num_images))


    row_needed = []
    def multiples(m, num_images):
        for i in range(num_images):
            row_needed.append(i*m)

    multiples(m,num_images)


    select_coords = np.array(coords_list)[np.array(row_needed).flatten()]

    print(type(select_coords))
    ################

    #tsne = np.asarray(coords_list)
    tsne = select_coords
    df_Xtsne = pd.DataFrame(tsne)
    df_Xtsne.to_csv(os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE_sm.csv'), header=None, index=None)

            
    # 26th spril 2021
    # save the tSNE points to bve read later on irrespective of whoch option was chosen
    df_Xtsne_touse = pd.DataFrame(tsne)
    df_Xtsne_touse.to_csv(os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE_touse_sm.csv'), header=None, index=None)

    tx, ty = tsne[:,0], tsne[:,1]
    tx = (tx-np.min(tx)) / (np.max(tx) - np.min(tx))
    ty = (ty-np.min(ty)) / (np.max(ty) - np.min(ty))
    print('###tx')
    print(tx)
    print(ty)
    inds = range(len(marker_image_list))

    N = len(inds)


    for k in range(len(inds)):
      
        image_all_2 = []
        image_all_1 = []
        #im = io.imread(marker_image_list[inds[k]])#,plugin='matplotlib') #26th jan 2022
        #im = tifffile.imread(marker_image_list[inds[k]])
        im = Image.open(marker_image_list[inds[k]])
             
            
        for m in range(1):
            image = im

            median_filtered = scipy.ndimage.median_filter(image, size=1)
            image_all_2.append(median_filtered)


            # apply threshold

            thresh = threshold_otsu(image_all_2[m])




            print('thresh is: ', str(thresh))
            
            bw = closing(image > thresh, square(1))

            # remove artifacts connected to image border
            cleared_imtsne = clear_border(bw)


            image_all_1.append(cleared_imtsne*100)

        tl = sum(image_all_1)
        
        if (rb_imtech_val ==0): #vectra
            tile_1 = Image.fromarray(np.uint8(cm.viridis(tl)*255))

        elif (rb_imtech_val ==1): #t-CyCIF
            tile_1 = Image.fromarray(np.uint8(cm.hsv(tl)*500)) #20th jan 2022
        elif (rb_imtech_val ==2): # CODEX
             tile_1 = Image.fromarray(np.uint8(cm.jet(tl)*255)) #20th jan 2022

        old_size = tile_1.size


        ##25th jan 2022 below


        new_size = (old_size[0]+1, old_size[1]+1)
        new_im = Image.new("RGB", new_size,color='black')

        new_im.paste(tile_1, (int((new_size[0]-old_size[0])/2),int((new_size[1]-old_size[1])/2)))



        file_name = os.path.join(path_wd+'/output_tiles/sm_image_tsne_tils'+str(k)+'.png')

        file_name_hover.append('sm_image_tsne_tils'+str(k)+'.png') # 24th jan 2022 file_name) #19th Jan 2022

        new_im.save(file_name) #2nd Feb 2021

        # Read Images 


        tile_2 = Image.open(file_name)
        rs = max(1, tile_2.width/max_dim, tile_2.height/max_dim)
        tile_2 = tile_2.resize((int(tile_2.width/rs), int(tile_2.height/rs)), Image.ANTIALIAS) #commented antialias on 9th Feb 2021

        full_image.paste(tile_2, (int((width-max_dim)*ty[k]), int((height-max_dim)*tx[k])),mask=tile_2.convert('RGBA'))

    matplotlib.pyplot.figure(figsize = (25,20))
    plt.imshow(full_image)
    plt.axis('off')
    #return (full_image)



    ###5th March 2021
    k = random.randint(2,500)
    file_name = os.path.join(path_wd+'/image_tSNE_GUI/static/sm_image_tsne_tils_all_'+str(k)+'.png')
    full_image.save(file_name)



    rotated_img     = full_image.rotate(90)
    file_name_rot = os.path.join(path_wd+'/image_tSNE_GUI/static/sm_image_tsne_tils_all_'+str(k)+'_rot.png')


    rotated_img.save(file_name_rot)

    return([file_name_rot,tsne, file_name_hover]) #19th Jan 2022 (added file_name_hover)     
        
        

###########################################################################################################
### generate_image_tSNE()                                                                          ######## 
###                                                                                                ########
### a) reads in and pre-processes the images                                                       ######## 
### b) generates random points or evenly-spaced points on the static canvas to arrange the images  ########
###                      in rows or reads in the user-provided tSNE                                ########
### c) generates thumbnails based on border choices, pastes the thumbnails onto the static canvas  ########
### d) stores the thumbnails in the output folder                                                  ########
### e) updates the hover tool with thumbnail paths                                                 ########
### f) shuffle or no shuffle option is handled in this function where images are randomly shuffled ########
###########################################################################################################    

def generate_image_tSNE(chk_box_marker,rb_val,rb_rs_val,rb_shf_val, rb_imtech_val, mc, wc, LABELS_MARKERS):
    full_image = Image.new('RGBA', (width, height))
    size = [256,256]

    file_name_hover = [] # 19th Jan 2022
    file_name_hover_list = [] # 19th Jan 2022
    
    if (rb_shf_val == 0): # no shuffle option
        
        
        #added 14th March 2022
        #pick the tsne file to start with
        if(rb_rs_val==1):
            df_Xtsne = pd.read_csv(os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE_user.csv'), index_col=None, header= None)
            print('usertsne')
        elif(rb_rs_val==0):
            df_Xtsne = pd.read_csv(os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE.csv'), index_col=None, header= None)
            print('origtsne')
            
        elif(rb_rs_val==2):
            df_Xtsne = pd.read_csv(os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE_seeall.csv'), index_col=None, header= None)
            print('seealltsne')
            
        tsne = np.array(df_Xtsne)   
        
        ''' commented out 14th March 2022   
        #create the random tsne projections
        if (rb_rs_val==1):
            # Choose up to k points around each reference point as candidates for a new
            # sample point
            k = 10

            # Minimum distance between samples
            r = 1.7

            width_1, height_1 = 20, 22

            print('Generating random co-ordinates')

            # Cell side length
            a = r/np.sqrt(2)
            # Number of cells in the x- and y-directions of the grid
            nx, ny = int(width_1 / a) + 1, int(height_1 / a) + 1

            # A list of coordinates in the grid of cells
            coords_list = [(ix, iy) for ix in range(nx) for iy in range(ny)]
            # Initilalize the dictionary of cells: each key is a cell's coordinates, the
            # corresponding value is the index of that cell's point's coordinates in the
            # samples list (or None if the cell is empty).
            cells = {coords: None for coords in coords_list}



            # Pick a random point to start with.
            pt = (np.random.uniform(0, width_1), np.random.uniform(0, height_1))
            samples = [pt]
            # Our first sample is indexed at 0 in the samples list...
            cells[get_cell_coords(pt,a)] = 0
            # ... and it is active, in the sense that we're going to look for more points
            # in its neighbourhood.
            active = [0]

            nsamples = 1
            # As long as there are points in the active list, keep trying to find samples.
            while (nsamples < num_images): #active:
                # choose a random "reference" point from the active list.
                idx = np.random.choice(active)
                refpt = samples[idx]
                # Try to pick a new point relative to the reference point.
                pt = get_point(k, refpt,r,a,nx,ny,cells,samples)
                if pt:
                    # Point pt is valid: add it to the samples list and mark it as active
                    samples.append(pt)
                    nsamples += 1
                    active.append(len(samples)-1)
                    cells[get_cell_coords(pt,a)] = len(samples) - 1
                    print('nsamples is: ',str(nsamples))
                else:
                    # We had to give up looking for valid points near refpt, so remove it
                    # from the list of "active" points.
                    active.remove(idx)

            tsne = np.asarray(samples)
            df_Xtsne = pd.DataFrame(tsne)
            df_Xtsne.to_csv(os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE_user.csv'), header=None, index=None)


        elif(rb_rs_val==0):

            df_Xtsne = pd.read_csv(os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE.csv'), index_col=None, header= None)
            df_Xtsne.shape
            tsne = np.array(df_Xtsne )
            
        elif(rb_rs_val==2):
            
            # Choose up to k points around each reference point as candidates for a new
            # sample point
            k = 10

            # Minimum distance between samples
            r = 2

            width_1, height_1 = 20, 22

            print('Arrange images side-by-side')

            # Cell side length
            a = r/np.sqrt(2)
            # Number of cells in the x- and y-directions of the grid
            nx, ny = int(width_1 / a) + 1, int(height_1 / a) + 1

            # A list of coordinates in the grid of cells
            coords_list = [(ix, iy) for ix in range(nx) for iy in range(ny)]
           
        
            #logic to get grid points - 29th March 2021
            m = np.int(np.floor(nx*ny/num_images))
       
            
            row_needed = []
            def multiples(m, num_images):
                for i in range(num_images):
                    row_needed.append(i*m)
        
            multiples(m,num_images)
            
           
            #print(num_images)
            #print(np.array(row_needed).flatten())
            select_coords = np.array(coords_list)[np.array(row_needed).flatten()]
            
            print(type(select_coords))
            ################
            
            #tsne = np.asarray(coords_list)
            tsne = select_coords
            df_Xtsne = pd.DataFrame(tsne)
            df_Xtsne.to_csv(os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE_seeall.csv'), header=None, index=None)

        '''    
        # 26th April 2021
        # save the tSNE points to bve read later on irrespective of whoch option was chosen
        df_Xtsne_touse = pd.DataFrame(tsne)
        df_Xtsne_touse.to_csv(os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE_touse.csv'), header=None, index=None)
            
        tx, ty = tsne[:,0], tsne[:,1]
        tx = (tx-np.min(tx)) / (np.max(tx) - np.min(tx))
        ty = (ty-np.min(ty)) / (np.max(ty) - np.min(ty))
    

        
        ##identify the markers - 26th March 2021
        mm = np.asarray(LABELS_MARKERS)[chk_box_marker]
        
        tiles = []


        marker_choice = np.array(mc)[chk_box_marker] #31st Jan 2022
        weight_choice = np.array(wc)[chk_box_marker] #31st Jan 2022


        
        inds = range(len(marker_image_list))

        N = len(inds)

        
        for k in range(len(inds)):
            
            image_all_2 = []
            image_all_1 = []
           

            
            #im = io.imread(marker_image_list[inds[k]])#,plugin='matplotlib') #26th jan 2022
            im = tifffile.imread(marker_image_list[inds[k]])
            if (rb_imtech_val ==2): #for codex
                im = im.reshape(64,5040,9408) ##hardcoded cycif remove # 11th feb 2022
            
            #print (im.shape)    
            
            for m in range(len(marker_choice)):
                image = im[marker_choice[m]]

                median_filtered = scipy.ndimage.median_filter(image, size=1)
                image_all_2.append(median_filtered)


                # apply threshold

                thresh = threshold_otsu(image_all_2[m])




                print('thresh is: ', str(thresh))
             
                bw = closing(image > thresh, square(1))

                # remove artifacts connected to image border
                cleared_imtsne = clear_border(bw)


                image_all_1.append(cleared_imtsne*weight_choice[m]) #10

            tl = sum(image_all_1)



            #tile_1 = Image.fromarray(np.uint8(cm.jet(tl)*255)) #11th Feb 2022 for codex #14th feb 2022

            #14th feb 2022
            if (rb_imtech_val ==0): #vectra
                tile_1 = Image.fromarray(np.uint8(cm.viridis(tl)*255))

            elif (rb_imtech_val ==1): #t-CyCIF
                tile_1 = Image.fromarray(np.uint8(cm.jet(tl)*255)) #20th jan 2022 #500?
            elif (rb_imtech_val ==2): # CODEX
                 tile_1 = Image.fromarray(np.uint8(cm.jet(tl)*255)) #20th jan 2022


            old_size = tile_1.size

            
            ##25th jan 2022 below
            
            if(rb_val==0): 
                new_size = (old_size[0]+1, old_size[1]+1)
                new_im = Image.new("RGB", new_size,color='black')
                
            elif(rb_val==1): # for the border #response based 
                new_size = (old_size[0]+50, old_size[1]+50)



                new_im = Image.new("RGB", new_size,color_vec[inds[k]])## color='yellow')
                
            elif(rb_val==2): # for the border #treatment based 
                new_size = (old_size[0]+50, old_size[1]+50)


                new_im = Image.new("RGB", new_size,color_vec_tx[inds[k]])# color='yellow')
            
            elif(rb_val==3): # for the border #cluster based 
                new_size = (old_size[0]+50, old_size[1]+50)


                new_im = Image.new("RGB", new_size,color_vec_clasgn[inds[k]])# colours_58[cx])# color='yellow')
                

            elif(rb_val==4): # for the border #patient id  based 
                new_size = (old_size[0]+50, old_size[1]+50)


                new_im = Image.new("RGB", new_size, color_vec_patid[inds[k]])# color='yellow')
            #25th jan 2022 comment
            '''            
            elif(rb_val==0): 
                new_size = (old_size[0]+1, old_size[1]+1)
                new_im = Image.new("RGB", new_size,color='black')
            '''    
            new_im.paste(tile_1, (int((new_size[0]-old_size[0])/2),int((new_size[1]-old_size[1])/2)))



            file_name = os.path.join(path_wd+'/output_tiles/image_tsne_tils'+str(k)+'.png')

            file_name_hover.append('image_tsne_tils'+str(k)+'.png') # 24th jan 2022 file_name) #19th Jan 2022

            new_im.save(file_name) #2nd Feb 2021

            # Read Images 


            tile_2 = Image.open(file_name)
            rs = max(1, tile_2.width/max_dim, tile_2.height/max_dim)
            tile_2 = tile_2.resize((int(tile_2.width/rs), int(tile_2.height/rs)), Image.ANTIALIAS) #commented antialias on 9th Feb 2021

            full_image.paste(tile_2, (int((width-max_dim)*ty[k]), int((height-max_dim)*tx[k])),mask=tile_2.convert('RGBA'))



        matplotlib.pyplot.figure(figsize = (25,20))
        plt.imshow(full_image)
        plt.axis('off')
        #return (full_image)



        ###5th March 2021
        k = random.randint(2,500)
        file_name = os.path.join(path_wd+'/image_tSNE_GUI/static/image_tsne_tils_all_'+str(k)+'.png')
        full_image.save(file_name)


 
        rotated_img     = full_image.rotate(90)
        file_name_rot = os.path.join(path_wd+'/image_tSNE_GUI/static/image_tsne_tils_all_'+str(k)+'_rot.png')


        rotated_img.save(file_name_rot)
        
        
        
        
    ##code for reshuffling
    
    elif (rb_shf_val==1): # shuffle images 
        
        #pick the tsne file to start with
        if(rb_rs_val==1):
            df_Xtsne = pd.read_csv(os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE_user.csv'), index_col=None, header= None)
            print('usertsne')
        elif(rb_rs_val==0):
            df_Xtsne = pd.read_csv(os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE.csv'), index_col=None, header= None)
            print('origtsne')
            
        elif(rb_rs_val==2):
            df_Xtsne = pd.read_csv(os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE_seeall.csv'), index_col=None, header= None)
            print('seealltsne')
            
        tsne = np.array(df_Xtsne)   
        
        
        # 26th spril 2021
        # save the tSNE points to be read later on, irrespective of which option was chosen
        df_Xtsne_touse = pd.DataFrame(tsne)
        df_Xtsne_touse.to_csv(os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE_touse.csv'), header=None, index=None)
        
        
        tx, ty = tsne[:,0], tsne[:,1]
        tx = (tx-np.min(tx)) / (np.max(tx) - np.min(tx))
        ty = (ty-np.min(ty)) / (np.max(ty) - np.min(ty))
            
        full_image = Image.new('RGBA', (width, height))
        
        size = [256,256]

        
        ##identify the markers - 26th March 2021
        mm = np.asarray(LABELS_MARKERS)[chk_box_marker]
        
        tiles = []

                                
        marker_choice = np.array(mc)[chk_box_marker] #31st Jan 2022 #[3,5]
        weight_choice = np.array(wc)[chk_box_marker] #31st Jan 2022 #[800,100]

        inds = range(len(marker_image_list))

        N = len(inds)
        shf_N = np.array(range(N))     
        random.shuffle(shf_N)
        print("#############shuffle file order$$$")
        print(shf_N)
        count_file = 0 #19th feb 2022
        
        for k in range(N): #19th feb 2022
            
            image_all_2 = []
            image_all_1 = []
           

            
            #im = io.imread(marker_image_list[shf_N[k]])#,plugin='matplotlib') #26th jan 2022  
            im = tifffile.imread(marker_image_list[shf_N[k]]) #19th feb 2022
            if (rb_imtech_val ==2): #for codex
                im = im.reshape(64,5040,9408) ##hardcoded cycif remove # 11th feb 2022
         
            for m in range(len(marker_choice)):
                image = im[marker_choice[m]]

                median_filtered = scipy.ndimage.median_filter(image, size=1)
                image_all_2.append(median_filtered)



                # apply threshold
 
                thresh = threshold_otsu(image_all_2[m])

                                
                print(thresh)
            
                bw = closing(image > thresh, square(1))

                # remove artifacts connected to image border
                cleared_imtsne = clear_border(bw)


                image_all_1.append(cleared_imtsne*weight_choice[m]) #10

            tl = sum(image_all_1)
            #tile_1 = Image.fromarray(np.uint8(cm.viridis(tl)*255)) #14th feb 2022
            
            
            #14th Feb 2022
            
            if (rb_imtech_val ==0): #vectra
                tile_1 = Image.fromarray(np.uint8(cm.viridis(tl)*255))

            elif (rb_imtech_val ==1): #t-CyCIF
                tile_1 = Image.fromarray(np.uint8(cm.jet(tl)*255)) #20th jan 2022
            elif (rb_imtech_val ==2): # CODEX
                 tile_1 = Image.fromarray(np.uint8(cm.jet(tl)*255)) #20th jan 2022
            old_size = tile_1.size

            print(pat_ind_list[shf_N[k]])

            # 25th jan 2022
            if(rb_val==0): 
                new_size = (old_size[0]+1, old_size[1]+1)
                new_im = Image.new("RGB", new_size,color='black')
                
            elif(rb_val==1): # for the border #response based 
                new_size = (old_size[0]+50, old_size[1]+50)




                new_im = Image.new("RGB", new_size,color_vec[shf_N[k]])# color='yellow')
                
            elif(rb_val==2): # for the border #treatment based 
                new_size = (old_size[0]+50, old_size[1]+50)

                new_im = Image.new("RGB", new_size,color_vec_tx[shf_N[k]])# color='yellow')
            
            elif(rb_val==3): # for the border #cluster based 
                new_size = (old_size[0]+50, old_size[1]+50)


                new_im = Image.new("RGB", new_size,color_vec_clasgn[shf_N[k]])# color='yellow')
                

            elif(rb_val==4): # for the border #patient id  based 
                new_size = (old_size[0]+50, old_size[1]+50)


                new_im = Image.new("RGB", new_size,color_vec_patid[shf_N[k]])# color='yellow')
            #25th jan 2022 comment
            '''            
            elif(rb_val==0): 
                new_size = (old_size[0]+1, old_size[1]+1)
                new_im = Image.new("RGB", new_size,color='black')
            '''    
            

            '''
            if(rb_val==1): # for the border
                new_size = (old_size[0]+30, old_size[1]+30)

                #new_im = Image.new("RGB", new_size,color='yellow')   ## luckily, this is already black!

                if(resp_list[shf_N[k]] == 'Response 1'):
                    new_im = Image.new("RGB", new_size,color='yellow')
                elif(resp_list[shf_N[k]] == 'Response 2'):
                    new_im = Image.new("RGB", new_size,color='red')

            elif(rb_val==0): 
                new_size = (old_size[0]+1, old_size[1]+1)
                new_im = Image.new("RGB", new_size,color='black')
            '''
            
            new_im.paste(tile_1, (int((new_size[0]-old_size[0])/2),int((new_size[1]-old_size[1])/2)))      
            
            
            count_file = np.int(np.array(np.where(shf_N[k]==shf_N)).flatten()) #19th feb 2022
                                
            file_name = os.path.join(path_wd+'/output_tiles/image_tsne_tils'+str(shf_N[k])+'.png') #19th Jan 2022 (changed the indexing), 19th feb 2022

            file_name_hover.append('image_tsne_tils'+str(shf_N[k])+'.png') # 24th jan 2022 #19th Jan 2022, 19th feb 2022
            
            #plt.imsave(file_name,tile_1)
            new_im.save(file_name) #2nd Feb 2021

            #count_file = count_file +1 #19th feb 2022
            
            # Read Images 


            tile_2 = Image.open(file_name)
            rs = max(1, tile_2.width/max_dim, tile_2.height/max_dim)
            tile_2 = tile_2.resize((int(tile_2.width/rs), int(tile_2.height/rs)), Image.ANTIALIAS) #commented antialias on 9th Feb 2021


            full_image.paste(tile_2, (int((width-max_dim)*ty[shf_N[k]]), int((height-max_dim)*tx[shf_N[k]])),mask=tile_2.convert('RGBA'))


        matplotlib.pyplot.figure(figsize = (25,20))
        plt.imshow(full_image)
        plt.axis('off')
        #return (full_image)
    
        ##19th feb 2022
        ## order filenamehover list before sending it out to the live panels
        so = np.argsort(shf_N)
        file_name_hover_np = np.array(file_name_hover)
        sorted_file_name_hover = file_name_hover_np[so]
        file_name_hover = sorted_file_name_hover.tolist()
        
        ###5th March 2021
        k1 = random.randint(2,500) #19th Jan 2022 (k to k1)
        file_name = os.path.join(path_wd+'/image_tSNE_GUI/static/image_tsne_tils_all_'+str(k1)+'.png') #19th Jan 2022 (k to k1)

        full_image.save(file_name)
      

        rotated_img     = full_image.rotate(90)
        file_name_rot = file_name = os.path.join(path_wd+'/image_tSNE_GUI/static/image_tsne_tils_all_'+str(k1)+'_rot.png') #19th Jan 2022 (k to k1)
       


        rotated_img.save(file_name_rot)


                                
                                
                                
                                
                                
                                
    return([file_name_rot,tsne, file_name_hover]) #19th Jan 2022 (added file_name_hover)


###############################################################################
### button_callback()                                                      ####        
### a) Calls the create_figure() that collects user inputs from the GUI    ####
### b) draw_tSNE_scatter() generates the tSNE plots for the live canvases  ####
### b) reads in the user-provided tSNE                                     ####
### c) generates thumbnails, and pastes these onto the static canvas       ####
### d) stores the thumbnails in the output folder                          ####
### e) updates the hover tool with thumbnail paths                         ####
###############################################################################  


def button_callback():
    
    theme_t = theme_select.value
    if(theme_t == 'black'):
        curdoc().theme= theme_black
    elif(theme_t == 'gray'):
        curdoc().theme= theme_gray
    elif(theme_t == 'dark blue'):
        curdoc().theme= theme_blue
        
    jk = create_figure(stack_montage_flag)
    layout.children[1] = jk[0]
    
    print('############')
    print('In Button callback')
    tsne3 = jk[1]
    print(type(tsne3))
    print(tsne3)
    
    #19th Jan 2022
    file_name_hover = jk[2]
    print('############fnh in button callback')
    print('file_name_hover')
    print(file_name_hover)
    

    #14th Feb 2022
    markers_single = jk[3]
    print('############')
    print(type(markers_single))
    print(markers_single)

    cluster_ms_list = jk[4]
    print('############')
    print(type(cluster_ms_list ))
    print(cluster_ms_list )

    p1_out = draw_tSNE_scatter(tsne3, file_name_hover, cluster_ms_list) #19th Jan 2022 (added file_name_hover)
    p1 = p1_out[0]
    p2 = p1_out[1]
    p3 = p1_out[2]
    p4 = p1_out[3] #19th Jan 2022
    #layout.children[2] = p1
    source = p1_out[4] #19th jan 2022 (added 4)
    
    tab1 = Panel(child=p1, title="Response")
    tab2 = Panel(child=p2, title="Treatment")
    tab3 = Panel(child=p3, title="Cluster Annotations")
    tab4 = Panel(child=p4, title="Patient id") #19th Jan 2022

    tabs = Tabs(tabs=[ tab1, tab2, tab3, tab4 ]) #19th Jan 2022 (added tab4)
    layout.children[2] = tabs
    
    return([p,p1,p2,p3,p4,source,tabs]) 


############################################################################
### create_figure() collects the user choices from the GUI and          ####
### calls either the generate_stack_montage() for reading in            ####
### a single image or the generate_image_tSNE() for multiplexed images  ####
############################################################################



def create_figure(stack_montage_flag):
   
    p = figure(tools=TOOLS,x_range=x_range, y_range=y_range,width=1000,height=1000)
    
    rb_imtech = radio_button_group_imtech.value
    
    rb = radio_button_group.value
    
    rb_rs = radio_button_group_RS.value
    
    rb_shf = radio_button_group_Shf.value
    
    chk_box_marker = checkbox_group.active
    
    print(chk_box_marker)
    
    chk_box_marker_sm = checkbox_group_sm.active #26th jan 2022
    print('**chk_box_marker_sm**')  #26th jan 2022
    print(chk_box_marker_sm)  #26th jan 2022


    if(rb=='No'):
        rb_val = 0
    elif(rb=='Based on Response'):
        rb_val = 1
    elif(rb=='Based on Treatment'):
        rb_val = 2
    elif(rb=='Based on Clusters'):
        rb_val = 3
    elif(rb=='Based on Patient id'):
        rb_val = 4

         
    
    if(rb_rs=='Generate new co-ordinates'):
        rb_rs_val = 1
    elif(rb_rs=='Use pre-defined co-ordinates'):
        rb_rs_val = 0
    elif(rb_rs == 'Arrange in rows'):
        rb_rs_val = 2
        
        
    if(rb_shf=='Yes'):
        rb_shf_val = 1
    else:
        rb_shf_val = 0
        
    
    #14th feb 2022
    if (rb_imtech == 'Vectra'):
        rb_imtech_val = 0
    elif (rb_imtech=='t-CyCIF'):
        rb_imtech_val = 1
    elif (rb_imtech=='CODEX'):
        rb_imtech_val = 2
        
    ## 14th feb 2022
    ## adding in the codex, vectra, tcycif options
    
    ##added on 9th feb 2022
    ## for codex sm for tonsils
    #cluster_ms_list = []
    
    
    # 20th Jan 2022        
    # collecting the marker names for tcycif/codex stack montage
    #color_ms_patid = []
    cluster_ms_list = ['nil'] * len(LABELS_MARKERS)#[]
    clust_ms_list = []
    clust_ms_list_1 = pd.read_csv(os.path.join(path_wd + '/user_inputs/metadata/markers.csv'),
                                         header= 0,index_col=None)
    markers_single = np.array(clust_ms_list_1.iloc[:,2]).flatten()


    ## need to update the markers_single array based on the order the files are read in 
    if (stack_montage_flag==True):
        if (rb_imtech_val ==1): #SM for t-CyCIF data
            print('in SM for t-CyCIF')
            ms_list=[]
            cluster_ms_list = []
            for i in range(markers_single.shape[0]):
                print(i)
                print(pat_fov_list[i])
                print(markers_single)
                channel_num = np.int(pat_fov_list[i].split("_40X_")[1].split(".tiff")[0])
                ms_list.append(markers_single[channel_num-1])
                #channel_name = pat_fov_list[i].split('.tif')[0].split('_')[3]
                #channel_num = np.int(np.array(np.where(channel_name==markers_single)).flatten())
                #ms_list.append(markers_single[channel_num])

            markers_single = np.copy(np.array(ms_list))



            # use this updated markers_single name order going forward
            for i in range(markers_single.shape[0]):

                #color_vec_patid.append(colours_58[clust_patid_list_1[i]]) 
                #clust_ms_list.append(markers_single[i]) commented out on the 14th Feb 2022
                cluster_ms_list.append('Channel '+ markers_single[i]) 

        elif (rb_imtech_val ==2): #SM for CODEX
            ## for codex sm for tonsils
            print('in SM for CODEX')
            ## need to update the markers_single array based on the order the files are read in 
            ms_list=[]
            cluster_ms_list = []
            for i in range(markers_single.shape[0]):
                print(i)
                print(pat_fov_list[i])
                #channel_num = np.int(pat_fov_list[i].split("_40X_")[1].split(".tiff")[0])
                channel_name = pat_fov_list[i].split('.tif')[0].split('_')[3]
                channel_num = np.int(np.array(np.where(channel_name==markers_single)).flatten())
                ms_list.append(markers_single[channel_num])

            markers_single = np.copy(np.array(ms_list))
            ###

            # use this updated markers_single name order going forward
            for i in range(markers_single.shape[0]):

                #color_vec_patid.append(colours_58[clust_patid_list_1[i]]) 
                #clust_ms_list.append(markers_single[i])
                cluster_ms_list.append('Channel '+ markers_single[i])        
                
                
    elif (stack_montage_flag == False): 
        ###############
        ###############
        #1st Feb 2022
        ###############
        #uncomment for tcycif/vectra
        ###############


        ## 28th Jan 2022
        # to handle all markers in t-CyCIF/CODEX/Vectra

        mc = []
        for m in range(len(LABELS_MARKERS)):
            in_mc = np.int(np.array(np.where(LABELS_MARKERS[m] == np.array(markers_single))).flatten())
            mc.append(in_mc)
            
        if (rb_imtech_val ==0):#Vectra
            wc = [100] * len(LABELS_MARKERS)      
            wc[0] = 800
            wc[1]=wc[2] = 400
        elif (rb_imtech_val ==1):#t-CyCIF
            wc = [100] * len(LABELS_MARKERS)      
            wc[0] = 50
        elif (rb_imtech_val ==2):
            wc = [150] * len(LABELS_MARKERS)      
            wc[0] = 300 #was 50 pre codex 11th feb 2022
            wc[6] = 100
            #wc[1]=wc[2]=wc[3]=wc[4]= 750 #added for codex 11th feb 2022
            
            
        
    ###########
            

    if(len(chk_box_marker_sm)==0): #so we are using the multiple multiplexed option #26th jan 2022
        if(len(chk_box_marker)==0): #if no markers are chosen, display defaults
            #file_name_1 = os.path.join(path_wd+'/user_inputs/image_tsne_tils_all_1_rot.png')#"image_tSNE_GUI/static/image_tsne_tils_all.png"
            file_name_1 = "image_tSNE_GUI/static/image_tsne_tils_all.png"
            p.image_url(url=[file_name_1], x=x_range[0],y=y_range[1],w=x_range[1]-x_range[0],h=y_range[1]-y_range[0])
            df_Xtsne = pd.read_csv(os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE.csv'), index_col=None, header= None)
            df_Xtsne.shape
            tsne_points = np.array(df_Xtsne )
            file_name_hover = list(range(num_images)) #19th Jan 2022

        else:


            out1 = generate_image_tSNE(chk_box_marker, rb_val,rb_rs_val,rb_shf_val,rb_imtech_val, mc, wc, LABELS_MARKERS) #14th feb 2022 (for tech choice)
            file_name_all = out1[0]
            tsne_points = out1[1]
            file_name_hover = out1[2] #19th jan 2022

            print('file_name_hover after gen_image_tsne')
            print(file_name_hover)

            print('#########file_name_all########') 
            print('#################')  
            print('#################') 
            print('#################') 
            print(file_name_all)

            file_name_1 = file_name_all.split('/code')[1]
            print('#########file_name_1########')  
            print(file_name_1)


            p.image_url(url=[file_name_1], x=x_range[0],y=y_range[1],w=x_range[1]-x_range[0],h=y_range[1]-y_range[0])

    elif(len(chk_box_marker_sm)==1): #26th jan 2022 #stack montage option 
        print('chosen stack montage')
        out1sm = generate_stack_montage(chk_box_marker, rb_imtech_val, LABELS_MARKERS)
        file_name_all = out1sm[0]
        tsne_points = out1sm[1]
        file_name_hover = out1sm[2] #19th jan 2022

        print('############fnh post sm')
        print('file_name_hover')
        print(file_name_hover)

        print('#########file_name_all########') 
        print('#################')  
        print('#################') 
        print('#################') 
        print(file_name_all)

        file_name_1 = file_name_all.split('/code')[1]
        print('#########file_name_1########')  
        print(file_name_1)


        p.image_url(url=[file_name_1], x=x_range[0],y=y_range[1],w=x_range[1]-x_range[0],h=y_range[1]-y_range[0])

            
    return ([p,tsne_points, file_name_hover,markers_single, cluster_ms_list]) #19th jan 2022 (added file_name_hover)


##########
# define the colour vectors
colours_58 = ["firebrick","gold","royalblue","green","dimgray","orchid","darkviolet",
              "red", "orange", "limegreen", "blue", "purple", "seagreen","gold","darkolivegreen",
              "lightpink","thistle","mistyrose","saddlebrown","slategrey","powderblue",
            "palevioletred","mediumvioletred","yellowgreen","lemonchiffon","chocolate",
              "lightsalmon","lightcyan","lightblue", "darkorange","black","darkblue","darkgreen","paleturquoise","yellow","rosybrown",
             "steelblue","dodgerblue","darkkhaki","lime","coral","aquamarine","mediumpurple","violet","plum",
             "deeppink","navy","seagreen","teal","mediumspringgreen","cadetblue",
             "maroon","silver","sienna","crimson","slateblue","magenta","darkmagenta"]

colours_resp = ["yellow","red","green"]
colours_tx = ["orange","limegreen","violet"]

##########

#####################################
#### Section that gets populated ####
####based on User uploads ###########
#####################################
#####################################
## This section reads in images, ####
## metadata, markers in the data,####
## and user choices              ####
#####################################
#####################################


path_wd = os.getcwd()
print('Current working directory: ')
print(path_wd)

'''7th Feb 2022
# read in tSNE co-ordinates 
df_Xtsne = pd.read_csv(os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE.csv'), index_col=None, header= None)
tsne = np.array(df_Xtsne )
tx, ty = tsne[:,0], tsne[:,1]
tx = (tx-np.min(tx)) / (np.max(tx) - np.min(tx))
ty = (ty-np.min(ty)) / (np.max(ty) - np.min(ty))
num_images = tsne.shape[0]
'''

### 7th Feb 2022
### to generate tsne points from the onset itself

fname = os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE.csv')
if os.path.isfile(fname):
    df_Xtsne = pd.read_csv(fname, index_col=None, header= None)
    tsne = np.array(df_Xtsne )
    tx, ty = tsne[:,0], tsne[:,1]
    tx = (tx-np.min(tx)) / (np.max(tx) - np.min(tx))
    ty = (ty-np.min(ty)) / (np.max(ty) - np.min(ty))
    num_images = tsne.shape[0]
    
    ## 14th march 2022
    ## to have the arrange_in_rows and random points already available
    
    # Choose up to k points around each reference point as candidates for a new
    # sample point
    k = 10

    # Minimum distance between samples
    r = 1.7

    width_1, height_1 = 20, 22

    print('Generating random co-ordinates')

    # Cell side length
    a = r/np.sqrt(2)
    # Number of cells in the x- and y-directions of the grid
    nx, ny = int(width_1 / a) + 1, int(height_1 / a) + 1

    # A list of coordinates in the grid of cells
    coords_list = [(ix, iy) for ix in range(nx) for iy in range(ny)]
    # Initilalize the dictionary of cells: each key is a cell's coordinates, the
    # corresponding value is the index of that cell's point's coordinates in the
    # samples list (or None if the cell is empty).
    cells = {coords: None for coords in coords_list}



    # Pick a random point to start with.
    pt = (np.random.uniform(0, width_1), np.random.uniform(0, height_1))
    samples = [pt]
    # Our first sample is indexed at 0 in the samples list...
    cells[get_cell_coords(pt,a)] = 0
    # ... and it is active, in the sense that we're going to look for more points
    # in its neighbourhood.
    active = [0]

    nsamples = 1
    # As long as there are points in the active list, keep trying to find samples.
    while (nsamples < num_images): #active:
        # choose a random "reference" point from the active list.
        idx = np.random.choice(active)
        refpt = samples[idx]
        # Try to pick a new point relative to the reference point.
        pt = get_point(k, refpt,r,a,nx,ny,cells,samples)
        if pt:
            # Point pt is valid: add it to the samples list and mark it as active
            samples.append(pt)
            nsamples += 1
            active.append(len(samples)-1)
            cells[get_cell_coords(pt,a)] = len(samples) - 1
            print('nsamples is: ',str(nsamples))
        else:
            # We had to give up looking for valid points near refpt, so remove it
            # from the list of "active" points.
            active.remove(idx)

    tsne = np.asarray(samples)
    tx, ty = tsne[:,0], tsne[:,1]
    tx = (tx-np.min(tx)) / (np.max(tx) - np.min(tx))
    ty = (ty-np.min(ty)) / (np.max(ty) - np.min(ty))  

    df_Xtsne_m = pd.DataFrame(tsne)
    #df_Xtsne_m.to_csv(os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE.csv'), header=None, index=None)
    df_Xtsne_m.to_csv(os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE_user.csv'), header=None, index=None) #14th march 2022
   
    
    ###### 14th March 2022
    ##### for 'arrange in rows' option at the onset itself


    # Minimum distance between samples
    r = 2

    width_1, height_1 = 20, 22

    print('Arrange images side-by-side')

    # Cell side length
    a = r/np.sqrt(2)
    # Number of cells in the x- and y-directions of the grid
    nx, ny = int(width_1 / a) + 1, int(height_1 / a) + 1

    # A list of coordinates in the grid of cells
    coords_list = [(ix, iy) for ix in range(nx) for iy in range(ny)]


    #logic to get grid points - 29th March 2021
    m = np.int(np.floor(nx*ny/num_images))


    row_needed = []
    def multiples(m, num_images):
        for i in range(num_images):
            row_needed.append(i*m)

    multiples(m,num_images)


    select_coords = np.array(coords_list)[np.array(row_needed).flatten()]

    print(type(select_coords))
    
    tsne1 = select_coords
    df_Xtsne = pd.DataFrame(tsne1)
    df_Xtsne.to_csv(os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE_seeall.csv'), header=None, index=None)
    
else: 
    #read in images
    FoV_path = os.path.join(path_wd + '/user_inputs/figures/')
    count_images = 0
    for fname in os.listdir(FoV_path):
        print(fname)
        count_images = count_images + 1
    num_images = count_images
    #generate random 2D coords for these images

    
    # Choose up to k points around each reference point as candidates for a new
    # sample point
    k = 10

    # Minimum distance between samples
    r = 1.7

    width_1, height_1 = 20, 22

    print('Generating random co-ordinates')

    # Cell side length
    a = r/np.sqrt(2)
    # Number of cells in the x- and y-directions of the grid
    nx, ny = int(width_1 / a) + 1, int(height_1 / a) + 1

    # A list of coordinates in the grid of cells
    coords_list = [(ix, iy) for ix in range(nx) for iy in range(ny)]
    # Initilalize the dictionary of cells: each key is a cell's coordinates, the
    # corresponding value is the index of that cell's point's coordinates in the
    # samples list (or None if the cell is empty).
    cells = {coords: None for coords in coords_list}



    # Pick a random point to start with.
    pt = (np.random.uniform(0, width_1), np.random.uniform(0, height_1))
    samples = [pt]
    # Our first sample is indexed at 0 in the samples list...
    cells[get_cell_coords(pt,a)] = 0
    # ... and it is active, in the sense that we're going to look for more points
    # in its neighbourhood.
    active = [0]

    nsamples = 1
    # As long as there are points in the active list, keep trying to find samples.
    while (nsamples < num_images): #active:
        # choose a random "reference" point from the active list.
        idx = np.random.choice(active)
        refpt = samples[idx]
        # Try to pick a new point relative to the reference point.
        pt = get_point(k, refpt,r,a,nx,ny,cells,samples)
        if pt:
            # Point pt is valid: add it to the samples list and mark it as active
            samples.append(pt)
            nsamples += 1
            active.append(len(samples)-1)
            cells[get_cell_coords(pt,a)] = len(samples) - 1
            print('nsamples is: ',str(nsamples))
        else:
            # We had to give up looking for valid points near refpt, so remove it
            # from the list of "active" points.
            active.remove(idx)

    tsne = np.asarray(samples)
    tx, ty = tsne[:,0], tsne[:,1]
    tx = (tx-np.min(tx)) / (np.max(tx) - np.min(tx))
    ty = (ty-np.min(ty)) / (np.max(ty) - np.min(ty))  

    df_Xtsne_m = pd.DataFrame(tsne)
    df_Xtsne_m.to_csv(os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE.csv'), header=None, index=None)
    df_Xtsne_m.to_csv(os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE_user.csv'), header=None, index=None) #14th march 2022
   
    
    ###### 14th March 2022
    ##### for 'arrange in rows' option at the onset itself


    # Minimum distance between samples
    r = 2

    width_1, height_1 = 20, 22

    print('Arrange images side-by-side')

    # Cell side length
    a = r/np.sqrt(2)
    # Number of cells in the x- and y-directions of the grid
    nx, ny = int(width_1 / a) + 1, int(height_1 / a) + 1

    # A list of coordinates in the grid of cells
    coords_list = [(ix, iy) for ix in range(nx) for iy in range(ny)]


    #logic to get grid points - 29th March 2021
    m = np.int(np.floor(nx*ny/num_images))


    row_needed = []
    def multiples(m, num_images):
        for i in range(num_images):
            row_needed.append(i*m)

    multiples(m,num_images)


    select_coords = np.array(coords_list)[np.array(row_needed).flatten()]

    print(type(select_coords))
    
    tsne1 = select_coords
    df_Xtsne = pd.DataFrame(tsne1)
    df_Xtsne.to_csv(os.path.join(path_wd + '/user_inputs/metadata/X_imagetSNE_seeall.csv'), header=None, index=None)
    
    
    ########################

# read in the markers
'''7th Feb 2022
df_markers = pd.read_csv(os.path.join(path_wd + '/user_inputs/metadata/Marker_ids.csv'), index_col=None, header= None)
markers_list = np.array(df_markers ).flatten()
LABELS_MARKERS = []
for j in range(markers_list.shape[0]):
    LABELS_MARKERS.append(markers_list[j]) 
'''

# 7TH FEB 2022

# adding this for reading in data if no marker info is present
fname = os.path.join(path_wd + '/user_inputs/metadata/Marker_ids.csv')

if os.path.isfile(fname):
    df_markers = pd.read_csv(fname, index_col=None, header= None)
    markers_list = np.array(df_markers ).flatten()
    LABELS_MARKERS = []
    for j in range(markers_list.shape[0]):
        LABELS_MARKERS.append(markers_list[j]) 
    stack_montage_flag = False

    
else:
    LABELS_MARKERS = ['nil'] * 6
    stack_montage_flag = True

## read in images
marker_image_list = []
pat_fov_list = []
FoV_path = os.path.join(path_wd + '/user_inputs/figures/')
file_order = [] #8th Feb 2022

#sorted input data add on 17th Feb 2022
for fname in sorted(os.listdir(FoV_path)):
    print(fname)
    marker_image_list.append(FoV_path+fname)
    pat_fov_list.append(fname)
    #file_order.append(np.int(fname.split('_')[1].split('.tif')[0])) #8th Feb 2022

    
## delete after trial
'''
marker_image_list.append(FoV_path+'FoV_0.tif')
marker_image_list.append(FoV_path+'FoV_1.tif')
marker_image_list.append(FoV_path+'FoV_2.tif')
marker_image_list.append(FoV_path+'FoV_3.tif')
marker_image_list.append(FoV_path+'FoV_4.tif')
marker_image_list.append(FoV_path+'FoV_5.tif')
marker_image_list.append(FoV_path+'FoV_6.tif')
marker_image_list.append(FoV_path+'FoV_7.tif')
marker_image_list.append(FoV_path+'FoV_8.tif')
marker_image_list.append(FoV_path+'FoV_9.tif')


pat_fov_list.append('FoV_0.tif')
pat_fov_list.append('FoV_1.tif')
pat_fov_list.append('FoV_2.tif')
pat_fov_list.append('FoV_3.tif')
pat_fov_list.append('FoV_4.tif')
pat_fov_list.append('FoV_5.tif')
pat_fov_list.append('FoV_6.tif')
pat_fov_list.append('FoV_7.tif')
pat_fov_list.append('FoV_8.tif')
pat_fov_list.append('FoV_9.tif')
'''
print("print image list")
print(marker_image_list)
print("file order")
print(file_order)




#for i in range(num_images):
#  file_ord.append(np.int(np.array(np.where(fs2_list[i]==np.array(ff_list))).flatten()))


#################################
#################################
# checks for user metadata inputs
# if these files are not present, gray out the tSNE or points. 

# collecting the response metadata
# 24th jan 2022

color_vec = []
resp_list= []
fname = os.path.join(path_wd + '/user_inputs/metadata/Response_categories.csv')

if os.path.isfile(fname):
    resp_list_1 = np.array(pd.read_csv(fname,header= None,index_col=None)).flatten()
    uni_resp,counts_resp = np.unique(resp_list_1,return_counts=True)

    for i in range(resp_list_1.shape[0]):
        row_t = np.int(np.array(np.where(resp_list_1[i]==uni_resp)).flatten())
        #if resp_list_1[i]=='Response 1':
        color_vec.append(colours_resp[row_t])
        #elif resp_list_1[i]=='Response 2':
        #    color_vec.append('red')
        resp_list.append(resp_list_1[i])
else:
    for i in range(num_images):
        color_vec.append('gray')
        resp_list.append('Response nil')
        
        
# collecting the treatment metadata
# 24th jan 2022
color_vec_tx = []
tx_list = []
fname = os.path.join(path_wd + '/user_inputs/metadata/Treatment_categories.csv')

if os.path.isfile(fname):
    tx_list_1= np.array(pd.read_csv(fname,header= None,index_col=None)).flatten()
    uni_tx,counts_tx = np.unique(tx_list_1,return_counts=True)
    for i in range(tx_list_1.shape[0]):
        row_t = np.int(np.array(np.where(tx_list_1[i]==uni_tx)).flatten())
        #if resp_list_1[i]=='Response 1':
        color_vec_tx.append(colours_tx[row_t])
        #if tx_list_1[i]=='Treatment 1':
        #    color_vec_tx.append('orange')
        #elif tx_list_1[i]=='Treatment 2':
        #    color_vec_tx.append('limegreen')
        tx_list.append(tx_list_1[i])
else:
    for i in range(num_images):
        color_vec_tx.append('gray')
        tx_list.append('Treatment nil')


# collecting the cluster assignments metadata
# 24th jan 2022
fname = os.path.join(path_wd + '/user_inputs/metadata/Cluster_categories.csv')
color_vec_clasgn = []
cluster_anno_list = []
clust_asgn_list = []


if os.path.isfile(fname):
    clust_asgn_list_1 = np.array(pd.read_csv(fname, header= None,index_col=None)).flatten()
    for i in range(clust_asgn_list_1.shape[0]):
   
        color_vec_clasgn.append(colours_58[clust_asgn_list_1[i]])
        clust_asgn_list.append(clust_asgn_list_1[i])
        cluster_anno_list.append('Cluster '+ str(clust_asgn_list_1[i]))  

else:
    for i in range(num_images):
        color_vec_clasgn.append('gray') 
        clust_asgn_list.append('nil')
        cluster_anno_list.append('Cluster nil')
  
     

# collecting the patient id metadata    
# 24th jan 2022
fname = os.path.join(path_wd + '/user_inputs/metadata/Patient_ids.csv')
color_vec_patid = []
cluster_pat_list = []
clust_patid_list = []

if os.path.isfile(fname):
    
    # 19th Jan 2022        
    # collecting the Patient id metadata

    clust_patid_list_1 = np.array(pd.read_csv(fname,header= None,index_col=None)).flatten()
    pat_ind_list = np.copy(clust_patid_list_1)

    for i in range(clust_patid_list_1.shape[0]):

        color_vec_patid.append(colours_58[clust_patid_list_1[i]]) 
        clust_patid_list.append(clust_patid_list_1[i])
        cluster_pat_list.append('Patient '+ str(clust_patid_list_1[i]))
        
else:
    pat_ind_list = []
    for i in range(num_images):
        color_vec_patid.append('gray') 
        clust_patid_list.append('nil')
        cluster_pat_list.append('Patient nil')
        pat_ind_list.append('nil')
        

# 19th Jan 2022        
# generate dummy thumbnail names for hover panel

file_name_hover = []
file_name_hover_list = []

for i in range(num_images): #clust_patid_list_1.shape[0]):
  
    file_name_hover.append(str(i))
    file_name_hover_list.append('Thumbnail '+ str(i))  

 
'''
14th feb 2022
# 20th Jan 2022        
# collecting the marker names for tcycif single
#color_ms_patid = []
cluster_ms_list = ['nil'] * len(LABELS_MARKERS)#[]
clust_ms_list = []
clust_ms_list_1 = pd.read_csv(os.path.join(path_wd + '/user_inputs/metadata/markers.csv'),
                                         header= 0,index_col=None)
markers_single = np.array(clust_ms_list_1.iloc[:,2]).flatten()
'''

####this was our option stub for sm= f ot t...
    


#################
# set up widgets
#################

RB_1 = ['Based on Response', 'Based on Treatment','Based on Clusters','Based on Patient id','No'] #25th Jan 2022

RB_2 = ['Generate new co-ordinates', 'Use pre-defined co-ordinates', 'Arrange in rows']

RB_3 = ['Yes', 'No']

RB_4 = ['Vectra', 't-CyCIF', 'CODEX'] #14th feb 2022

TS_1 = ['black','gray', 'dark blue']

TOOLS="hover,pan,crosshair,wheel_zoom,zoom_in,zoom_out,box_zoom,undo,redo,reset,save,box_select,"

x_range=(0,1)
y_range=(0,1)


#main image tSNE canvas
p = figure(tools=TOOLS,x_range=x_range, y_range=y_range,width=1000,height=1000)
tsne_points = np.zeros([1,2])

#additional tSNE scatter plot canvas



point_tSNE = figure(plot_width=350, plot_height=350,
              tools='hover,pan,wheel_zoom,box_select,reset')
point_tSNE.title.text = 'tSNE point cloud for Patient response'


point_tSNE.scatter(tsne[:,0],tsne[:,1],fill_alpha=0.6, color ='red',size=8,legend='Response')

point_tSNE.legend.location = "bottom_left"

theme_black = Theme(json={
    'attrs': {
        'Figure': {
            'background_fill_color': '#2F2F2F',
            'border_fill_color': '#2F2F2F',
            'outline_line_color': '#444444'
            },
        'Axis': {
            'axis_line_color': "white",
            'axis_label_text_color': "white",
            'major_label_text_color': "white",
            'major_tick_line_color': "white",
            'minor_tick_line_color': "white",
            'minor_tick_line_color': "white"
            },
        'Grid': {
            'grid_line_dash': [6, 4],
            'grid_line_alpha': .3
            },
        'Circle': {
            'fill_color': 'lightblue',
            'size': 10,
            },
        'Title': {
            'text_color': "white"
            }
        }
    })

theme_gray = Theme(json={
    'attrs': {
        'Figure': {
            'background_fill_color': '#555555',
            'border_fill_color': '#2F2F2F',
            'outline_line_color': '#444444'
            },
        'Axis': {
            'axis_line_color': "white",
            'axis_label_text_color': "white",
            'major_label_text_color': "white",
            'major_tick_line_color': "white",
            'minor_tick_line_color': "white",
            'minor_tick_line_color': "white"
            },
        'Grid': {
            'grid_line_dash': [6, 4],
            'grid_line_alpha': .3
            },
        'Circle': {
            'fill_color': 'lightblue',
            'size': 10,
            },
        'Title': {
            'text_color': "white"
            }
        }
    })

theme_blue = Theme(json={
    'attrs': {
        'Figure': {
            'background_fill_color': '#25256d',
            'border_fill_color': '#2F2F2F',
            'outline_line_color': '#444444'
            },
        'Axis': {
            'axis_line_color': "white",
            'axis_label_text_color': "white",
            'major_label_text_color': "white",
            'major_tick_line_color': "white",
            'minor_tick_line_color': "white",
            'minor_tick_line_color': "white"
            },
        'Grid': {
            'grid_line_dash': [6, 4],
            'grid_line_alpha': .3
            },
        'Circle': {
            'fill_color': 'lightblue',
            'size': 10,
            },
        'Title': {
            'text_color': "white"
            }
        }
    })

#########
#########


## 8th March 2021
TOOLS="hover,pan,crosshair,wheel_zoom,zoom_in,zoom_out,box_zoom,undo,redo,reset,tap,save,box_select,poly_select,lasso_select,"


TOOLTIPS = [
        ("index", "$index"),
        ("(x,y)", "($x, $y)"),
        ("Pat_id", "@pat_list"),
        ("Response", "@res_list"),
        ("Treatment", "@tx_list"), #19th Jan 2022
        ("Cluster id", "@clust_asgn_list"), #19th Jan 2022
        ("Channel", "@cluster_ms_list"), #20th jan 2022
        ("Thumbnail", "@file_name_hover_list"), #19th Jan 2022
        ("FoV","@fov_list")
    ]
    
p1 = figure(plot_width=400, plot_height=400, tooltips=TOOLTIPS,tools = TOOLS,
               title="Patient response")




#####################################################################################
## This block prepares and sets up the GUI layout, and collects user-input choices ##
#####################################################################################


desc = Div(text=open(os.path.join(path_wd + '/image_tSNE_GUI/desc.html')).read(), sizing_mode="stretch_width")

##desc_im_tech = Div(text=open(os.path.join(path_wd + '/image_tSNE_GUI/descimtech.html')).read(), sizing_mode="stretch_width") #14th feb 2022

desc_SM1 = Div(text=open(os.path.join(path_wd + '/image_tSNE_GUI/descSM1.html')).read(), sizing_mode="stretch_width") #26th jan 2022

desc_SM = Div(text=open(os.path.join(path_wd + '/image_tSNE_GUI/descMontage.html')).read(), sizing_mode="stretch_width") #26th jan 2022
              
##desc_MM = Div(text=open(os.path.join(path_wd + '/image_tSNE_GUI/descMarker.html')).read(), sizing_mode="stretch_width") #3rd Feb 2022

##14th Feb 2022
radio_button_group_imtech = Select(value='Vectra',
                          title='',
                          width=200,
                          options=RB_4)


radio_button_group = Select(value='No',
                          title='Image border',
                          width=200,
                          options=RB_1)

radio_button_group_RS = Select(value='Generate new co-ordinates',
                          title='tSNE co-ordinates',
                          width=220,
                          options=RB_2)

radio_button_group_Shf = Select(value='Yes',
                          title='Shuffle images',
                          width=200,
                          options=RB_3)

theme_select = Select(value = 'black',
                      title='Theme', 
                      width = 200, 
                      options = TS_1)


checkbox_group = CheckboxGroup(labels=LABELS_MARKERS)#, active=[0, 1])


button = Button(label='Run', width=100, button_type="success")

## added to activate Run button
button.on_click(button_callback)

##26th jan 2022
## for stack montage
SM = ['Stack montage']
checkbox_group_sm = CheckboxGroup(labels=SM)


print('updating new p1#')



# set up layout and GUI refresh after every 'Run' click

out2 = create_figure(stack_montage_flag)
print(out2)
p = out2[0]
tsne2 = out2[1]
print('############')
print(type(tsne2))
print(tsne2)

#19th Jan 2022
file_name_hover = out2[2]
print('############fnh after create figure')
print(type(file_name_hover))
print(file_name_hover)

#14th Feb 2022
markers_single = out2[3]
print('############')
print(type(markers_single))
print(markers_single)

cluster_ms_list = out2[4]
print('############')
print(type(cluster_ms_list ))
print(cluster_ms_list )


p11_out = draw_tSNE_scatter(tsne2, file_name_hover,cluster_ms_list ) #19th Jan 2022 (added file_name_hover)
p1 = p11_out[0]
p2 = p11_out[1]
p3 = p11_out[2]
p4 = p11_out[3] #19th Jan 2022

tab1 = Panel(child=p1, title="Response")
tab2 = Panel(child=p2, title="Treatment")
tab3 = Panel(child=p3, title="Cluster Annotations")
tab4 = Panel(child=p4, title="Patient id") #19th Jan 2022

tabs = Tabs(tabs=[ tab1, tab2, tab3, tab4 ]) #19th Jan 2022 (added tab4)

#layout1 = row(checkbox_group_sm, desc_SM) #26th jan 2022

selects = column(desc,  radio_button_group_imtech, desc_SM1, checkbox_group_sm,  desc_SM,  checkbox_group,  radio_button_group, radio_button_group_RS, radio_button_group_Shf,  theme_select, button, width=520) # was 420 #26th jan 2022, #3rd Feb 2022 (added the MM), 14th feb 2022 for im tech

layout=row(selects,p, tabs)#,selected_points)#create_figure())

#doc = curdoc()
curdoc().theme= theme_black


# add to document
curdoc().add_root(layout)

curdoc().title = "Mistic: Image tSNE viewer"



# cd image_tSNE_code/bokeh_GUI/bokeh-branch-2.3/examples/app
# bokeh serve --port 5098 --show image_tSNE_GUI

