import ROOT
import math
import uuid

# some useful globals, mainly to deal with ROOT idiosyncrasies
c_idx = 0
p_idx = 0
colors = range(1, 6)
stuff = []
f_idx = 0

ROOT.gStyle.SetPadBottomMargin(0.13)
ROOT.gStyle.SetPadLeftMargin(0.13)
ROOT.gStyle.SetPadRightMargin(0.30)

ROOT.gStyle.SetCanvasBorderMode(0)
ROOT.gStyle.SetCanvasColor(0)
ROOT.gStyle.SetCanvasDefH(600)
ROOT.gStyle.SetCanvasDefW(800)

# define some utility functions
def newCanvas(name=None, title=None, xdiv=0, ydiv=0, form=4):
    global c_idx
    if name is None:
        name = 'c_{}'.format(uuid.uuid4().hex[:6])
        c_idx += 1
    if title is None:
        title = name
    # print name, title
    canvas = ROOT.TCanvas(name, title)
    if(xdiv*ydiv != 0):
        canvas.Divide(xdiv, ydiv)
    global stuff
    stuff.append(canvas)
    return canvas


def draw(plot, options='', text=None):
    c = newCanvas()
    c.cd()
    plot.Draw(options)
    if text:
        rtext = getText(text, 0.15, 0.85)
        rtext.Draw('same')

    c.Draw()

    return


def drawAll(histograms,
            labels=None,
            options='',
            text=None,
            norm=False,
            logy=False,
            min_y=None,
            max_y=None,
            y_axis_label=None,
            do_ratio=False,
            do_profile=False):
    if len(histograms) == 0:
        print 'ERROR: no histogram in input'
        return -1
    if do_ratio and len(histograms) != 2:
        print 'ERROR: do_ratio option only available when 2 histograms need to be drawn!'
        return -2
    if do_profile and not ('TH2' in histograms[0].ClassName() or 'TH3' in histograms[0].ClassName()):
        print 'ERROR: do_profile option only available with TH2 and TH3 histograms'
        return -3

    # we build the canvas
    return


def drawAll(histograms,
            labels=None,
            options='',
            text=None,
            norm=False,
            logy=False,
            min_y=None,
            max_y=None,
            y_axis_label=None,
            do_ratio=False,
            do_profile=False):
    if len(histograms) == 0:
        print 'ERROR: no histogram in input'
        return -1
    if do_ratio and len(histograms) != 2:
        print 'ERROR: do_ratio option only available when 2 histograms need to be drawn!'
        return -2
    if do_profile and not ('TH2' in histograms[0].ClassName() or 'TH3' in histograms[0].ClassName()):
        print 'ERROR: do_profile option only available with TH2 and TH3 histograms'
        return -3

    # we build the canvas
    return 0


def getLegend(x1=0.7, y1=0.71, x2=0.95, y2=0.85):
    global stuff
    legend = ROOT.TLegend(x1, y1, x2, y2)
    stuff.append(legend)
    legend.SetFillColor(0)
    legend.SetFillStyle(0)
    legend.SetBorderSize(0)
    legend.SetTextSize(0.05)
    return legend


def drawAndProfileX(plot2d, miny=None, maxy=None, do_profile=True, options='', text=None):
    global p_idx
    if miny and maxy:
        plot2d.GetYaxis().SetRangeUser(miny, maxy)
    c = newCanvas()
    c.SetGrid(1, 1)
    c.cd()
    plot2d.Draw(options)
    ROOT.gPad.SetGrid(1, 1)
    ROOT.gStyle.SetGridColor(15)

    if do_profile:
        profname = plot2d.GetName()+'_prof_'+str(p_idx)
        p_idx += 1
        firstbin = 1
        lastbin = -1
        prof = plot2d.ProfileX(profname, firstbin, lastbin, 's')
        prof.SetMarkerColor(2)
        prof.SetLineColor(2)
        prof.Draw('same')

    if text:
        rtext = getText(text, 0.15, 0.85)
        rtext.Draw('same')

    c.Draw()


def getText(text, ndc_x, ndc_y):
    global stuff
    rtext = ROOT.TLatex(ndc_x, ndc_y, text)
    stuff.append(rtext)
    rtext.SetNDC(True)
    # rtext.SetTextFont(40)
    rtext.SetTextSize(0.03)
    return rtext


