## Quick start guide for running standalone executable

Go to the latest release *via* the "Releases" tab, then:

1. Download the source code file bundle (```.zip``` or ```.tar.gz``` format).
2. Download one of the executables (```.exe```).
3. Double-click the ```.exe``` file and ```StrEmbed-5-6``` will run.

___

# StrEmbed-5-6

Version 5-6 of Structure Embedding

Part of the Design Configuration Spaces (DCS) project hosted by the University of Leeds

Hugh Rice (HR/HPR), Tom Hazlehurst (TH) and Hau Hing Chau (HHC)

January 2020-February 2021

School of Mechanical Engineering  
University of Leeds  
LS2 9JT

All communication, including bug/issues reports, to: h.p.rice@leeds.ac.uk

___

<i> ```StrEmbed-5-6``` is a graphical user interface for visualisation and manipulation of part-whole relationships in assemblies of parts, and is written in Python. The user can read files in the [STEP format](https://en.wikipedia.org/wiki/ISO_10303-21), which is a common data exchange format containing both assembly information (i.e. part-whole information) and shape data. Functionality is based on [```StrEmbed-4```](https://github.com/hhchau/StrEmbed-4) (and earlier versions) by Hau Hing Chau, written in Perl.</i>  

<b>This research is supported by the UK Engineering and Physical Sciences Research Council (EPSRC) under grant number EP/S016406/1.</b>

___

## Full guide

There are several ways to run ```StrEmbed-5-6```, which are described below and in more detail in the user manual. The simplest is to download the latest release, which contains all the Python scripts and a standalone executable file. To run ```StrEmbed-5-6``` you can then do one of the following:

(1) Run as a Python script in your own environment. Two scripts are required:

1. ```StrEmbed_5_6``` (main script)
2. ```step_parse_5_6``` (contains class for for file and graph operations)

The above incorporate code (specifically for the 3D viewer) from ```Python-OCC``` [here](https://github.com/tpaviot/pythonocc-core). ```StrEmbed-5-6``` has a large number of dependencies that must also be installed in your environment. Contact the developers of those packages if you encounter problems. The script ```env_setup.txt``` can be run as a batch file in an Anaconda shell to create an environment in which ```StrEmbed-5-6``` will run.

(2) Run as a standalone executable. This does not require you to have Python or any IDE installed. Simply double-click on one of the files ending with  ```.exe``` and the user interface will appear. Please note that two executables are provided, with and without console output for debugging purposes. Please make a record of the output if you encounter problems and wish to contact the developers for help.

Several STEP file examples are provided. The "Images" folder contains images necessary for building the application but not for running it. Temporary images corresponding to the parts in a loaded STEP file are also stored in a folder called "Temp" that is created and destroyed at runtime and which the user may delete at any time.

```StrEmbed-5-6``` was developed in Spyder, an IDE for Python that is packaged with the Anaconda distribution, which can be downloaded [here](https://www.anaconda.com/distribution/).

```StrEmbed-5-6``` is published under the GNU General Purpose License version 3, which is given in the LICENSE document.
