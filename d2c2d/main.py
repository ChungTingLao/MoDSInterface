import os
from pathlib import Path
from dotenv import load_dotenv
from osp.core.utils import export_cuds, import_cuds
import drivecycleinterface as dci
import dlitecudsbridge as dcb
import simphonybridge as sb

load_dotenv()
cwd = Path(__file__).parent.resolve()

# force re-install ontologies for SimPhoNy 4

if True:

    import simphony_osp.tools.pico as pico

    list_namespaces=[x.name for x in pico.namespaces()]

    if "mods" in list_namespaces:
        pico.uninstall("mods")
    if "cuba" in list_namespaces:
        pico.uninstall("cuba")

    pico.install(cwd/"ontologies"/"cuba.yml")
    pico.install(cwd/"ontologies"/"mods.yml")

# Convert input DLite to CUDS using DLite2CUDS

dcb.d2c(input_dlite=cwd/"input_collection.json",input_cuds_external=cwd/"input_cuds_4.ttl")

# further processing for SimPhoNy compatibility (4 to 3.8)

sb.downgrade(cwd/"input_cuds_4.ttl",cwd/"input_cuds_3.8.ttl")

# MoDS wrapper takes input CUDS and call MoDS Agent, eventually return output as CUDS

input_cuds_internal=import_cuds(os.path.join(cwd,"input_cuds_3.8.ttl"),format="ttl")
output_cuds_internal=dci.mods_wrapper(input_cuds_internal)
export_cuds(output_cuds_internal,file=os.path.join(cwd,"output_cuds_3.8.ttl"), format="ttl")

# further processing for SimPhoNy compatibility (3.8 to 4)

sb.upgrade(cwd/"output_cuds_3.8.ttl",cwd/"output_cuds_4.ttl")

# Convert to DLite using CUDS2DLite

dcb.c2d(output_cuds_internal=cwd/"output_cuds_4.ttl",output_dlite=os.path.join(cwd,"output_collection.json"))

for file in ['tmp.json','out.json',cwd/"input_cuds_3.8.ttl",cwd/"input_cuds_4.ttl",cwd/"output_cuds_3.8.ttl",cwd/"output_cuds_4.ttl"]:
    if True: os.remove(file) # remove intermediate files