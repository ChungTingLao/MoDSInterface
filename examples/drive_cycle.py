import logging
from osp.core.namespaces import mods, cuba
from osp.core.utils import pretty_print, export_cuds, import_cuds
import osp.core.utils.simple_search as search
import osp.wrappers.sim_cmcl_mods_wrapper.mods_session as ms
from dotenv import load_dotenv
import urllib.parse
import csv
import numpy as np

# This examples aims to run the success story by hard-coding
# the input CUDS objects and passing them to the MoDS_Session class
# for execution.

def readcsvintodict(fn):
    # return a dictionary with headers as keys, columns as values
    dict_out={}
    with open(fn,'r') as f:
        NK=csv.reader(f)
        content=[row for row in NK]
    header=content[0]
    dict_idx={}
    for i in range(len(header)):
        dict_idx[i]=header[i]
    for i in range(len(header)):
        dict_out[header[i]]=[]
    for i in range(1,len(content)):
        for j in range(len(content[i])):
            try:
                dict_out[dict_idx[j]].append(float(content[i][j]))
            except:
                dict_out[dict_idx[j]].append(content[i][j])
    return dict_out

def getdrivecycle(n):
    # read drive cycle input data, then interpolate into n points (affect run time)
    drive_cycle=readcsvintodict('examples/EngineSurrogateInput.csv')
    time=np.linspace(0,1800.0,n)
    old_time=drive_cycle["Time [s]"]
    for key in drive_cycle.keys():
        drive_cycle[key]=np.interp(time,old_time,drive_cycle[key])
    return drive_cycle

def populateDataset(aDataset,data):
    # given input data, create Dataset instance
    data_header = data[0]
    data_values = data[1:]

    for row in data_values:
        data_point = mods.DataPoint()
        for header, value in zip(data_header, row):
            data_point.add(mods.DataPointItem(name=header, value=value),rel=mods.hasPart)
        aDataset.add(data_point, rel=mods.hasPart)
    return aDataset

def prepare_evaluate(logger,surrogateToLoad,inputs,outputs):
    # define inputs for an "Evaluate" simulation.
    logger.info("################  Start: Evaluate ################")
    logger.info("Loading surrogate: "+surrogateToLoad)
    logger.info("Setting up the simulation inputs")

    evaluate_simulation = mods.EvaluateSurrogate()
    hdmr_algorithm = mods.Algorithm(name="algorithm1", type="GenSurrogateAlg", surrogateToLoad=surrogateToLoad, saveSurrogate=False)
    evaluate_simulation.add(hdmr_algorithm)
    evaluate_algorithm = mods.Algorithm(name="algorithm2", type="SamplingAlg", saveSurrogate=False)
    for input in inputs:
        evaluate_algorithm.add(mods.Variable(name=input["name"], type="input"))
    for output in outputs:
        evaluate_algorithm.add(mods.Variable(name=output["name"], type="output"))
    evaluate_simulation.add(evaluate_algorithm)

    example_data=[]
    example_data.append([input["name"] for input in inputs])
    for i in range(len(inputs[0]["values"])):
        example_data.append([input["values"][i] for input in inputs])

    input_data = populateDataset(mods.InputData(),example_data)

    evaluate_simulation.add(input_data)

    return evaluate_simulation

