from __future__ import absolute_import
import python.plotters as plotters
import python.collections as collections
import python.selections as selections


# simple_selections = (selections.Selector('^EGq[4-5]$')*('^Pt[1-3][0]$|all'))()

simple_selections = [selections.Selection("all", '', ''),
                     selections.Selection('Pt10', 'p_{T}^{TOBJ}>=10GeV', 'pt >= 10'),]

sta_selection = (selections.Selector('^IDTight[EPS]|all')*selections.Selector('^Pt5|all')*selections.Selector('^EtaABCDF$|all'))()
# print(f"simple_selections: {simple_selections}")

egid_iso_etatk_selections = (selections.Selector('^IDTight[EP]|all')*selections.Selector('^Iso|all')*selections.Selector('^Eta[F]$|^Eta[AF][ABCD]*[C]$'))()

l1tc_simple_plotters = [
    # EE Tk-electrons
    # plotters.TkElePlotter(collections.TkEleEE, egid_iso_etatk_selections),
    # plotters.TkElePlotter(collections.TkEleEB, egid_iso_etatk_selections),
    # plotters.TkElePlotter(collections.TkEleL2, egid_iso_etatk_selections),
    plotters.EGPlotter(collections.TkEmEE, sta_selection),
    plotters.EGPlotter(collections.TkEmEB, sta_selection),
    plotters.EGPlotter(collections.EGStaEE, sta_selection),
    plotters.EGPlotter(collections.EGStaEB, sta_selection),
    ]

quantization_plotters = [
    plotters.QuantizationPlotter(collections.hgc_cl3d,  simple_selections, ['pt', 'hoe', 'srrtot', 'meanz_scaled']),
    plotters.QuantizationPlotter(collections.tracks,  simple_selections, ['nStubs', 'chi2'])

]

# l1tc_pho_plotters = [

# ]
