def downgrade(new_cuds,old_cuds):

    with open(new_cuds,'r') as f:
        content=f.readlines()

    new_content=['@prefix cuba: <http://www.osp-core.com/cuba#> .\n','@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n']

    # change namespace

    for line in content:
        tmp_line=line.replace('https://www.simphony-osp.eu/entity','http://www.osp-core.com/cuds')
        new_content.append(tmp_line)
        # EvaluateSurrogate is the highest-level object
        if "EvaluateSurrogate" in tmp_line:
            first=tmp_line.split('#')[1].split('>')[0]
    
    new_content.append('cuba:_serialization rdf:first "'+first+'" .')

    with open(old_cuds,'w') as f:
        f.writelines(new_content)

def upgrade(old_cuds,new_cuds):

    with open(old_cuds,'r') as f:
        content=f.readlines()

    new_content=[]

    # change namespace
    
    for line in content:
        tmp_line=line.replace('http://www.osp-core.com/cuds','https://www.simphony-osp.eu/entity')
        if 'mods:value' in tmp_line:
            tmp_line=tmp_line.replace('" .','"^^xsd:float .') # add float specification
        new_content.append(tmp_line)
        
    # remove wrapper reference in EvaluateSurrogate

    for i in range(len(new_content)):
        if 'cuba:relationship' in new_content[i]:
            new_content.pop(i)
            break
    
    with open(new_cuds,'w') as f:
        f.writelines(new_content)