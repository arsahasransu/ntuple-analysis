from python.plotters import GenericDataFramePlotter
from python.selections import Selection

from .histos import GenCaloParticleHistos

class GenPlotter(GenericDataFramePlotter):
    def __init__(self, gen_set, gen_selections=[Selection('all')], pt_bins=None):
        super(GenPlotter, self).__init__(
            GenCaloParticleHistos,
            gen_set,
            gen_selections,
            pt_bins)
