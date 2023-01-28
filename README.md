# Mistic_code_live_cell_imaging: image tSNE visualizer

This is a Python tool using the Bokeh library to view multiple multiplex images simultaneously. The code has been tested on 7-panel Vectra TIFF, 32- & 64-panel CODEX TIFF, 16-panel CODEX QPTIFF, 4-panel CyCIF TIFF, and 44-panel t-CyCIF TIFF images.

Mistic is published at [Patterns (2022)](https://www.cell.com/patterns/fulltext/S2666-3899(22)00120-9).

Mistic's GUI with user inputs is shown below:

<img src=/fig_readme/Figure_2.jpg width="80%"></img>

Figure description: A sample Mistic GUI with user inputs is shown. **A.** User-input panel where imaging technique choice, stack montage option or markers can be selected, images borders can be added, new or pre-defined image display coordinates can be chosen, and a theme for the canvases can be selected. **B.** Static canvas showing the image t-SNE colored and arranged as per user inputs. **C.** Live canvas showing the corresponding t-SNE scatter plot where each image is represented as a dot. The live canvas has tabs for displaying additional information per image. Metadata for each image can be obtained by hovering over each dot.


## Features of Mistic
* Two canvases: 
  *   still canvas with the image tSNE rendering 
  *   live canvases with tSNE scatter plots for image metadata rendering
* Dropdown option to select the imaging technique: Vectra, CyCIF, t-CyCIF, or CODEX
* Option to choose between Stack montage view or multiple multiplexed images by selecting the markers to be visualised at once
* Option to place a border around each image based on image metadata
* Option to use a pre-defined tSNE or generate a new set of tSNE co-ordinates
* Option to shuffle images with the tSNE co-ordinates
* Option to render multiple tSNE scatter plots based on image metadata
* Hover functionality available on the tSNE scatter plot to get more information of each image
* Save, zoom, etc each of the Bokeh canvases

## Requirements

* Python >= 3.6 
  * Install Python from here: https://www.python.org/downloads/
<!---* bokeh 0.12.16 -->
  <!---* For installation, open terminal and type: ``` pip install bokeh ```-->
  <!---* To verify a successful installation, type: ``` bokeh info ```-->
  <!---* Further information: https://docs.bokeh.org/en/latest/docs/first_steps/installation.html -->
* Open a command prompt (or the Terminal application):
  * Download ``` pip ```. Type: 
    * ``` curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py ```
    * ``` python3 get-pip.py ``` and wait for the installation to complete
    * Verify the ``` pip ``` installation by typing ``` pip --version ```
  * ```pip install mistic ```

## Setting up Mistic

* Download this code repository or Open Terminal and use `git clone`

  `$ git clone https://github.com/MathOnco/Mistic_for_live_cell_imaging.git`
 
* In the Mistic folder, navigate to /user_inputs folder to upload input files to /figures and /metadata subfolders:
  * ```Mistic_code/code/user_inputs```
  * Use the /figures subfolder to upload the live cell .png images
    * Images for ```FoFX001003_221018_brightfield``` and ```FoFX002005_221018_brightfield``` can be found in the 'live-cell-imaging-data' folder
  * Use the /metadata subfolder to upload metadata for these images:
    * For this, navigate to the ```Mistic_code_live_cell_imaging/code/user_inputs/live-cell-imaging-data/```, choose the data of choice, move the two metadata files (Cluster_categories.csv and X_imagetSNE.csv) to ```Mistic_code/code/user_inputs/metadata/```
    * Retain the Markers_ids.csv and markers.csv, as is



## Run Mistic
  
* Open a command prompt (or the Terminal application), change to the directory containing /code and type:
  * ```bash mistic.sh```
  * This runs a bokeh server locally and will automatically open the interactive dashboard in your browser at http://localhost:5098/image_tSNE_GUI
  * On the interactive dashboard: choose the options as shown below and click ```Run```.
  * <img src=/fig_readme/live_cell_options.png width="40%"></img>




* If you get an error: ```Cannot start Bokeh server, port 5098 is already in use```, then at the Terminal, issue: 
  * ```ps -ef | grep 5098```
  * You should see a line similar to the one below on the Terminal:
   ```55525 12519 11678   0  1:22AM ttys004    0:57.81 /opt/anaconda3/bin/python /opt/anaconda3/bin/bokeh serve --port 5098 --show image_tSNE_GUI``` 
   where the 2nd term is the _process id_. Here this is '12519'.
  * Use this _process id_ to kill the process: ```kill -9 12519```


## Additional information

* Paper on bioRxiv: https://www.biorxiv.org/content/10.1101/2021.10.08.463728v1
* Documentation: https://mistic-rtd.readthedocs.io
* Code has been published at Zenodo: https://doi.org/10.5281/zenodo.5912169
* Example NSCLC Vectra images are published here: https://doi.org/10.5281/zenodo.6131933
* Mistic is highlighted on Bokeh's user showcase: http://bokeh.org/


