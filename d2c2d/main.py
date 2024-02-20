import os
import logging
from dotenv import load_dotenv
from osp.core.utils import export_cuds, import_cuds
import drivecycleinterface as dci
import dlitecudsbridge as dcb
import simphonybridge as sb

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(logging.Formatter("%(levelname)s %(asctime)s [%(name)s]: %(message)s"))
logger.info("Loading environment variables")
load_dotenv()

# Convert input DLite to CUDS using DLite2CUDS

dcb.d2c(input_dlite="input_collection.json",input_cuds_external="input_cuds_4.ttl")

# further processing for SimPhoNy compatibility (4 to 3.8)

sb.downgrade("input_cuds_4.ttl","input_cuds_3.8.ttl")

# MoDS wrapper takes input CUDS and call MoDS Agent, eventually return output as CUDS

input_cuds_internal=import_cuds("input_cuds_3.8.ttl",format="ttl")
output_cuds_internal=dci.mods_wrapper(input_cuds_internal,logger)
os.remove('tmp.json') # junk file from MoDS Interface
os.remove('out.json') # junk file from MoDS Interface
export_cuds(output_cuds_internal,file="output_cuds_3.8.ttl", format="ttl")

# further processing for SimPhoNy compatibility (3.8 to 4)

sb.upgrade("output_cuds_3.8.ttl","output_cuds_4.ttl")

# Convert to DLite using CUDS2DLite

dcb.c2d(output_cuds_internal="output_cuds_4.ttl",output_dlite="output_collection.json")