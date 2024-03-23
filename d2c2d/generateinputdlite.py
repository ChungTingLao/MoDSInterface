from pathlib import Path
dir_path = Path(__file__).parent.resolve()
print(Path(__file__))

import os
import dlitecudsbridge as dcb
import simphonybridge as sb

from osp.core.namespaces import mods
from osp.core.utils import export_cuds
import urllib.parse
import csv
import numpy as np



def readcsvintodict(fn):
    # return a dictionary with headers as keys, columns as values
    dict_out={}
    with open(fn,'r') as f:
        NK=csv.reader(f)
        content=[row for row in NK]
    header=content[0]
    dict_idx={}
    for i in range(len(header)):
        dict_idx[i]=header[i]
    for i in range(len(header)):
        dict_out[header[i]]=[]
    for i in range(1,len(content)):
        for j in range(len(content[i])):
            try:
                dict_out[dict_idx[j]].append(float(content[i][j]))
            except:
                dict_out[dict_idx[j]].append(content[i][j])
    return dict_out

def getdrivecycle(path_input,n):
    # read drive cycle input data, then interpolate into n points (affect run time)
    drive_cycle=readcsvintodict(path_input)
    time=np.linspace(0,1800.0,n)
    old_time=drive_cycle["Time [s]"]
    for key in drive_cycle.keys():
        drive_cycle[key]=np.interp(time,old_time,drive_cycle[key])
    return drive_cycle

def populateDataset(aDataset,data):
    # given input data, create Dataset instance
    data_header = data[0]
    data_values = data[1:]

    for row in data_values:
        data_point = mods.DataPoint()
        for header, value in zip(data_header, row):
            data_point.add(mods.DataPointItem(name=header, value=value),rel=mods.hasPart)
        aDataset.add(data_point, rel=mods.hasPart)
    return aDataset

def prepare_evaluate(surrogateToLoad,inputs,outputs,time):

    evaluate_simulation = mods.EvaluateSurrogate()
    hdmr_algorithm = mods.Algorithm(name="algorithm1", type="GenSurrogateAlg", surrogateToLoad=surrogateToLoad, saveSurrogate=False)
    evaluate_simulation.add(hdmr_algorithm)
    evaluate_algorithm = mods.Algorithm(name="algorithm2", type="SamplingAlg", saveSurrogate=False)
    for input in inputs:
        evaluate_algorithm.add(mods.Variable(name=input["name"], type="input"))
    for output in outputs:
        evaluate_algorithm.add(mods.Variable(name=output["name"], type="output"))
    evaluate_simulation.add(evaluate_algorithm)

    example_data=[]
    example_data.append(["Time [s]"]+[input["name"] for input in inputs])
    for i in range(len(inputs[0]["values"])):
        example_data.append([time[i]]+[input["values"][i] for input in inputs])
    
    input_data = populateDataset(mods.InputData(),example_data)

    evaluate_simulation.add(input_data)

    return evaluate_simulation

def create_input_cuds(path_input,n):

    engine_inputs=[{"name":"Engine%20speed%20%5BRPM%5D"},{"name":"BMEP%20%5Bbar%5D"}]
    engine_outputs=[{"name":"CO%20mass%20fraction%20%5B%2D%5D"},
                    {"name":"CO2%20mass%20fraction%20%5B%2D%5D"},
                    {"name":"C3H6%20mass%20fraction%20%5B%2D%5D"},
                    {"name":"H2%20mass%20fraction%20%5B%2D%5D"},
                    {"name":"H2O%20mass%20fraction%20%5B%2D%5D"},
                    {"name":"NO%20mass%20fraction%20%5B%2D%5D"},
                    {"name":"O2%20mass%20fraction%20%5B%2D%5D"},
                    {"name":"N2%20mass%20fraction%20%5B%2D%5D"},
                    {"name":"Temperature%20%5BK%5D"},
                    {"name":"Total%20flow%20%5Bg%2Fh%5D"}
                    ]
    
    drive_cycle=getdrivecycle(path_input,n) # number of points will affect runtime

    for input in engine_inputs:
        input["values"]=drive_cycle[urllib.parse.unquote(input["name"])]
    input_cuds_object=prepare_evaluate("engine-surrogate",engine_inputs,engine_outputs,drive_cycle['Time [s]'])
    return input_cuds_object

input_cuds_object=create_input_cuds(os.path.join(dir_path,"EngineSurrogateInput.csv"),181)

export_cuds(input_cuds_object,file=os.path.join(dir_path,"drive_cycle_input_3.8.ttl"), format="ttl")
# force re-install ontologies for SimPhoNy 4

import simphony_osp.tools.pico as pico

list_namespaces=[x.name for x in pico.namespaces()]

if "mods" in list_namespaces: pico.uninstall("mods")
if "cuba" in list_namespaces: pico.uninstall("cuba")

pico.install(dir_path/"ontologies"/"cuba.yml")
pico.install(dir_path/"ontologies"/"mods.yml")

# SimPhoNy compatibility (3.8 to 4)

sb.upgrade(dir_path/"drive_cycle_input_3.8.ttl",dir_path/"drive_cycle_input_4.ttl")

# Convert to DLite using CUDS2DLite

dcb.c2d(output_cuds_internal=dir_path/"drive_cycle_input_4.ttl",output_dlite=os.path.join(dir_path,"input_collection.json"),
        list_c=["Algorithm","DataPoint","DataPointItem","EvaluateSurrogate","InputData","OutputData","Variable"])

for file in [dir_path/"drive_cycle_input_4.ttl",dir_path/"drive_cycle_input_3.8.ttl"]:
    if True: os.remove(file) # remove intermediate files