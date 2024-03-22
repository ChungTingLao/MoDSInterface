import osp.core.pico as pico

if 'mods' in [x for x in pico.packages()]:
    pico.uninstall('mods')
    pico.install("ontology.mods.yml")