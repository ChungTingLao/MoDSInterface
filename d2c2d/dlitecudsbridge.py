def d2c(input_dlite,input_cuds_external):

    from pathlib import Path
    import dlite
    from simphony_osp.session import core_session
    from simphony_osp.tools import export_file
    from dlite_cuds.dlite2cuds import dlite2cuds
    from simphony_osp.namespaces import mods
    
    work_dir = Path(__file__).parent.resolve()

    # import DLite instance
    
    dlite.storage_path.append(work_dir/"entities")

    # Get the mappings
    mappings = dlite.Collection.from_location("json",work_dir/"mappings"/"mappings_ss5.json",)
    mapping_iri = "http://emmo.info/domain-mappings#mapsTo"

    ### DLite2CUDS ###

    dlite_all = dlite.Collection.from_location("json",work_dir/input_dlite,
                                            id="uuid-collection",) # the one with all the relations

    all_uuid=[]

    for subject, predicate, obj in dlite_all.get_relations():
        if predicate in ["_is-a", "_has-meta", "_has-uuid"]:
            continue
        all_uuid.append(subject)
        all_uuid.append(obj)
        all_uuid=list(set(all_uuid))

    core_session.clear(force=True)

    for uuid in all_uuid:
        dlite_inst = dlite_all.get(uuid)
        cuds_inst = dlite2cuds(simphony_session=core_session,ontology=mods,instance=dlite_inst,
                            mappings=mappings,mapping_iri=mapping_iri,relations=dlite_all,)
    
    # add them again see what happens
    
    for uuid in all_uuid:
        dlite_inst = dlite_all.get(uuid)
        cuds_inst = dlite2cuds(simphony_session=core_session,ontology=mods,instance=dlite_inst,
                            mappings=mappings,mapping_iri=mapping_iri,relations=dlite_all,)

    export_file(core_session,file=str(work_dir/input_cuds_external))

def c2d(output_cuds_internal,output_dlite):
    import os

    from pathlib import Path
    import dlite
    from simphony_osp.session import core_session
    from simphony_osp.tools import import_file
    from dlite_cuds.cuds2dlite import create_instance
    from simphony_osp.namespaces import mods
    
    core_session.clear(force=True)
    
    work_dir = Path(__file__).parent.resolve()

    # import DLite instance
    dlite.storage_path.append(work_dir/"entities")
    print(dlite.storage_path)

    # Get the mappings
    mappings = dlite.Collection.from_location("json",work_dir/"mappings"/"mappings_ss5.json",)

    ### CUDS2DLite ###

    import_file(file=str(work_dir/output_cuds_internal))

    collection = dlite.Collection(id="uuid-collection")

    list_class=['DataPointItem','DataPoint','OutputData']

    for c in list_class:

        label, coll = create_instance(simphony_session=core_session,cuds_class_iri="http://www.osp-core.com/mods#"+c,
            entity_uri="http://onto-ns.com/meta/0.1/"+c,mappings=mappings,collection=collection,)

    if os.path.exists(output_dlite): os.remove(output_dlite)
    collection.save(output_dlite)