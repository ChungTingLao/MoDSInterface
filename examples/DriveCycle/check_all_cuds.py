import urllib.parse
from osp.core.namespaces import mods, cuba
from osp.core.utils import import_cuds, pretty_print
import osp.core.utils.simple_search as search
import numpy as np
import os
import csv

from pathlib import Path
dir_path = Path(__file__).parent.resolve()

file_name="drive_cycle_engine_out"

eva=import_cuds(os.path.join(dir_path,file_name+".ttl"), format="ttl")
output_data = search.find_cuds_objects_by_oclass(mods.OutputData, eva, rel=mods.hasPart)[-1]
output_data_points = search.find_cuds_objects_by_oclass(mods.DataPoint, output_data, rel=mods.hasPart)

# read data points

def updateresult(result,name,value):
    if name not in result.keys():
        result[name]=[value]
    else:
        result[name].append(value)
    return result

result={}
num_points=len(output_data_points)

for output_data_point in output_data_points:
    input_data_point = output_data_point.get(rel=mods.isDerivedFrom)[0]
    input_items = search.find_cuds_objects_by_oclass(mods.DataPointItem, input_data_point, rel=mods.hasPart)
    output_items = search.find_cuds_objects_by_oclass(mods.DataPointItem, output_data_point, rel=mods.hasPart)
    for input_item in input_items:
        updateresult(result,"input:"+urllib.parse.unquote(input_item.name),input_item.value)
    for output_item in output_items:
        updateresult(result,"output:"+urllib.parse.unquote(output_item.name),output_item.value)

# sort data points

arr_time=[float(x) for x in result["input:Time [s]"]]
index=np.argsort(arr_time)
for var in result:
    result[var]=[result[var][i] for i in index]

# write to csv

with open(os.path.join(dir_path,file_name+".csv"),"w") as f:
    JY=csv.writer(f)
    header=list(result.keys())
    JY.writerow(header)
    for i in range(num_points):
        JY.writerow([result[key][i] for key in header])
    