def drawSame(histograms,
             labels,
             options='',
             norm=False,
             logy=False,
             min_y=None,
             max_y=None,
             text=None,
             y_axis_label=None,
             x_axis_label=None,
             v_lines=None,
             h_lines=None):
    global colors
    global stuff
    c = newCanvas(title=histograms[0].GetName())
    c.cd()
    leg = getLegend()

    max_value = max_y
    min_value = min_y
    if min_y is None:
        min_value = min([hist.GetBinContent(hist.GetMinimumBin()) for hist in histograms])
    if max_y is None:
        max_value = max([hist.GetBinContent(hist.GetMaximumBin()) for hist in histograms])*1.2

    for hidx, hist in enumerate(histograms):
        hist.SetLineColor(colors[hidx])
        hist.SetStats(False)
        if norm:
            hist.DrawNormalized('same'+','+options, 1.)
        else:
            if hidx:
                hist.Draw('same'+','+options)
            else:
                hist.Draw(options)
        leg.AddEntry(histograms[hidx], labels[hidx], 'l')

    histograms[0].GetYaxis().SetRangeUser(min_value, max_value)
    if y_axis_label:
        histograms[0].GetYaxis().SetTitle(y_axis_label)
    if x_axis_label:
            histograms[0].GetXaxis().SetTitle(x_axis_label)

    leg.Draw()
    c.Draw()
    if text:
        rtext = getText(text, 0.15, 0.85)
        rtext.Draw("same")
    if logy:
        c.SetLogy()

    if v_lines:
        for v_line_x in v_lines:
            aline = ROOT.TLine(v_line_x, c.GetUymin(), v_line_x,  c.GetUymax())
            aline.SetLineStyle(2)
            aline.Draw("same")
            stuff.append(aline)
    if h_lines:
        for h_line_y in h_lines:
            aline = ROOT.TLine(c.GetUxmin(), h_line_y, c.GetUxmax(),  h_line_y)
            aline.SetLineStyle(2)
            aline.Draw("same")
            stuff.append(aline)
    c.Update()


def drawProfileX(histograms, labels, options=''):
    profiles = [hist.ProfileX() for hist in histograms]
    drawSame(profiles, labels, options)


def drawSeveral(histograms, labels, options='', do_profile=False, miny=None, maxy=None, text=None):
    ydiv = int(math.ceil(float(len(histograms))/2))
    for hidx in range(0, len(histograms)):
        newtext = labels[hidx]
        if text:
            newtext = '{}: {}'.format(labels[hidx], text)
        if do_profile:
            drawAndProfileX(histograms[hidx], miny=miny, maxy=maxy, options=options, do_profile=do_profile, text=newtext)
        else:
            draw(histograms[hidx], options=options, text=newtext)


def drawProfileRatio(prof1, prof2, ymin=None, ymax=None, text=None):
    hist1 = prof1.ProjectionX(uuid.uuid4().hex[:6])
    hist2 = prof2.ProjectionX(uuid.uuid4().hex[:6])
    hist1.Divide(hist2)
    draw(hist1)
    if text:
        rtext = getText(text, 0.15, 0.85)
        rtext.Draw("same")

    if ymin is not None and ymax is not None:
        hist1.GetYaxis().SetRangeUser(ymin, ymax)
    ROOT.gPad.Update()


# mean+-nsigmas*RMS.
def drawGaussFit(histo, nsigmas, min, max):
    minfit = histo.GetMean() - nsigmas*histo.GetRMS()
    maxfit = histo.GetMean() + nsigmas*histo.GetRMS()
    drawGFit(histo, min, max, minfit, maxfit)


# Fit a histogram in the range (minfit, maxfit) with a gaussian and
# draw it in the range (min, max)
def drawGFit(histo, min, max, minfit, maxfit):
    # static int i = 0
    # i++
    # gPad->SetGrid(1,1);
    # gStyle->SetGridColor(15);
    histo.GetXaxis().SetRangeUser(min, max)
    global f_idx
    nameF1 = "g{}".format(f_idx)
    f_idx +=1
    g1 = ROOT.TF1(nameF1, "gaus", minfit, maxfit)
    g1.SetLineColor(2)
    g1.SetLineWidth(2)
    histo.Fit(g1,"R")


def drawGraphsSame(histograms,
                   labels,
                   options='',
                   norm=False,
                   logy=False,
                   min_y=None,
                   max_y=None,
                   text=None):
    global colors
    c = newCanvas()
    c.cd()
    leg = getLegend()

    for hidx in range(0, len(histograms)):
        histograms[hidx].SetLineColor(colors[hidx])
        histograms[hidx].Draw('same'+','+options)
        leg.AddEntry(histograms[hidx], labels[hidx], 'l')

    max_value = max_y
    min_value = min_y
    if min_y is None:
        min_value = min([hist.GetBinContent(hist.GetMinimumBin()) for hist in histograms])
    if max_y is None:
        max_value = max([hist.GetBinContent(hist.GetMaximumBin()) for hist in histograms])*1.2
    histograms[0].GetYaxis().SetRangeUser(min_value, max_value)
    leg.Draw()
    c.Draw()
    if logy:
        c.SetLogy()
    if text:
        rtext = getText(text, 0.15, 0.85)
        rtext.Draw("same")
    c.Update()