def prepare_twc_thermal(logger,modelToLoad,time,temperature,massflowrate):
    # define inputs for the TWC thermal simulation.
    logger.info("################  Start: TWC thermal model ################")
    logger.info("Setting up the simulation inputs")

    twc_thermal_simulation = mods.SampleSRM()
    twc_thermal_algorithm = mods.Algorithm(name="algorithm1", type="SamplingAlg", modelToLoad=modelToLoad, saveSurrogate=False)
    x_value=",".join(["{:.1f}".format(t) for t in time])
    initialreaddetail=mods.InitialReadDetail(x_column="Time [s]",y_column="Wall Temperature at volume element 30 [K]",
                                             x_value=x_value,read_function="Get_DSV_y_at_x_double",
                                             lb_factor="0.9",ub_factor="1.1",lb_append="-0.0",ub_append="0.0",
                                             file="OutputCase00001Cyc0001Monolith001Layer001WallTemperature.csv")
    workingreaddetail=mods.WorkingReadDetail(x_column="Time [s]",y_column="Wall Temperature at volume element 30 [K]",
                                             x_value=x_value,read_function="Get_DSV_y_at_x_double")
    wall_temperature=mods.Variable(name="WallTemperature%20%28Layer%201%2C%20Vol%2E%20element%2030%29",type="output",nParams=str(len(time)))
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

    input_data = populateDataset(mods.InputData(),[["Gas%20flow%20rate", "Environment%20temperature"],[60000.0,605.0]])

    twc_thermal_simulation.add(input_data)

    output_data = populateDataset(mods.OutputData(),[["WallTemperature%20%28Layer%201%2C%20Vol%2E%20element%2030%29"],[300.0]])

    twc_thermal_simulation.add(output_data)

    twc_thermal_simulation.add(mods.File(file="OutputCase00001Cyc0001Monolith001Layer001WallTemperature.csv"))

    model_input = mods.ModelInput(path="All/Temperature.csv")

    example_model_input_data=[["Time","Temperature"]]
    for i in range(len(time)):
        example_model_input_data.append([time[i],temperature[i]])

    model_input_data = populateDataset(mods.DataSet(),example_model_input_data)

    model_input.add(model_input_data, rel=mods.hasPart)

    twc_thermal_simulation.add(model_input)

    model_input = mods.ModelInput(path="All/MassFlowRate.csv")

    example_model_input_data=[["Time","Mass Flow Rate"]]
    for i in range(len(time)):
        example_model_input_data.append([time[i],massflowrate[i]])

    model_input_data = populateDataset(mods.DataSet(),example_model_input_data)

    model_input.add(model_input_data, rel=mods.hasPart)

    twc_thermal_simulation.add(model_input)

    return twc_thermal_simulation

def run(logger,evaluate_simulation):
    # call MoDSSimpleAgent via wrapper, then get output data back

    logger.info("Invoking the wrapper session")
    # Construct a wrapper and run a new session
    with ms.MoDS_Session() as session:
        wrapper = cuba.wrapper(session=session)
        wrapper.add(evaluate_simulation, rel=cuba.relationship)
        wrapper.session.run()

        output_data = search.find_cuds_objects_by_oclass(mods.OutputData, wrapper, rel=None)

        logger.info("Printing the simulation results.")

        if output_data:
            pretty_print(output_data[-1])

    logger.info("################ End ################")

    return output_data[-1]

def outputtodict(output_data):

    # convert output data into a dictionary object

    output={}

    datapoints = search.find_cuds_objects_by_oclass(mods.DataPoint, output_data, rel=mods.hasPart)
    for datapoint in datapoints:
        datapointitems = search.find_cuds_objects_by_oclass(mods.DataPointItem, datapoint, rel=mods.hasPart)
        for datapointitem in datapointitems:
            name=datapointitem.name
            value=datapointitem.value
            if name not in output.keys():
                output[name]=[value]
            else:
                output[name].append(value)

    return output

def createtimefrominput(input_cuds_object):
    input_data = search.find_cuds_objects_by_oclass(mods.InputData, input_cuds_object, rel=None)
    datapoints = search.find_cuds_objects_by_oclass(mods.DataPoint, input_data[0], rel=mods.hasPart)
    drive_cycle=getdrivecycle(len(datapoints))
    return drive_cycle["Time [s]"]

