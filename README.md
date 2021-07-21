# VirtualHome2KG
VirtualHome2KG is a system for constructing and augmenting knowledge graphs (KGs) of daily living activities using virtual space. We also provide an ontology to describe the structure of the KGs.
We used [VirtualHome](http://virtual-home.org/) as a platform of virtual space simulation. Thus, this repository is an extension of the [virtualhome](https://github.com/xavierpuigf/virtualhome).
Please see the original repository of the [virtualhome](https://github.com/xavierpuigf/virtualhome) for details of the Unity simulation. 

## Contents
1. Overview
2. Set Up
3. How to use
4. Ontology
<!--5. Knowledge graphs-->

## Overview

![overview](image/overview.png "Overview of VirtualHome2KG")

## Set Up

```bash
git clone https://github.com/aistairc/virtualhome2kg.git
```
We provide VirtualHome2KG as [Jupyter](https://jupyter.org/) notebooks. If you want to run the tools, install Jupyter and run it on your host.
<br/>
First of all, you need to build an environment where VirtualHome can run.
```bash
pip install -r requirements.txt
```
Second, you need to download the VirtualHome Unity Simulater and move it under `simulation/` (for MacOS) or `simulation/unity_simulator` (Windows).  
Please see the below link.  
[Download Unity Simulator
](https://github.com/xavierpuigf/virtualhome/blob/master/README.md#download-unity-simulator)  

Our experimental conditions:  
Local machine  
- MacBook Pro (13-inch, 2020, Four Thunderbolt 3 ports)
- macOS Catalina (10.15.7)
- CPU: 2.3 GHz Quad core Intel Core i7
- RAM: 32GB 3733 MHz LPDDR4X
- GPU: Intel Iris Plus Graphics 1536 MB
  
Server  
- Triplestore: GraphDB SE 9.6 by Ontotext
- OS: Windows 10 for Workstation
- CPU: Xeon Gold 5215L 10 cores
- RAM: 2.15TB
  
If you want to generate knowledge graphs based on the VirtualHome's activities, you need to downlowd the [dataset](https://github.com/xavierpuigf/virtualhome/tree/master/simulation#dataset).

## How to Use

### Simulation and export
First, you have to run the Unity simulator: [https://github.com/xavierpuigf/virtualhome#download-unity-simulator](https://github.com/xavierpuigf/virtualhome#download-unity-simulator).  
Second, you have to download the dataset of the VirtualHome from [here](http://virtual-home.org/release/programs/programs_processed_precond_nograb_morepreconds.zip), and move them to [dataset/](dataset/).  
<!--Script:  
```bash
cd scripts
python simulation_export.py [activity class (e.g., HygieneStyling, BedTimeSleep, and EatingDrinking)]
```-->
We provide two scripts for generating activity graphs (Note that the activity graph is not a knowledge graph. This is the simulation results described in JSON format).
The first one generates the activity graphs without recording objects' 3D coordinates and actions' duration (execution time). This script simulates without rendering on the Unity simulator to generate a lot of data in a short time.  
Jupyter notebook:  
Run [demo/generate_activitiy_graph.ipynb](demo/generate_activity_graph.ipynb)
  
The second one generates the activity graphs containing 3D coordinates and duration. This version simulates using the Unity simulator. Therefore, it takes a lot of time to generate the data. In addition, the executability of the simulation depends on the VirtualHome's Unity simulator.  
Jupyter notebook:  
Run [demo/generate_activitiy_graphi_with_bbox.ipynb](demo/generate_activity_graph_with_bbox.ipynb)
### Generate knowledge graphs
<!--Script:  
```bash
cd scripts
python create_rdf.py [activity name (folder name of the simulation results)]
```-->
Jupyter notebook:  
Run [demo/create_rdf.ipyb](demo/create_rdf.ipynb)
  
If you want to generate RDF file containing objects' bbox.  
Jupyter notebook:  
Run [demo/create_rdf_with_bbox.ipyb](demo/create_rdf_with_bbox.ipynb)
### Generate activity sequences
<!--Script:  
```bash
cd scripts
python markov_chain.py
```-->
Jupyter notebook:  
Run [demo/markov_chain.ipynb](demo/markov_chain.ipynb)

### Augment knowledge graphs
<!--```bash
cd scripts
python behavioral_data_augmentation.py
```-->
Jupyter notebook:  
Run [demo/behavioral_data_augmentation.ipynb](demo/behavioral_data_augmentation.ipynb)

## Ontology
We designed the ontology for the VirtualHome2KG. Please see [here](ontology) for learing more about our ontology.

<!--## Knowledge graphs
As samples, we generate several activity KGs. Please see [here](demo/graph_state_list).
-->
## License

<a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png" /></a><br /><span xmlns:dct="http://purl.org/dc/terms/" property="dct:title">VirtualHome2KG</span> by <a xmlns:cc="http://creativecommons.org/ns#" href="https://github.com/aistairc/virtualhome2kg/" property="cc:attributionName" rel="cc:attributionURL">Shusaku Egami, Satoshi Nishimura, Ken Fukuda</a> is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License</a>.<br />Based on a work at <a xmlns:dct="http://purl.org/dc/terms/" href="https://github.com/xavierpuigf/virtualhome" rel="dct:source">https://github.com/xavierpuigf/virtualhome</a>.
