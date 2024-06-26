import logging
from osp.core.namespaces import mods, cuba
from osp.core.utils import pretty_print, export_cuds
import osp.core.utils.simple_search as search
import osp.wrappers.sim_cmcl_mods_wrapper.mods_session as ms
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(
    logging.Formatter("%(levelname)s %(asctime)s [%(name)s]: %(message)s")
)


def OntoFlow_MCDM_example():
    logger.info(
        "################ Start: MoDS OntoFlow MCDM Example ################")
    logger.info("Setting up the simulation inputs")

    mcdm_simulation = mods.MultiCriteriaDecisionMaking()
    mcdm_algorithm = mods.Algorithm(
        name="algorithm1", type="MCDM")

    mcdm_algorithm.add(
        # A value uniquely identifying the model (curretnly must be numerical)
        mods.Variable(name="ModelId", type="input"),

        # Optional (e.g. step size) can have multiple of these
        mods.Variable(name="ModelParameter", type="input"),

        # First cost of model (e.g. time)
        mods.Variable(name="Cost1", type="output",
                      objective="Minimise", maximum="18.0", weight="1"),

        # Second cost of model (e.g. uncertainty of final result)
        mods.Variable(name="Cost2", type="output",
                      objective="Minimise", maximum="0.1", weight="3"),
    )

    mcdm_simulation.add(mcdm_algorithm)

    example_data = [
        ["ModelId", "ModelParameter", "Cost1", "Cost2"],
        [1.0, 0.2, 20.0, 0.001],
        [2.0, 0.4, 17.0, 0.003],
        [3.0, 0.6, 16.0, 0.03],
        [4.0, 0.8, 10.0, 0.09],
        [5.0, 1.0, 5.0, 0.1],
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

    mcdm_simulation.add(input_data)
    
    export_cuds(mcdm_simulation,file="ontoflow_mcdm_input.ttl",format="ttl")

    logger.info("Invoking the wrapper session")
    # Construct a wrapper and run a new session
    with ms.MoDS_Session() as session:
        load_dotenv()
        wrapper = cuba.wrapper(session=session)
        wrapper.add(mcdm_simulation, rel=cuba.relationship)
        wrapper.session.run()
        
        sim = search.find_cuds_objects_by_oclass(mods.Simulation, wrapper, rel=None)[0]

        pareto_front = search.find_cuds_objects_by_oclass(
            mods.ParetoFront, wrapper, rel=None
        )
        job_id = search.find_cuds_objects_by_oclass(
            mods.JobID, wrapper, rel=None
        )

        logger.info("Printing the simulation results.")

        if pareto_front:
            pretty_print(pareto_front[0])
        if job_id:
            pretty_print(job_id[0])

    logger.info(
        "################ End: MoDS OntoFlow MCDM Example ################")
    
    export_cuds(pareto_front[0],file="ontoflow_mcdm_output.ttl",format="ttl")

    return job_id


if __name__ == "__main__":
    OntoFlow_MCDM_example()
