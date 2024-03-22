import logging
from osp.core.namespaces import mods, cuba
from osp.core.utils import pretty_print, export_cuds
import osp.core.utils.simple_search as search
import osp.wrappers.sim_cmcl_mods_wrapper.mods_session as ms
from dotenv import load_dotenv
import os

from pathlib import Path
dir_path = Path(__file__).parent.resolve()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(
    logging.Formatter("%(levelname)s %(asctime)s [%(name)s]: %(message)s")
)

# This examples aims to run a engine surrogate by hard-coding
# the input CUDS objects and passing them to the MoDS_Session class
# for execution.


def evaluate_example(surrogateToLoad="engine-surrogate"):
    logger.info("################  Start: Engine Surrogate ################")
    load_dotenv()
    #os.environ["MODS_AGENT_BASE_URL"]="http://localhost:58085"
    logger.info("Setting up the simulation inputs")

    evaluate_simulation = mods.EvaluateSurrogate()

    hdmr_algorithm = mods.Algorithm(
        name="algorithm1", type="GenSurrogateAlg", surrogateToLoad=surrogateToLoad, saveSurrogate=False)
    evaluate_simulation.add(hdmr_algorithm)

    evaluate_algorithm = mods.Algorithm(
        name="algorithm2", type="SamplingAlg", saveSurrogate=False)
    evaluate_algorithm.add(
        mods.Variable(name="Engine%20speed%20%5BRPM%5D", type="input"),
        mods.Variable(name="BMEP%20%5Bbar%5D", type="input"),
        mods.Variable(name="CO%20mass%20fraction%20%5B%2D%5D",type="output"),
        mods.Variable(name="CO2%20mass%20fraction%20%5B%2D%5D",type="output"),
        mods.Variable(name="C3H6%20mass%20fraction%20%5B%2D%5D",type="output"),
        mods.Variable(name="H2%20mass%20fraction%20%5B%2D%5D",type="output"),
        mods.Variable(name="H2O%20mass%20fraction%20%5B%2D%5D",type="output"),
        mods.Variable(name="NO%20mass%20fraction%20%5B%2D%5D",type="output"),
        mods.Variable(name="O2%20mass%20fraction%20%5B%2D%5D",type="output"),
        mods.Variable(name="N2%20mass%20fraction%20%5B%2D%5D",type="output"),
        mods.Variable(name="Temperature%20%5BK%5D",type="output"),
        mods.Variable(name="Total%20flow%20%5Bg%2Fh%5D",type="output")
    )

    evaluate_simulation.add(evaluate_algorithm)

    example_data = [
        ["Time%5Bs%5D","Engine%20speed%20%5BRPM%5D", "BMEP%20%5Bbar%5D"],
        [0.0,1000.0,1.0],
        [900.0,1500.0,5.0],
        [1800.0,2000.0,10.0]
    ]

    example_data_header = example_data[0]
    example_data_values = example_data[1:]

    input_data = mods.InputData()

    for row in example_data_values:
        data_point = mods.DataPoint()
        for header, value in zip(example_data_header, row):
            data_point.add(
                mods.DataPointItem(name=header, value=value),
                rel=mods.hasPart,
            )
        input_data.add(data_point, rel=mods.hasPart)

    evaluate_simulation.add(input_data)
    
    export_cuds(evaluate_simulation,file=os.path.join(dir_path,"engine_in.ttl"), format="ttl")

    logger.info("Invoking the wrapper session")
    # Construct a wrapper and run a new session
    with ms.MoDS_Session() as session:
        wrapper = cuba.wrapper(session=session)
        wrapper.add(evaluate_simulation, rel=cuba.relationship)
        wrapper.session.run()

        output_data = search.find_cuds_objects_by_oclass(
            mods.OutputData, wrapper, rel=None
        )
        job_id = search.find_cuds_objects_by_oclass(
            mods.JobID, wrapper, rel=None
        )

        logger.info("Printing the simulation results.")

        if output_data: pretty_print(output_data[0])
            
        if job_id: pretty_print(job_id[0])
        
    eva = search.find_cuds_objects_by_oclass(
        mods.EvaluateSurrogate, wrapper, rel=None
    )
    
    export_cuds(eva[0],file=os.path.join(dir_path,"engine_all.ttl"), format="ttl")
    
    export_cuds(output_data[0],file=os.path.join(dir_path,"engine_out.ttl"), format="ttl")
    
    input_data = search.find_cuds_objects_by_oclass(
            mods.InputData, wrapper, rel=None
        )[0]
    
    list_input_data_point=search.find_cuds_objects_by_oclass(
        mods.DataPoint, input_data, rel=mods.hasPart
    )
    
    input_name="Time"
    output_name="Temperature"
    
    for input_data_point in list_input_data_point:
        input_value=find_data_point_item_by_name(input_data_point,input_name)
        output_data_point = input_data_point.get(rel=mods.isSourceOf)[0]
        output_value=find_data_point_item_by_name(output_data_point,output_name)
        print("%s=%s,%s=%s"%(input_name,input_value,output_name,output_value))
    
    logger.info("################  End: Engine Surrogate ################")

    return output_data

def find_data_point_item_by_name(data_point,name):
    items=search.find_cuds_objects_by_oclass(
        mods.DataPointItem, data_point, rel=mods.hasPart
    )
    for item in items:
        if name in item.name:
            return item.value

if __name__ == "__main__":
    evaluate_example()
