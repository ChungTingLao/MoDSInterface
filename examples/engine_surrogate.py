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
        [7.433921000000000276e+02,0.000000000000000000e+00],
        [7.438565710999999965e+02,0.000000000000000000e+00],
        [7.443265066000000161e+02,0.000000000000000000e+00],
        [7.448182996000000458e+02,0.000000000000000000e+00],
        [7.453100924999999961e+02,0.000000000000000000e+00],
        [7.458018855000000258e+02,0.000000000000000000e+00],
        [7.462936783999999761e+02,0.000000000000000000e+00],
        [7.467854714000000058e+02,0.000000000000000000e+00],
        [7.472772644000000355e+02,0.000000000000000000e+00],
        [7.477690572999999858e+02,3.919999999999999941e-18],
        [7.482608503000000155e+02,3.530095999999999928e-03],
        [7.487315873999999667e+02,8.614867000000000011e-03],
        [7.491181014999999661e+02,1.991833800000000071e-02],
        [7.493930477000000110e+02,2.076699400000000043e-02],
        [7.495006421000000500e+02,5.933426999999999799e-03],
        [7.496082366000000548e+02,0.000000000000000000e+00],
        [7.497158309999999801e+02,0.000000000000000000e+00],
        [7.498234254999999848e+02,0.000000000000000000e+00],
        [7.499310199000000239e+02,0.000000000000000000e+00],
        [7.500386144000000286e+02,0.000000000000000000e+00]
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
        "################  End: Engine Surrogate ################")

    return output_data


if __name__ == "__main__":
    evaluate_example()
