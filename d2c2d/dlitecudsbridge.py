import os

from pathlib import Path
import dlite
from simphony_osp.session import core_session
from simphony_osp.tools import import_file, export_file
from dlite_cuds.dlite2cuds import dlite2cuds
from dlite_cuds.cuds2dlite import create_instance
from simphony_osp.namespaces import mods

work_dir = Path(__file__).parent.resolve()
dlite.storage_path.append(work_dir/"entities")
mappings = dlite.Collection.from_location("json",work_dir/"mappings"/"mappings_ss5.json",)

def d2c(input_dlite,input_cuds_external):

    core_session.clear(force=True)

    ### DLite2CUDS ###

    dlite_all = dlite.Collection.from_location("json",work_dir/input_dlite,
                                            id="uuid-collection",) # the one with all the relations

    all_uuid = [subject for subject, predicate, obj in dlite_all.get_relations() if predicate == "_is-a"]
    
    cuds_instances = [dlite2cuds(simphony_session=core_session,ontology=mods,instance=dlite_inst,
                            mappings=mappings,mapping_iri="http://emmo.info/domain-mappings#mapsTo",relations=dlite_all,) 
                      for dlite_inst in [dlite_all.get(uuid) for uuid in all_uuid]]

    export_file(core_session,file=str(work_dir/input_cuds_external))

def c2d(output_cuds_internal,output_dlite):
        
    core_session.clear(force=True)

    ### CUDS2DLite ###

    import_file(file=str(work_dir/output_cuds_internal))

    collection = dlite.Collection(id="uuid-collection")

    for c in ['DataPointItem','DataPoint','OutputData']:

        label, coll = create_instance(simphony_session=core_session,cuds_class_iri="http://www.osp-core.com/mods#"+c,
            entity_uri="http://onto-ns.com/meta/0.1/"+c,mappings=mappings,collection=collection,)

    if os.path.exists(output_dlite): os.remove(output_dlite)
    collection.save(output_dlite)