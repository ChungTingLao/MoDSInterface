from numpy import maximum
import osp.core.utils.simple_search as search
from typing import Any, List
import osp.wrappers.sim_cmcl_mods_wrapper.engine_sim_templates as engtempl
from osp.core.cuds import Cuds
from osp.core.namespaces import mods, cuba
import json
import logging
from collections import defaultdict
from typing import Dict
from enum import Enum

logger = logging.getLogger(__name__)

INPUTS_KEY = "Inputs"
OUTPUTS_KEY = "Outputs"
ALGORITHMS_KEY = "Algorithms"
SIM_TYPE_KEY = "SimulationType"
OPTIONAL_ATTRS = ["objective", "maximum", "minimum", "weight"]

class CUDS_Adaptor:
    """Class to handle translation between CUDS and JSON objects."""

    @staticmethod
    def toJSON(root_cuds_object: Cuds, simulation_template: Enum) -> str:
        """Translates the input CUDS object to a JSON object matching the
        INPUT format of the remote MoDS simulation."""

        # NOTE - This translation relies heavily on the structure of the CUDS data,
        # which is defined by the ontology. If the ontology changes, it is likely
        # that this translation will need updating too. The translation is defined
        # in the agent_cases module.

        jsonData = defaultdict(list)

        # atm only MOO simulation template is supported, so the check
        # below, together with the template concept is not really needed.
        # However, once things get complicated, e.g. more MoDS backend
        # features will be supported, the template variable might be useful
        # for picking predefined CUDStoJSON and JSONtoCUDS translation
        # functions.
        if simulation_template == engtempl.Engine_Template.MOO or simulation_template == engtempl.Engine_Template.MOOonly or simulation_template == engtempl.Engine_Template.HDMR:
            logger.info("Registering inputs")
            
            jsonData[SIM_TYPE_KEY] = simulation_template.name

            CUDS_Adaptor.algorithmsCUDStoJSON(
                root_cuds_object=root_cuds_object,
                jsonData = jsonData,
            )

            CUDS_Adaptor.inputDataCUDStoJSON(
                root_cuds_object=root_cuds_object,
                jsonData = jsonData,
            )

            CUDS_Adaptor.inputAnalyticModelCUDStoJSON(
                root_cuds_object=root_cuds_object,
                jsonData = jsonData,
            )

            CUDS_Adaptor.inputAnalyticModelCUDStoJSON(
                root_cuds_object=root_cuds_object,
                jsonData = jsonData,
            )
        
        jsonDataStr = json.dumps(jsonData)
        return jsonDataStr

    @staticmethod
    def algorithmsCUDStoJSON(root_cuds_object, jsonData):
        algorithms: List[Cuds] = search.find_cuds_objects_by_oclass(
         mods.Algorithm, root_cuds_object, rel=None
        )  # type: ignore

        logger.info("Registering simulation algorithms.")
        if not algorithms:
            raise ValueError(
                (
                    "Missing Algorithm specification. "
                    "At least one Algorithm CUDS must be defined."
                )
            )

        for algorithm in algorithms:
            json_item = defaultdict(list)
            json_item['name'] = algorithm.name
            json_item['type'] = algorithm.type
            json_item['maxNumberOfResults'] = algorithm.maxNumberOfResults if algorithm.maxNumberOfResults!="None" else None
            json_item['saveSurrogate'] = algorithm.saveSurrogate if algorithm.saveSurrogate!="None" else None
            json_item['loadSurrogate'] = algorithm.loadSurrogate if algorithm.loadSurrogate!="None" else None
            json_item['variables'] = []

            variables = algorithm.get(oclass=mods.Variable)
            if not variables:
                raise ValueError(
                    (
                        "Missing algorithm Variable specification. "
                        "At least one Variable CUDS must be defined for each algorithm."
                    )
                )

            for var_item in variables: # type:ignore
                variables = {}
                variables["name"] = var_item.name
                variables["type"] = var_item.type
                for opt_attr in OPTIONAL_ATTRS:
                    opt_attr_value = getattr(var_item, opt_attr, "None")
                    if opt_attr_value != "None":
                        variables[opt_attr] = opt_attr_value
                json_item['variables'].append(variables)

            jsonData[ALGORITHMS_KEY].append(json_item)


    @staticmethod
    def inputDataCUDStoJSON(root_cuds_object, jsonData):
        dataPoints: List[Cuds] = search.find_cuds_objects_by_oclass(
         mods.DataPoint, root_cuds_object, rel=None
        )  # type: ignore
        loadSurrogate: List[Cuds] = search.find_cuds_objects_by_oclass(
         mods.Algorithm, root_cuds_object, rel=None
        )[0].loadSurrogate  # type: ignore

        logger.info("Registering simulation data points.")
        if not dataPoints and not loadSurrogate:
            raise ValueError(
                (
                    "Missing DataPoint specification. "
                    "At least one DataPoint CUDS must be defined or a surrogate must be loaded."
                )
            )

        json_items = defaultdict(list)
        for datum in dataPoints:
            datum_items = datum.get(oclass=mods.DataPointItem)
            if not datum_items:
                raise ValueError(
                    (
                        "Missing DataPointItem specification. "
                        "At least one DataPointItem CUDS must be "
                        "defined for each DataPoint."
                    )
                )

            for dat_item in datum_items: # type: ignore
                json_items[dat_item.name].append(dat_item.value)

        for name, values in json_items.items():
            jsonData[INPUTS_KEY].append({'name':name, 'values': values})

    @staticmethod
    def inputAnalyticModelCUDStoJSON(root_cuds_object, jsonData):
        analyticModels: List[Cuds] = search.find_cuds_objects_by_oclass(
         mods.AnalyticModel, root_cuds_object, rel=None
        )  # type: ignore

        logger.info("Registering simulation analytic models.")
        for model in analyticModels:
            model_funcs = model.get(oclass=mods.Function)
            if not model_funcs: return

            for func_item in model_funcs: # type: ignore
                jsonData[INPUTS_KEY].append({'name': func_item.name, 'formula': func_item.formula})

    simulation = None
    @staticmethod
    def toCUDS(
        root_cuds_object, jsonResults: Dict, simulation_template: Enum
    ) -> None:
        """Writes JSON output of an engine simulation into CUDS."""

        logger.info("Converting JSON output to CUDS")
        if not jsonResults:
            logger.warning("Empty JSON output. Nothing to convert.")
            return

        ParetoFront = mods.ParetoFront()

        if simulation_template == engtempl.Engine_Template.MOO or simulation_template == engtempl.Engine_Template.MOOonly:
            logger.info("Registering outputs")
            if simulation_template == engtempl.Engine_Template.MOOonly:
                simulation = root_cuds_object.get(oclass=mods.MultiObjectiveSimulationOnly, rel=cuba.relationship)[0]
            else:
                simulation = root_cuds_object.get(oclass=mods.MultiObjectiveSimulation, rel=cuba.relationship)[0]

            num_values = len(jsonResults[OUTPUTS_KEY][0]["values"])
            for i in range(num_values):
                data_point = mods.DataPoint()
                for output in jsonResults[OUTPUTS_KEY]:
                    out_value = output["values"][i]
                    out_name = output["name"]

                    data_point.add(
                        mods.DataPointItem(name=out_name, value=out_value),
                        rel=mods.hasPart,
                    )

                ParetoFront.add(data_point)
                
            simulation.add(ParetoFront)
        elif simulation_template == engtempl.Engine_Template.HDMR:
            simulation = root_cuds_object.get(oclass=mods.HighDimensionalModelRepresentationSimulation, rel=cuba.relationship)[0]

        job_id = mods.JobID()
        job_id.add(mods.JobIDItem(name=jsonResults["jobID"]), rel=mods.hasPart)
        simulation.add(job_id)
        
        logger.info("All outputs successfully registered.")