if __name__ == "__main__":

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    logger.handlers[0].setFormatter(logging.Formatter("%(levelname)s %(asctime)s [%(name)s]: %(message)s"))
    logger.info("Loading environment variables")
    load_dotenv()

    try:
        input_cuds_object=import_cuds("examples/input_cuds_object.ttl", format="ttl")
        # create drive cycle time, assuming engine sampling points are evenly spaced in time from 0 to 1800 seconds
        drive_cycle_time=createtimefrominput(input_cuds_object)
    except:
        # create input CUDS object by code

        engine_inputs=[{"name":"Engine%20speed%20%5BRPM%5D"},{"name":"BMEP%20%5Bbar%5D"}]
        engine_outputs=[{"name":"CO%20mass%20fraction%20%5B%2D%5D"},
                        {"name":"CO2%20mass%20fraction%20%5B%2D%5D"},
                        {"name":"C3H6%20mass%20fraction%20%5B%2D%5D"},
                        {"name":"H2%20mass%20fraction%20%5B%2D%5D"},
                        {"name":"H2O%20mass%20fraction%20%5B%2D%5D"},
                        {"name":"NO%20mass%20fraction%20%5B%2D%5D"},
                        {"name":"O2%20mass%20fraction%20%5B%2D%5D"},
                        {"name":"N2%20mass%20fraction%20%5B%2D%5D"},
                        {"name":"Temperature%20%5BK%5D"},
                        {"name":"Total%20flow%20%5Bg%2Fh%5D"}
                        ]
        
        drive_cycle=getdrivecycle(181) # number of points will affect runtime
        drive_cycle_time=drive_cycle["Time [s]"]

        for input in engine_inputs:
            input["values"]=drive_cycle[urllib.parse.unquote(input["name"])]
        
        input_cuds_object=prepare_evaluate(logger,"engine-surrogate",engine_inputs,engine_outputs)

        export_cuds(input_cuds_object,file="examples/input_cuds_object.ttl", format="ttl")        

    engine_out=outputtodict(run(logger,input_cuds_object))

    twc_thermal_out=outputtodict(
        run(logger,prepare_twc_thermal(logger,"twc-thermal",
                                     drive_cycle_time,engine_out["Temperature [K]"],engine_out["Total flow [g/h]"])))
    
    print([key for key in engine_out.keys()])
    twc_inputs=[{"name":"Temperature%20%5BK%5D"},
                {"name":"Total%20flow%20%5Bg%2Fh%5D"},
                {"name":"Inlet%20CO%20mass%20fraction%20%5B%2D%5D"},
                {"name":"Inlet%20CO2%20mass%20fraction%20%5B%2D%5D"},
                {"name":"Inlet%20C3H6%20mass%20fraction%20%5B%2D%5D"},
                {"name":"Inlet%20H2%20mass%20fraction%20%5B%2D%5D"},
                {"name":"Inlet%20H2O%20mass%20fraction%20%5B%2D%5D"},
                {"name":"Inlet%20NO%20mass%20fraction%20%5B%2D%5D"},
                {"name":"Inlet%20O2%20mass%20fraction%20%5B%2D%5D"}       
                ]
    twc_outputs=[{"name":"Outlet%20CO%20mass%20fraction%20%5B%2D%5D"},
                 {"name":"Outlet%20CO2%20mass%20fraction%20%5B%2D%5D"},
                 {"name":"Outlet%20C3H6%20mass%20fraction%20%5B%2D%5D"},
                 {"name":"Outlet%20H2%20mass%20fraction%20%5B%2D%5D"},
                 {"name":"Outlet%20H2O%20mass%20fraction%20%5B%2D%5D"},
                 {"name":"Outlet%20NO%20mass%20fraction%20%5B%2D%5D"},
                 {"name":"Outlet%20O2%20mass%20fraction%20%5B%2D%5D"}
                ]

    for input in twc_inputs:
        input["values"]=engine_out[urllib.parse.unquote(input["name"]).replace("Inlet ","")]
        print(urllib.parse.unquote(input["name"].replace("Inlet ","")))
        if "Temperature" in input["name"]:
            input["values"]=twc_thermal_out["WallTemperature (Layer 1, Vol. element 30)"]
            print(input["name"])
    
    output_cuds_object=run(logger,prepare_evaluate(logger,"twc-model-6",twc_inputs,twc_outputs))

    # export

    export_cuds(output_cuds_object,file="examples/output_cuds_object.ttl", format="ttl")