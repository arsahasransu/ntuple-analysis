import awkward as ak

import python.boost_hist as bh
from python.histos import GenParticleHistos


class GenParticleExtraHistos(GenParticleHistos):
    def __init__(self, name, root_file=None, pt_bins=None, debug=False):
        if not root_file:
            self.h_n = bh.TH1F(f'{name}_#', 'Gen Part #; #', 10, 0, 10)
            self.h_pdgid = bh.TH1F(f'{name}_pdgid', 'Gen Part pdgid; pdgid;', 100, -50, 50)
            self.h_phi = bh.TH1F(f'{name}_phi', 'Gen Part phi; #phi;', 640, -3.2, 3.2)
            self.h_prompt = bh.TH1F(f'{name}_promptStatus', 'Gen Part prompt status; prompt_status;', 1000, -500, 500)
            self.h_vz = bh.TH1F(f'{name}_zVertex', 'Gen Part vz; zVertex;', 1000, -500, 500)

        GenParticleHistos.__init__(self, name, root_file, pt_bins, debug)

    def fill(self, particles):
        # weights = None
        # if 'weights' in particles.fields:
        #     weights = particles.weights

        self.h_n.fill(ak.count(particles.pt, axis=1))
        bh.fill_1Dhist(hist=self.h_pdgid,
                       array=particles.pdgid)
        bh.fill_1Dhist(hist=self.h_phi,
                       array=particles.phi)
        bh.fill_1Dhist(hist=self.h_prompt,
                       array=particles.prompt)
        bh.fill_1Dhist(hist=self.h_vz,
                       array=particles.vz)
        
        GenParticleHistos.fill(self, particles)

class GenCaloParticleHistos(GenParticleExtraHistos):
    def __init__(self, name, root_file=None, pt_bins=None, debug=False):
        if not root_file:
            self.h_caloeta = bh.TH1F(f'{name}_caloeta', 'Gen Part calo eta; calo. #eta;', 100, -5, 5)
            self.h_calophi = bh.TH1F(f'{name}_calophi', 'Gen Part calo phi; calo. #phi;', 640, -3.2, 3.2)

        GenParticleExtraHistos.__init__(self, name, root_file, pt_bins, debug)

    def fill(self, particles):
        bh.fill_1Dhist(hist=self.h_caloeta,
                       array=particles.caloeta)
        bh.fill_1Dhist(hist=self.h_calophi,
                       array=particles.calophi)
        
        GenParticleExtraHistos.fill(self, particles)