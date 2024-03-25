import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from osp.core.utils import export_cuds, import_cuds
import drivecycleinterface as dci
import dlitecudsbridge as dcb
import simphonybridge as sb
import sys

def blockPrint():
    sys.stdout = open(os.devnull, 'w')

def enablePrint():
    sys.stdout = sys.__stdout__

#load_dotenv()
os.environ["MODS_AGENT_BASE_URL"]="http://localhost:58085"
cwd = Path(__file__).parent.resolve()

logging.getLogger("osp.wrappers.sim_cmcl_mods_wrapper").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(logging.Formatter("%(levelname)s %(asctime)s [%(name)s]: %(message)s"))

logger.info("Force re-install ontologies for SimPhoNy 4")

import simphony_osp.tools.pico as pico

list_namespaces=[x.name for x in pico.namespaces()]

if "mods" in list_namespaces: pico.uninstall("mods")
if "cuba" in list_namespaces: pico.uninstall("cuba")

pico.install(cwd/"ontologies"/"cuba.yml")
pico.install(cwd/"ontologies"/"mods.yml")

logger.info("Convert input DLite to CUDS")

blockPrint()
dcb.d2c(input_dlite=cwd/"input_collection.json",input_cuds_external=cwd/"input_cuds_4.ttl")
enablePrint()

logger.info("SimPhoNy compatibility (4 to 3.8)")

sb.downgrade(cwd/"input_cuds_4.ttl",cwd/"input_cuds_3.8.ttl")

logger.info("Call MoDS wrapper")

input_cuds_internal=import_cuds(os.path.join(cwd,"input_cuds_3.8.ttl"),format="ttl")
output_cuds_internal=dci.mods_wrapper(logger,input_cuds_internal)
export_cuds(output_cuds_internal,file=os.path.join(cwd,"output_cuds_3.8.ttl"), format="ttl")

logger.info("SimPhoNy compatibility (3.8 to 4)")

sb.upgrade(cwd/"output_cuds_3.8.ttl",cwd/"output_cuds_4.ttl")

logger.info("Convert output CUDS to DLite")
blockPrint()
dcb.c2d(output_cuds_internal=cwd/"output_cuds_4.ttl",output_dlite=os.path.join(cwd,"output_collection.json"),
        list_c=["Algorithm","DataPoint","DataPointItem","EvaluateSurrogate","InputData","OutputData","Variable"])
enablePrint()

for file in [cwd/"input_cuds_3.8.ttl",cwd/"input_cuds_4.ttl",cwd/"output_cuds_3.8.ttl",cwd/"output_cuds_4.ttl"]:
    if True: os.remove(file) # remove intermediate files