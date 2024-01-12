import logging
from osp.core.namespaces import mods, cuba
from osp.core.utils import pretty_print
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


def evaluate_example(surrogateToLoad="twc-model-6"):
    logger.info(
        "################  Start: TWC Surrogate ################")
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
        mods.Variable(name="Temperature%20%5BK%5D",type="input"),
        mods.Variable(name="Total%20flow%20%5Bg%2Fh%5D",type="input"),
        mods.Variable(name="Inlet%20CO%20mass%20fraction%20%5B%2D%5D",type="input"),
        mods.Variable(name="Inlet%20CO2%20mass%20fraction%20%5B%2D%5D",type="input"),
        mods.Variable(name="Inlet%20C3H6%20mass%20fraction%20%5B%2D%5D",type="input"),
        mods.Variable(name="Inlet%20H2%20mass%20fraction%20%5B%2D%5D",type="input"),
        mods.Variable(name="Inlet%20H2O%20mass%20fraction%20%5B%2D%5D",type="input"),
        mods.Variable(name="Inlet%20NO%20mass%20fraction%20%5B%2D%5D",type="input"),
        mods.Variable(name="Inlet%20O2%20mass%20fraction%20%5B%2D%5D",type="input"),
        mods.Variable(name="Outlet%20CO%20mass%20fraction%20%5B%2D%5D",type="output"),
        mods.Variable(name="Outlet%20CO2%20mass%20fraction%20%5B%2D%5D",type="output"),
        mods.Variable(name="Outlet%20C3H6%20mass%20fraction%20%5B%2D%5D",type="output"),
        mods.Variable(name="Outlet%20H2%20mass%20fraction%20%5B%2D%5D",type="output"),
        mods.Variable(name="Outlet%20H2O%20mass%20fraction%20%5B%2D%5D",type="output"),
        mods.Variable(name="Outlet%20NO%20mass%20fraction%20%5B%2D%5D",type="output"),
        mods.Variable(name="Outlet%20O2%20mass%20fraction%20%5B%2D%5D",type="output")        
    )

    evaluate_simulation.add(evaluate_algorithm)

    example_data = [
        ["Temperature%20%5BK%5D","Total%20flow%20%5Bg%2Fh%5D",
         "Inlet%20CO%20mass%20fraction%20%5B%2D%5D","Inlet%20CO2%20mass%20fraction%20%5B%2D%5D",
         "Inlet%20C3H6%20mass%20fraction%20%5B%2D%5D","Inlet%20H2%20mass%20fraction%20%5B%2D%5D",
         "Inlet%20H2O%20mass%20fraction%20%5B%2D%5D","Inlet%20NO%20mass%20fraction%20%5B%2D%5D","Inlet%20O2%20mass%20fraction%20%5B%2D%5D"],
        [300.,9614.,0.00423872,0.070268,0.0205358,7.336e-5,0.053835,0.0012947,0.07026804],
        [908.,10626.,0.003077,0.04493,0.013256,5.7013293e-5,0.063,0.001863,0.0449314]
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
        if job_id:
            pretty_print(job_id[0])

    logger.info(
        "################  End: TWC Surrogate ################")

    return output_data


if __name__ == "__main__":
    evaluate_example()
