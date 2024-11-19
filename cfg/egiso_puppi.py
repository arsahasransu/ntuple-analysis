from eg_puppi_iso.collections import gen_ele
from eg_puppi_iso.plotters import GenPlotter
from eg_puppi_iso.selections import gen_prompt_el_sel

from python.selections import Selection

all_genel_plotter = [GenPlotter(gen_ele, [Selection('all')])]
prompt_genel_plotter = [GenPlotter(gen_ele, gen_prompt_el_sel)]