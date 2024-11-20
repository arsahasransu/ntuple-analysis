import numpy as np

from python.collections import DFCollection


def ele_pdg_fixture(particles):
    if 'pdgid' not in particles.fields:
        particles['pdgid'] = particles.charge*11
    return particles


gen_ele = DFCollection(
    name='genel', label='GEN particles (ele)',
    filler_function=lambda event, entry_block: event.getDataFrame(
        prefix='GenEl', entry_block=entry_block),
    fixture_function=ele_pdg_fixture,
    max_print_lines=None,
    debug=1)


puppi_ele = DFCollection(
    name='puppiel', label='PUPPI particle (ele)',
    filler_function=lambda event, entry_block: event.getDataFrame(
        prefix='PuppiEl', entry_block=entry_block),
        fixture_function=ele_pdg_fixture,
    max_print_lines=None,
    debug=1)
