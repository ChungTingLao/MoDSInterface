from osp.core.cuds import Cuds
from osp.core.namespaces import mods
import osp.core.utils.simple_search as search
from osp.wrappers.sim_cmcl_mods_wrapper.cuds_adaptor import CUDS_Adaptor
import osp.wrappers.sim_cmcl_mods_wrapper.engine_exceptions as enexc
import osp.wrappers.sim_cmcl_mods_wrapper.engine_sim_templates as engtempl
import logging
from typing import Dict
from enum import Enum

logger = logging.getLogger(__name__)

class MoDS_Engine:
    """Engine handling data objects for the MoDS use cases."""

    # current template
    simulation_template = engtempl.Engine_Template.MOO

    name = "MoDS Engine"

    def __init__(self):
        """Initialise a new SimulationEngine instance."""
        logger.info(f"New '{self.__class__.__name__ }' instantiated!")

    def __str__(self):
        """Textual representation.

        Returns:
            Textual representation.
        """
        return self.__class__.__name__

    def determineTemplate(self, root_cuds_object: Cuds) -> None:
        """Determines which simulation template to use based on the modelFlag."""

        simulation_list = search.find_cuds_objects_by_oclass(
            mods.Simulation, root_cuds_object, rel=None)  # type: ignore

        if len(simulation_list) != 1:
            logger.error("Invalid number of simulations defined: %s",
                         str(len(simulation_list)))
            return

        simulation_class = simulation_list[0].oclass

        if simulation_class == mods.MultiObjectiveSimulation:
            self.simulation_template = engtempl.Engine_Template.MOO
        elif simulation_class == mods.MultiObjectiveSimulationOnly:
            self.simulation_template = engtempl.Engine_Template.MOOonly
        elif simulation_class == mods.HighDimensionalModelRepresentationSimulation:
            self.simulation_template = engtempl.Engine_Template.HDMR
        elif simulation_class == mods.EvaluateSurrogate:
            self.simulation_template = engtempl.Engine_Template.Evaluate
        elif simulation_class == mods.SensitivityAnalysis:
            self.simulation_template = engtempl.Engine_Template.Sensitivity
        elif simulation_class == mods.MultiCriteriaDecisionMaking:
            self.simulation_template = engtempl.Engine_Template.MCDM
        else:
            raise enexc.UnsupportedSimulationType

        logger.info("Detected simulation template as %s",
                    self.simulation_template.name)

    def generateJSON(self, root_cuds_object: Cuds) -> str:
        """Generates JSON input string from CUDS."""

        self.executed = False

        # Build the JSON data from the CUDS objects
        jsonSimCase = CUDS_Adaptor.toJSON(root_cuds_object, self.simulation_template)
        logger.info("JSON data successfully generated from CUDS objects.")
        return jsonSimCase

    def parseResults(self, root_cuds_object, jsonResults: Dict) -> None:
        """Given the results of a remote simulation in JSON form, this
        function parses them in to CUDS objects."""

        # Use the CUDS_Adaptor to fill CUDS objects with results
        CUDS_Adaptor.toCUDS(root_cuds_object, jsonResults, self.simulation_template)
        logger.info("CUDS objects have now been populated with simulation results.")
        self.successful = True

    def hasExecuted(self) -> bool:
        """Returns true if this engine instance has been executed."""
        return self.executed

    def wasSuccessful(self) -> bool:
        """Returns true if the remote simulation completed successfully."""
        return self.successful
