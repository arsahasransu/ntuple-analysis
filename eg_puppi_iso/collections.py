import numpy as np

from python.collections import DFCollection


def mc_fixtures(particles):
    particles['abseta'] = np.abs(particles.eta)
    return particles


def ele_mc_fixtures(particles):
    if 'pdgid' not in particles.fields:
        particles['pdgid'] = particles.charge*11
    return mc_fixtures(particles)


gen_ele = DFCollection(
    name='genel', label='GEN particles (ele)',
    filler_function=lambda event, entry_block: event.getDataFrame(
        prefix='GenEl', entry_block=entry_block),
    fixture_function=ele_mc_fixtures,
    max_print_lines=None,
    debug=1)