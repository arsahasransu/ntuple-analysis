from python.plotters import BasePlotter, GenericDataFramePlotter

from .histos import CaloGenParticleHistos, ParticleHistos


class GenPlotter(GenericDataFramePlotter):
    def __init__(self, gen_set, gen_selections, pt_bins=None):
        super(GenPlotter, self).__init__(
            CaloGenParticleHistos,
            gen_set,
            gen_selections,
            pt_bins)


class PuppiPlotter(GenericDataFramePlotter):
    def __init__(self, puppi_set, puppi_selections, pt_bins=None):
        super(PuppiPlotter, self).__init__(
            ParticleHistos,
            puppi_set,
            puppi_selections,
            pt_bins)
        

class GenMatchPlotter(BasePlotter):
    def __init__(self, gen_set, data_set, gen_sel, data_sel, pt_bins=None):
        super(GenMatchPlotter, self).__init__(
            CaloGenParticleHistos,
            gen_set,
            gen_selections,
            pt_bins)
        