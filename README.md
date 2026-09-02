## Overview ##
Updated PLQY analysis code to extract PLQY, OD, and FWHM values from data collected in C31. Data files and metadata (integration times) are inputted via a gui.

## Inputs ##
The input file must be in the format .txt. <BR>
The file must contain WAVELENGTH and INTENSITY columns. Any other columns are ignored. <BR>
The <CODE>utils</CODE> module contains a function <CODE>find_data_start_row</CODE> that will determine the start row of the numerical data, allowing headers of variable length to be parsed. <BR>

## Pre-requisites ##
You will need <CODE>python >= 3.11</CODE> and <CODE>uv</CODE> which can be installed at: https://docs.astral.sh/uv/getting-started/installation/

## Usage ##
To run the analysis code:
<LI>First clone the repository by typing the following into your terminal: <CODE>git clone https://github.com/RamadanLab/PLQY-analysis-updated.git</CODE></LI>
<LI>To install the dependencies in a virtual environment, <CODE>venv</CODE>, run: <CODE>uv sync</CODE></LI>
<LI>Finally, to run the analysis, run: <CODE>uv run main.py</CODE>. A gui will pop up to input data files. Note that the default path to the calibration file assumes that the file is in the same folder as the code (as it will be when you clone the repo). If you wish to use a different path, or if you move the calibration file, you will need to select the file using the 'browse' widget.</LI>

## Future work ##
<LI>This needs testing against the legacy code to ensure outputs are reliable and repeatable before release</LI>
<LI><CODE>stray_light_correction</CODE> needs to be verified, the outputs seem much lower in the PL range after correction. </LI>
<LI>Docstrings need updating</LI>
<LI>Laser correction factor and hot pixel handling need to be verified and implimented/removed as needed.</LI>
<LI>Add functionality to analyses multiple files from one folder.</LI>
<LI>Add feature to enable alternative file naming for <CODE>_out</CODE> measurements, for instances where multiple spot <CODE>_in</CODE> measurements use the same <CODE>_out</CODE> measurement.</LI>
