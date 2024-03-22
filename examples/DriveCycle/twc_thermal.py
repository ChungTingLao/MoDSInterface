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

# This examples aims to run the TWC warmup case in SRM by hard-coding
# the input CUDS objects and passing them to the MoDS_Session class
# for execution.

def populateDataset(aDataset,data):
    data_header = data[0]
    data_values = data[1:]

    for row in data_values:
        data_point = mods.DataPoint()
        for header, value in zip(data_header, row):
            data_point.add(
                mods.DataPointItem(name=header, value=value),
                rel=mods.hasPart,
            )
        aDataset.add(data_point, rel=mods.hasPart)
    return aDataset

def evaluate_example(modelToLoad="twc-thermal"):
    logger.info(
        "################  Start: TWC thermal model ################")
    logger.info("Loading environment variables")
    load_dotenv()
    logger.info("Setting up the simulation inputs")

    twc_thermal_simulation = mods.SampleSRM()

    twc_thermal_algorithm = mods.Algorithm(
        name="algorithm1", type="SamplingAlg", modelToLoad=modelToLoad, saveSurrogate=False)
    x_value=",".join(["{:.1f}".format(i) for i in range(1801)])
    initialreaddetail=mods.InitialReadDetail(x_column="Time [s]",y_column="Wall Temperature at volume element 30 [K]",
                                             x_value=x_value,read_function="Get_DSV_y_at_x_double",
                                             lb_factor="0.9",ub_factor="1.1",lb_append="-0.0",ub_append="0.0",
                                             file="OutputCase00001Cyc0001Monolith001Layer001WallTemperature.csv")
    workingreaddetail=mods.WorkingReadDetail(x_column="Time [s]",y_column="Wall Temperature at volume element 30 [K]",
                                             x_value=x_value,read_function="Get_DSV_y_at_x_double")
    wall_temperature=mods.Variable(name="WallTemperature%20%28Layer%201%2C%20Vol%2E%20element%2030%29",type="output",nParams="1801")
    wall_temperature.add(workingreaddetail,rel=mods.hasPart)
    wall_temperature.add(initialreaddetail,rel=mods.hasPart)
    twc_thermal_algorithm.add(
        mods.Variable(name="Gas%20flow%20rate", type="input",
                      path="/srm_inputs/exhaust_aftertreatment/connection[@index='1'][@name='Main Inlet']/massflowrate/value"),
        mods.Variable(name="Environment%20temperature", type="input",
                      path="/srm_inputs/exhaust_aftertreatment/monolith[@index='1'][@name='Monolith #1']/gas/temperature/value"),
        wall_temperature
    )

    twc_thermal_simulation.add(twc_thermal_algorithm)

    example_input_data = [
        ["Gas%20flow%20rate", "Environment%20temperature"],
        [60000.0,605.0]
    ]

    input_data = populateDataset(mods.InputData(),example_input_data)

    twc_thermal_simulation.add(input_data)

    example_output_data = [
        ["WallTemperature%20%28Layer%201%2C%20Vol%2E%20element%2030%29"],
        [300.0]
    ]

    output_data = populateDataset(mods.OutputData(),example_output_data)

    twc_thermal_simulation.add(output_data)

    file = mods.File(file="OutputCase00001Cyc0001Monolith001Layer001WallTemperature.csv")

    twc_thermal_simulation.add(file)

    model_input = mods.ModelInput(path="All/Temperature.csv")

    example_model_input_data = [
        ["Time","Temperature"],
        [0.,700.],
        [1800.,1000.]
    ]

    model_input_data = populateDataset(mods.DataSet(),example_model_input_data)

    model_input.add(model_input_data, rel=mods.hasPart)

    twc_thermal_simulation.add(model_input)

    model_input = mods.ModelInput(path="All/MassFlowRate.csv")

    example_model_input_data = [
        ["Time","Mass Flow Rate"],
        [0.,10000.],
        [1800.,20000.]
    ]

    model_input_data = populateDataset(mods.DataSet(),example_model_input_data)

    model_input.add(model_input_data, rel=mods.hasPart)

    twc_thermal_simulation.add(model_input)
    
    export_cuds(twc_thermal_simulation,file=os.path.join(dir_path,"twc_thermal_in.ttl"), format="ttl")

    logger.info("Invoking the wrapper session")
    # Construct a wrapper and run a new session
    with ms.MoDS_Session() as session:
        wrapper = cuba.wrapper(session=session)
        wrapper.add(twc_thermal_simulation, rel=cuba.relationship)
        wrapper.session.run()

        output_data = search.find_cuds_objects_by_oclass(
            mods.OutputData, wrapper, rel=None
        )
        job_id = search.find_cuds_objects_by_oclass(
            mods.JobID, wrapper, rel=None
        )

        logger.info("Printing the simulation results.")

        if output_data: pretty_print(output_data[1]) # output_data[0] is the one created above as part of input
        
        if job_id: pretty_print(job_id[0])
    
    sampleSRM=search.find_cuds_objects_by_oclass(
        mods.SampleSRM, wrapper, rel=None
    )
    
    export_cuds(sampleSRM[0],file=os.path.join(dir_path,"twc_thermal_all.ttl"), format="ttl")
    
    export_cuds(output_data[1],file=os.path.join(dir_path,"twc_thermal_out.ttl"), format="ttl")

    logger.info("################  End: TWC thermal model ################")

    return output_data


if __name__ == "__main__":
    evaluate_example()
