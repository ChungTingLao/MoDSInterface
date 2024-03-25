import urllib.parse
import dlite
import os
import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path
dir_path = Path(__file__).parent.resolve()
dlite.storage_path.append(dir_path/"entities")

def findbyclass(relations,c):
    return [subj for subj, pred, obj in relations
            if pred == "_has-meta" and c in obj]

def findbysp(relations,s,p):
    return [obj for subj, pred, obj in relations
            if pred == p and s in subj]

def findbyhaspart(relations,s):
    return findbysp(relations,s,"http://www.osp-core.com/mods#hasPart")

def findbyderived(relations,s):
    return findbysp(relations,s,"http://www.osp-core.com/mods#isDerivedFrom")

def adddatapointitem(dict_result,relations,data_point):
    list_data_point_item = findbyhaspart(relations,data_point)
    for data_point_item in list_data_point_item:
        data_point_item_instance=dlite.get_instance(id=data_point_item)
        var_name=urllib.parse.unquote(data_point_item_instance.properties["name"])
        var_val=float(data_point_item_instance.properties["value"])
        if var_name not in dict_result:
            dict_result[var_name]=[var_val]
        else:
            dict_result[var_name].append(var_val)
    return dict_result

def readfromdlite(file_name,isOutput=False):

    dlite_all = dlite.Collection.from_location("json",os.path.join(dir_path,file_name),
                                                id="uuid-collection",) # the one with all the relations

    if isOutput:
        dataset = findbyclass(dlite_all.get_relations(),"OutputData")[0]
    else:
        dataset = findbyclass(dlite_all.get_relations(),"InputData")[0]

    list_data_point = findbyhaspart(dlite_all.get_relations(),dataset)

    dict_result={}

    for data_point in list_data_point:
        if isOutput:
            input_data_point = findbyderived(dlite_all.get_relations(),data_point)[0]
            dict_result = adddatapointitem(dict_result,dlite_all.get_relations(),input_data_point)
        dict_result = adddatapointitem(dict_result,dlite_all.get_relations(),data_point)
    
    # sort by time

    arr_time=[float(x) for x in dict_result["Time [s]"]]
    index=np.argsort(arr_time)
    for var in dict_result:
        dict_result[var]=[dict_result[var][i] for i in index]
    
    return dict_result

def plotfromdlite(dict_result,x,y,file_name):
    plt.figure()
    plt.plot(dict_result[x],dict_result[y])
    plt.xlabel(x)
    plt.ylabel(y)
    plt.savefig(file_name)
    plt.close()

def plotalldlite(dict_result):
    for k in dict_result.keys():
        if k != "Time [s]":
            print(k)
            plotfromdlite(dict_result,"Time [s]",k,
                          os.path.join(dir_path,k.split("[")[0].rstrip().lower().replace(' ', '_')))

if __name__ == "__main__":
    
    engine_in = readfromdlite("input_collection.json",isOutput=False)
    plotalldlite(engine_in)
    twc_out = readfromdlite("output_collection.json",isOutput=True)
    plotalldlite(twc_out)