## Overview ##
Updated PLQY analysis code to extract PLQY, OD, and FWHM values from data collected from the PLQY setup in C31. Data files and metadata (integration times) are inputted via a gui. Following De Mello method [1].

## Inputs ##
The input file must be in the format .txt. <BR>
The file must contain WAVELENGTH and INTENSITY columns. Any other columns are ignored. <BR>
The <CODE>utils</CODE> module contains a function <CODE>find_data_start_row</CODE> that will determine the start row of the numerical data, allowing headers of variable length to be parsed. <BR>
If you have taken multiple spot measurements and want to use the same <CODE>_out</CODE> and <CODE>_long_out</CODE> measurements, the <CODE>_in</CODE> measurements should be saved in the form <CODE>sample_spot1_in</CODE> etc.

## Pre-requisites ##
You will need <CODE>python >= 3.11</CODE> and <CODE>uv</CODE> which can be installed at: https://docs.astral.sh/uv/getting-started/installation/

## Usage ##

<LI>First clone the repository by typing the following into your terminal: 

  ```
   git clone https://github.com/RamadanLab/PLQY-analysis-updated.git
 ```
  </LI>
<LI>To install the dependencies in a virtual environment, <CODE>venv</CODE>, run:
  
  ```
  uv sync
```
</LI>

### To analyse a single sample:

Run the following:
  
  ```
  uv run main.py
  ```
  A gui will pop up to input data files. Note that the default path to the calibration file assumes that the file is in the same folder as the code (as it will be when you clone the repo). If you wish to use a different path, or if you move the calibration file, you will need to select the file using the 'browse' widget.

  ### To analyse every sample withing a folder:
  There is an option to analyse multiple files together in one go. This has most of the same arguments as before, but no gui is used. Note that currently to do this you can only set the arguments once, so all the samples will have the same integration times etc. All of the default argument values are the same, except for <CODE>common</CODE> and <CODE>stray_light</CODE>, which default to <CODE>TRUE</CODE>. Instead of having file paths as an argument, you will pass a <CODE>--directory</CODE> argument, which is the path to the folder containing all of your files. Any <CODE>short_in</CODE> files will be found and analysed. The PLQY values will be saved in a <CODE>batch_plqy_results.csv</CODE> file.

  To run the code use (inputting your own arguments as required):
  
  ```
  uv run batch.py --directory path\to\your\folder --short_time 100 --long_time 5000
  ```

Change any of the arguments in a similar way, e.g: <CODE>--pl_range 500 650</CODE>. Note that if there is a space in you folder path (e.g. <CODE>G:\My Drive\ </CODE> you will need to enclose the path in quote marks. 

### Input Arguments: ###
<LI><B>short_path:</B> Path to your <CODE>short_in</CODE> sample measurement. Use the file chooser widget to select.</LI>
<LI><B>short_time:</B> The short integration time of your measurement in ms. [Defaults to 100 ms] </LI>
<LI><B>long_path:</B> Path to your <CODE>long_in</CODE> sample measurement. Use the file chooser widget to select.</LI>
<LI><B>long_time:</B> The long integration time of your measurement in ms. [Defaults to 5000 ms] </LI>
<LI><B>common:</B> Select this if you background and empty files are saved as <CODE>bckg</CODE>, <CODE>long_bckg</CODE>, <CODE>empty</CODE>, and <CODE>long_empty</CODE>. If this is not selected, the files should be named with the same name as the <CODE>_in</CODE> measurements, replacing <CODE>_in</CODE> with <CODE>_bckg</CODE> etc. [Defaults to <CODE>FALSE</CODE>] </LI>
<LI><B>stray_light:</B> When this is ticked a stray light correction is applied across <CODE>pl_range</CODE>, removing the effects of stray light in the integrating sphere. This is recommended to be on for all analysis. [Defaults to <CODE>FALSE</CODE>] </LI>
<LI><B>pl_range:</B> This is the expected range that your PL peak resides in, used for the peak fitting and axis limits for the plot. [Defaults to 560 - 850 nm] </LI>

### Experimental Configuration Arguments: ###
These should only be changed if the experimental setup is changed.
<LI><B>laser_range:</B> The nm range of the laser peak. For the 405 nm laser this should be 395 - 415 nm.</LI>
<LI><B>cal_path:</B> Path to the the calibration file. If you clone the repo from GitHub, the default path should be correct.</LI>
<LI><B>dark_indices:</B> This refers to the indices of 'dark pixels' in the spectrometer.</LI>
<LI><B>trim_indices:</B> These are the indices of noisy edge pixel, and are specific to the spectrometer.</LI>
<LI><B>correction_factor:</B> As of 16-09-2026 this factor is not used in the code. Previously this was used to correct the laser power estimation from the <CODE>empty</CODE> measurement.</LI>

## Needs updating (must do) ##
<LI><S>This needs testing against the legacy code to ensure outputs are reliable and repeatable before release</S></LI>
<LI><S><CODE>stray_light_correction</CODE> needs to be verified, the outputs seem much lower in the PL range after correction.</S> </LI>
<LI><S>Docstrings need updating</S></LI>
<LI>Laser correction factor and <S>hot pixel handling</S> need to be verified and implimented/removed as needed.</LI>
<LI><S>Stray light correction and common naming toggles are currently non-functional.</S></LI>

## Future work (nice-to-have) ##
<LI><S>Add functionality to analyses multiple files from one folder.</S></LI>
<LI><S>Add feature to enable alternative file naming for <CODE>_out</CODE> measurements, for instances where multiple spot <CODE>_in</CODE> measurements use the same <CODE>_out</CODE> measurement.</S></LI>


## References ##
[1]: J. C. de Mello, H. F. Wittmann, and R. H. Friend, ‘An improved experimental determination of external photoluminescence quantum efficiency’, Advanced Materials, vol. 9, no. 3, pp. 230–232, 1997, doi: 10.1002/adma.19970090308. 
