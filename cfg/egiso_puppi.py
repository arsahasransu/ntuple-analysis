from eg_puppi_iso.collections import gen_ele, puppi_ele
from eg_puppi_iso.plotters import GenPlotter, PuppiPlotter
from eg_puppi_iso.selections import gen_prompt_el_sel

from python.selections import Selection

all_genel_plotter = [GenPlotter(gen_ele, [Selection('all')])]
prompt_genel_plotter = [GenPlotter(gen_ele, gen_prompt_el_sel)]

all_puppi_plotter = [PuppiPlotter(puppi_ele, [Selection('all')])]