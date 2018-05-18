import numpy

from PyQt5.QtGui import QPalette, QColor, QFont

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from orangecontrib.wise2.util.wise_objects import WiseData
from orangecontrib.wise2.widgets.gui.ow_wise_widget import WiseWidget

from wofry.propagator.propagator import PropagationElements
from wofry.propagator.wavefront1D.generic_wavefront import GenericWavefront1D

from wofrywise2.propagator.wavefront1D.wise_wavefront import WiseWavefront

class OWFromWofryWavefront1d(WiseWidget):
    name = "From Wofry Wavefront 1D"
    id = "FromWofryWavefront1d"
    description = "From Wofry Wavefront 1D"
    icon = "icons/from_wofry_wavefront_1d.png"
    priority = 1
    category = ""
    keywords = ["wise", "gaussian"]

    inputs = [("GenericWavefront1D", GenericWavefront1D, "set_input")]

    wofry_wavefront = None
    reset_phase = Setting(0)
    normalization_factor = Setting(1.0)

    source_lambda = 0.0

    def build_gui(self):

        main_box = oasysgui.widgetBox(self.controlArea, "Wofry Wavefront Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5, height=300)

        le = oasysgui.lineEdit(main_box, self, "source_lambda", "Wavelength [nm]", labelWidth=260, valueType=float, orientation="horizontal")
        le.setReadOnly(True)
        font = QFont(le.font())
        font.setBold(True)
        le.setFont(font)
        palette = QPalette(le.palette())
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 140))
        le.setPalette(palette)

        gui.separator(main_box, height=5)

        gui.comboBox(main_box, self, "reset_phase", label="Reset Phase",
                                            items=["No", "Yes"], labelWidth=300, sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(main_box, self, "normalization_factor", "Normalization Factor", labelWidth=260, valueType=float, orientation="horizontal")

    def check_fields(self):
        self.source_lambda = congruence.checkStrictlyPositiveNumber(self.source_lambda, "Wavelength")

    def do_wise_calculation(self):
        rinorm = numpy.sqrt(self.normalization_factor/numpy.max(self.wofry_wavefront.get_intensity()))

        if self.reset_phase:
            electric_fields = self.wofry_wavefront.get_amplitude()*rinorm + 0j
        else:
            electric_fields = self.wofry_wavefront.get_amplitude()*rinorm + self.wofry_wavefront.get_phase()

        self.wofry_wavefront.set_complex_amplitude(electric_fields)

        data_to_plot = numpy.zeros((2, self.wofry_wavefront.size()))

        data_to_plot[0, :] = self.wofry_wavefront._electric_field_array.get_abscissas()/self.workspace_units_to_m
        data_to_plot[1, :] = numpy.abs(self.wofry_wavefront._electric_field_array.get_values())**2

        return WiseWavefront.fromGenericWavefront(self.wofry_wavefront), data_to_plot

    def getTitles(self):
        return ["Wavefront Intensity"]

    def getXTitles(self):
        return ["Z [" + self.workspace_units_label + "]"]

    def getYTitles(self):
        return ["Intensity [arbitrary units]"]

    def extract_plot_data_from_calculation_output(self, calculation_output):
        return calculation_output[1]

    def extract_wise_data_from_calculation_output(self, calculation_output):
        return WiseData(wise_wavefront=calculation_output[0], wise_beamline=PropagationElements())

    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            self.wofry_wavefront = input_data.duplicate()
            self.source_lambda = round(self.wofry_wavefront._wavelength*1e9, 4)

            if self.is_automatic_run: self.compute()
