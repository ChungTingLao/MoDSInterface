import os
from pathlib import Path

def downgrade(new_cuds,old_cuds):
    cwd = Path(__file__).parent.resolve()

    with open(os.path.join(cwd,new_cuds),'r') as f:
        content=f.readlines()

    new_content=['@prefix cuba: <http://www.osp-core.com/cuba#> .\n','@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n']

    # change namespace and add float specification

    for line in content:
        tmp_line=line.replace('https://www.simphony-osp.eu/entity','http://www.osp-core.com/cuds')
        new_content.append(tmp_line)
        # hack
        if "EvaluateSurrogate" in tmp_line:
            first=tmp_line.split('#')[1].split('>')[0]
    
    new_content.append('cuba:_serialization rdf:first "'+first+'" .')

    with open(os.path.join(cwd,old_cuds),'w') as f:
        f.writelines(new_content)

def upgrade(old_cuds,new_cuds):
    cwd = Path(__file__).parent.resolve()

    with open(os.path.join(cwd,old_cuds),'r') as f:
        content=f.readlines()

    new_content=[]

    # change namespace and add float specification

    for line in content:
        tmp_line=line.replace('http://www.osp-core.com/cuds','https://www.simphony-osp.eu/entity')
        if 'mods:value' in tmp_line:
            tmp_line=tmp_line.replace('" .','"^^xsd:float .')
        new_content.append(tmp_line)
        
    # hack to remove EvaluateSurrogate reference in OutputData

    for i in range(len(new_content)):
        if 'mods:OutputData' in new_content[i]:
            for j in range(i,len(new_content)):
                line=new_content[j]
                if 'mods:isPartOf' in line:
                    new_content[j-1]=new_content[j-1].replace(';','.')
                    new_content.pop(j)
                    stop_now=True
                    break
            if stop_now: break
    
    with open(os.path.join(cwd,new_cuds),'w') as f:
        f.writelines(new_content)