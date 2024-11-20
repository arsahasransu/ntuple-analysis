import awkward as ak

import python.boost_hist as bh
from python.histos import BaseHistos


class ThreeMomentumHistos(BaseHistos):
    def __init__(self, name, root_file=None, pt_bins=None, debug=False):
        if not root_file:
            self.h_pt = bh.TH1F(f'{name}_pt', '3-Momentum pt; pt;', 100, 0, 100)
            self.h_eta = bh.TH1F(f'{name}_eta', '3-Momentum eta; #eta;', 100, -5, 5)
            self.h_phi = bh.TH1F(f'{name}_phi', '3-Momentum phi; #phi;', 64, -3.2, 3.2)

        BaseHistos.__init__(self, name, root_file, debug)

    def fill(self, particles):
        bh.fill_1Dhist(hist=self.h_pt, array=particles.pt)
        bh.fill_1Dhist(hist=self.h_eta, array=particles.eta)
        bh.fill_1Dhist(hist=self.h_phi, array=particles.phi)


class ParticleHistos(ThreeMomentumHistos):
    def __init__(self, name, root_file=None, pt_bins=None, debug=False):
        if not root_file:
            self.h_n = bh.TH1F(f'{name}_#', 'Part #; #', 10, 0, 10)
            self.h_pdgid = bh.TH1F(f'{name}_pdgid', 'Part pdgid; pdgid;', 100, -50, 50)
            self.h_vz = bh.TH1F(f'{name}_zVertex', 'Part vz; zVertex;', 500, -25, 25)

        ThreeMomentumHistos.__init__(self, name, root_file, debug)
        
    def fill(self, particles):
        self.h_n.fill(ak.count(particles.pt, axis=1))
        bh.fill_1Dhist(hist=self.h_pdgid, array=particles.pdgid)
        bh.fill_1Dhist(hist=self.h_vz, array=particles.vz)

        ThreeMomentumHistos.fill(self, particles)


class GenParticleHistos(ParticleHistos):
    def __init__(self, name, root_file=None, pt_bins=None, debug=False):
        if not root_file:
            self.h_prompt = bh.TH1F(f'{name}_promptStatus', 'Gen Part prompt status; prompt_status;', 6, -1, 5)

        ParticleHistos.__init__(self, name, root_file, debug)
        
    def fill(self, particles):
        bh.fill_1Dhist(hist=self.h_prompt, array=particles.prompt)

        ParticleHistos.fill(self, particles)


class CaloGenParticleHistos(GenParticleHistos):
    def __init__(self, name, root_file=None, pt_bins=None, debug=False):
        if not root_file:
            self.h_caloeta = bh.TH1F(f'{name}_caloeta', 'Gen Part calo eta; calo. #eta;', 100, -5, 5)
            self.h_calophi = bh.TH1F(f'{name}_calophi', 'Gen Part calo phi; calo. #phi;', 64, -3.2, 3.2)

        GenParticleHistos.__init__(self, name, root_file, pt_bins, debug)

    def fill(self, particles):
        bh.fill_1Dhist(hist=self.h_caloeta,
                       array=particles.caloeta)
        bh.fill_1Dhist(hist=self.h_calophi,
                       array=particles.calophi)
        
        GenParticleHistos.fill(self, particles)