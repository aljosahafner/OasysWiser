import sys
import numpy
from scipy.stats import norm
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from wiselib2 import Optics
import wiselib2.FermiSource as Fermi

from wofrywise2.propagator.propagator1D.wise_propagator import WisePropagationElements

from wofrywise2.beamline.wise_beamline_element import WiseBeamlineElement
from wofrywise2.beamline.light_sources.wise_gaussian_source import WiseGaussianSource

from orangecontrib.wise2.util.wise_objects import WiseData
from orangecontrib.wise2.widgets.gui.ow_wise_widget import WiseWidget, ElementType

class OWGaussianSource1d(WiseWidget):
    name = "GaussianSource1d"
    id = "GaussianSource1d"
    description = "GaussianSource1d"
    icon = "icons/gaussian_source_1d.png"
    priority = 1
    category = ""
    keywords = ["wise", "gaussian"]

    source_name = Setting("Gaussian Source")

    source_lambda = Setting(10)
   
    waist_calculation = Setting(0)
    source_waist =  Setting(125e-3)
    

    def build_gui(self):

        main_box = oasysgui.widgetBox(self.controlArea, "Gaussian Source 1D Input Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)

        source_box = oasysgui.widgetBox(main_box, "Source Setting", orientation="vertical", width=self.CONTROL_AREA_WIDTH-25)

        oasysgui.lineEdit(source_box, self, "source_name", "Source Name", labelWidth=120, valueType=str, orientation="horizontal")

        oasysgui.lineEdit(source_box, self, "source_lambda", "Wavelength [nm]", labelWidth=260, valueType=float, orientation="horizontal", callback=self.set_WaistCalculation)

        gui.comboBox(source_box, self, "waist_calculation", label="Waist Data",
                     items=["User", "Fermi FEL1", "Fermi FEL2", "Fermi Auto"], labelWidth=260,
                     callback=self.set_WaistCalculation, sendSelectedValue=False, orientation="horizontal")

        self.le_source_waist = oasysgui.lineEdit(source_box, self, "source_waist", "Waist", labelWidth=260, valueType=float, orientation="horizontal")

        super(OWGaussianSource1d, self).build_positioning_directive_box(container_box=main_box,
                                                                        width=self.CONTROL_AREA_WIDTH-25,
                                                                        element_type=ElementType.SOURCE)

    def set_WaistCalculation(self):
        if self.source_lambda > 0.0:
            self.source_waist = round(Fermi.Waist0E(self.source_lambda, str( self.waist_calculation))/self.workspace_units_to_m, 8)

    def after_change_workspace_units(self):
        super(OWGaussianSource1d, self).after_change_workspace_units()

        label = self.le_source_waist.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def check_fields(self):
        self.source_lambda = congruence.checkStrictlyPositiveNumber(self.source_lambda, "Wavelength")
        self.source_waist = congruence.checkStrictlyPositiveNumber(self.source_waist, "Waist")

    def do_wise_calculation(self):
        position_directives = self.get_PositionDirectives()
        position_directives.WhichAngle = Optics.TypeOfAngle.SelfFrameOfReference
        position_directives.Angle = 0.0

        wise_source = WiseGaussianSource(name=self.source_name,
                                         source_gaussian=Optics.SourceGaussian(self.source_lambda*1e-9,
                                                                               self.source_waist*self.workspace_units_to_m) ,
                                         position_directives=position_directives)

        data_to_plot = numpy.zeros((2, 100))

        sigma = self.source_waist/2
        mu = 0.0 if self.XYCentre_checked else self.YCentre

        data_to_plot[0, :] = numpy.linspace((-5*sigma) + mu, mu + (5*sigma), 100)
        data_to_plot[1, :] = (norm.pdf(data_to_plot[0, :], mu, sigma))**2

        return wise_source, data_to_plot

    def getTitles(self):
        return ["Gaussian Source Intensity"]

    def getXTitles(self):
        return ["Y [" + self.workspace_units_label + "]"]

    def getYTitles(self):
        return ["Intensity [arbitrary units]"]

    def extract_plot_data_from_calculation_output(self, calculation_output):
        return calculation_output[1]

    def extract_wise_data_from_calculation_output(self, calculation_output):
        beamline = WisePropagationElements()
        beamline.add_beamline_element(WiseBeamlineElement(optical_element=calculation_output[0]))

        return WiseData(wise_wavefront=None, wise_beamline=beamline)

