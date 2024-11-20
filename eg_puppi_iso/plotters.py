from python.plotters import GenericDataFramePlotter

from .histos import CaloGenParticleHistos

class GenPlotter(GenericDataFramePlotter):
    def __init__(self, gen_set, gen_selections, pt_bins=None):
        super(GenPlotter, self).__init__(
            CaloGenParticleHistos,
            gen_set,
            gen_selections,
            pt_bins)
