import logging
from osp.core.namespaces import mods, cuba
from osp.core.utils import pretty_print, export_cuds
import osp.core.utils.simple_search as search
import osp.wrappers.sim_cmcl_mods_wrapper.mods_session as ms
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(
    logging.Formatter("%(levelname)s %(asctime)s [%(name)s]: %(message)s")
)

# This examples aims to run the amiii forward use case by hard-coding
# the input CUDS objects and passing them to the MoDS_Session class
# for execution.


def evaluate_example(surrogateToLoad="engine-surrogate"):
    logger.info(
        "################  Start: Engine Surrogate ################")
    logger.info("Loading environment variables")
    load_dotenv()
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
        ["Engine%20speed%20%5BRPM%5D", "BMEP%20%5Bbar%5D"],
        [1000.0,1.0],
        [1500.0,5.0],
        [2000.0,10.0]
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
    
    DataPoints = search.find_cuds_objects_by_oclass(
        mods.DataPoint, input_data, rel=mods.hasPart
    )
    
    list_input_data_uid=[]
    count=0
    
    for DP in DataPoints:
        count=count+1
        list_input_data_uid.append(DP.uid)
    
    pretty_print(input_data)
    
    export_cuds(evaluate_simulation,file="examples/engine_in.ttl", format="ttl")

    output_data = None

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

        if output_data:
            pretty_print(output_data[0])
            DataPoints = search.find_cuds_objects_by_oclass(
                mods.DataPoint, output_data[0], rel=mods.hasPart
            )
            
            list_output_data_uid=[]
            count=0
            
            for DP in DataPoints:
                count=count+1
                list_output_data_uid.append(DP.uid)
        if job_id:
            pretty_print(job_id[0])
        
        eva = search.find_cuds_objects_by_oclass(
            mods.EvaluateSurrogate, wrapper, rel=None
        )
        
        export_cuds(eva[0],file="examples/engine_all.ttl", format="ttl")

    logger.info(
        "################  End: Engine Surrogate ################")
    
    export_cuds(output_data[0],file="examples/engine_out.ttl", format="ttl")
    
    for i in range(count):
        DPi=search.find_cuds_object_by_uid(list_input_data_uid[i],eva[0],rel=None)
        items=search.find_cuds_objects_by_oclass(
            mods.DataPointItem, DPi, rel=mods.hasPart
        )
        for item in items:
            if "speed" in item.name:
                input_value=item.value
        DPo=search.find_cuds_object_by_uid(list_output_data_uid[i],eva[0],rel=None)
        items=search.find_cuds_objects_by_oclass(
            mods.DataPointItem, DPo, rel=mods.hasPart
        )
        for item in items:
            if "Temperature" in item.name:
                output_value=item.value
        print("speed= "+input_value+", temperature= "+output_value)
        

    return output_data


if __name__ == "__main__":
    evaluate_example()
