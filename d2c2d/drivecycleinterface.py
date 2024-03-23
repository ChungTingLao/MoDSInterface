from osp.core.namespaces import mods, cuba
import osp.core.utils.simple_search as search
import osp.wrappers.sim_cmcl_mods_wrapper.mods_session as ms
import urllib.parse
import numpy as np

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

def prepare_evaluate(surrogateToLoad,inputs,outputs,time):
    # define inputs for an "Evaluate" simulation.

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
    example_data.append(["Time [s]"]+[input["name"] for input in inputs])
    for i in range(len(inputs[0]["values"])):
        example_data.append([time[i]]+[input["values"][i] for input in inputs])

    input_data = populateDataset(mods.InputData(),example_data)

    evaluate_simulation.add(input_data)

    return evaluate_simulation

def prepare_twc_thermal(modelToLoad,time,temperature,massflowrate):
    # define inputs for the TWC thermal simulation.

    twc_thermal_simulation = mods.SampleSRM()
    twc_thermal_algorithm = mods.Algorithm(name="algorithm1", type="SamplingAlg", modelToLoad=modelToLoad, saveSurrogate=False)
    x_value=",".join(["{:.1f}".format(float(t)) for t in time])
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

def run(evaluate_simulation):
    # call MoDSSimpleAgent via wrapper, then get output data back

    # Construct a wrapper and run a new session
    with ms.MoDS_Session() as session:
        wrapper = cuba.wrapper(session=session)
        wrapper.add(evaluate_simulation, rel=cuba.relationship)
        wrapper.session.run()
        
        sim = search.find_cuds_objects_by_oclass(mods.Simulation, wrapper, rel=None)[0]

        output_data = search.find_cuds_objects_by_oclass(mods.OutputData, sim, rel=None)

        if output_data:
            return sim
        else:
            raise RuntimeError("No output is present.")

def outputtodict(sim,find_time=True):

    # convert output data into a dictionary object

    output={}
    
    output_data = search.find_cuds_objects_by_oclass(mods.OutputData, sim, rel=None)[-1]

    datapoints = search.find_cuds_objects_by_oclass(mods.DataPoint, output_data, rel=mods.hasPart)
    for datapoint in datapoints:
        if find_time:
            # copy time from input
            input_datapoint = datapoint.get(rel=mods.isDerivedFrom)[0]
            input_datapointitems = search.find_cuds_objects_by_oclass(mods.DataPointItem, input_datapoint, rel=mods.hasPart)
            for datapointitem in input_datapointitems:
                name=datapointitem.name
                value=datapointitem.value
                if "Time" in datapointitem.name:
                    if name not in output.keys():
                        output[name]=[value]
                    else:
                        output[name].append(value)
        datapointitems = search.find_cuds_objects_by_oclass(mods.DataPointItem, datapoint, rel=mods.hasPart)
        for datapointitem in datapointitems:
            name=datapointitem.name
            value=datapointitem.value
            if name not in output.keys():
                output[name]=[value]
            else:
                output[name].append(value)

    if find_time:
        # sort everything by time
        arr_time=[float(x) for x in output["Time [s]"]]
        index=np.argsort(arr_time)
        for var in output:
            output[var]=[output[var][i] for i in index]

    return output

def mods_wrapper(logger,input_cuds_object):
    
    logger.info("Evaluate engine surrogate")

    engine_out=outputtodict(run(input_cuds_object))

    logger.info("Run TWC thermal simulation")
    
    twc_thermal_out=outputtodict(
        run(prepare_twc_thermal("twc-thermal",
                                engine_out["Time [s]"],
                                engine_out["Temperature [K]"],
                                engine_out["Total flow [g/h]"])),
        find_time=False
        )
    
    # create input for TWC surrogate
    
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
        if "Temperature" in input["name"]:
            input["values"]=twc_thermal_out["WallTemperature (Layer 1, Vol. element 30)"]

    logger.info("Evaluate TWC surrogate")
    
    return run(prepare_evaluate("twc-model-6",twc_inputs,twc_outputs,engine_out["Time [s]"]))