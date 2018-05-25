import sys

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor, QFont

from orangewidget import gui
from orangewidget.settings import Setting
from orangewidget.widget import OWAction
from oasys.widgets import widget
from oasys.widgets import gui as oasysgui
from oasys.util.oasys_util import EmittingStream

from orangecontrib.wise2.util.wise_util import WisePlot
from orangecontrib.wise2.util.wise_objects import WiseData

from wiselib2.Fundation import PositioningDirectives
import wiselib2.Optics as Optics

from wofry.propagator.propagator import PropagationManager, PropagationMode
from wofrywise2.propagator.propagator1D.wise_propagator import WisePropagator, WISE_APPLICATION

def initialize_propagator_1D():
    PropagationManager.Instance().add_propagator(WisePropagator())
    print("Propagation Manager is initialized")
try:
    initialize_propagator_1D()
except:
    pass

positioning_directives_what = [PositioningDirectives.What.Centre,
                               PositioningDirectives.What.UpstreamFocus,
                               PositioningDirectives.What.DownstreamFocus]

positioning_directives_where = [PositioningDirectives.Where.Centre,
                                PositioningDirectives.Where.UpstreamFocus,
                                PositioningDirectives.Where.DownstreamFocus]

positioning_directives_refer_to = [PositioningDirectives.ReferTo.AbsoluteReference,
                                   PositioningDirectives.ReferTo.UpstreamElement,
                                   PositioningDirectives.ReferTo.DownstreamElement,
                                   PositioningDirectives.ReferTo.DoNotMove,
                                   PositioningDirectives.ReferTo.Source]

positioning_directives_which_angle = [Optics.TypeOfAngle.GrazingNominal,
                                      Optics.TypeOfAngle.InputNominal,
                                      Optics.TypeOfAngle.OutputNominal,
                                      Optics.TypeOfAngle.SelfFrameOfReference,
                                      Optics.TypeOfAngle.NormalAbsolute,
                                      Optics.TypeOfAngle.TangentAbsolute]


class ElementType:
    SOURCE = 0
    MIRROR = 1
    DETECTOR = 10

class WiseWidget(widget.OWWidget):
    author = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi@elettra.eu"

    outputs = [{"name": "WiseData",
                "type": WiseData,
                "doc": ""}]

    IMAGE_WIDTH = 760
    IMAGE_HEIGHT = 545
    MAX_WIDTH = 1320
    MAX_HEIGHT = 700
    CONTROL_AREA_WIDTH = 405
    TABS_AREA_HEIGHT = 560

    is_automatic_run = Setting(False)

    view_type=Setting(1)

    calculated_data = None
    plot_data = None

    want_main_area = 1


    ReferTo = Setting(PositioningDirectives.ReferTo.AbsoluteReference)
    What = Setting(PositioningDirectives.What.Centre)
    Where = Setting(PositioningDirectives.Where.Centre)
    Distance = Setting(0.0)
    XCentre = Setting(0.0)
    YCentre = Setting(0.0)
    GrazingAngle = Setting(0.0)
    Angle = Setting(0.0)
    WhichAngle = Setting(0)

    Distance_checked = Setting(0)
    XYCentre_checked = Setting(0)
    GrazingAngle_checked = Setting(0)
    Angle_checked = Setting(0)

    wise_live_propagation_mode = "Unknown"

    def __init__(self):
        super().__init__()

        self.runaction = OWAction("Compute", self)
        self.runaction.triggered.connect(self.compute)
        self.addAction(self.runaction)

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.MAX_WIDTH)),
                               round(min(geom.height()*0.95, self.MAX_HEIGHT))))

        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        self.general_options_box = gui.widgetBox(self.controlArea, "General Options", addSpace=True, orientation="horizontal")
        gui.checkBox(self.general_options_box, self, 'is_automatic_run', 'Automatic Execution')

        self.button_box = gui.widgetBox(self.controlArea, "", orientation="horizontal")
        #widget buttons: compute, set defaults, help
        gui.button(self.button_box, self, "Compute", callback=self.compute, height=35)
        gui.button(self.button_box, self, "Defaults", callback=self.defaults, height=35)

        gui.separator(self.controlArea, height=10)

        self.build_gui()

        gui.rubber(self.controlArea)

        self.main_tabs = oasysgui.tabWidget(self.mainArea)
        plot_tab = oasysgui.createTabPage(self.main_tabs, "Results")
        out_tab = oasysgui.createTabPage(self.main_tabs, "Output")

        self.view_box = oasysgui.widgetBox(plot_tab, "Results Options", addSpace=False, orientation="horizontal")
        view_box_1 = oasysgui.widgetBox(self.view_box, "", addSpace=False, orientation="vertical", width=350)

        self.view_type_combo = gui.comboBox(view_box_1, self, "view_type", label="View Results",
                                            labelWidth=220,
                                            items=["No", "Yes"],
                                            callback=self.set_ViewType, sendSelectedValue=False, orientation="horizontal")

        oasysgui.widgetBox(self.view_box, "", addSpace=False, orientation="vertical", width=100)


        #* -------------------------------------------------------------------------------------------------------------
        propagation_box = oasysgui.widgetBox(self.view_box, "", addSpace=False, orientation="vertical")

        self.le_wise_live_propagation_mode = gui.lineEdit(propagation_box, self, "wise_live_propagation_mode", "Propagation Mode", labelWidth=150, valueType=str, orientation="horizontal")
        self.le_wise_live_propagation_mode.setAlignment(Qt.AlignCenter)
        self.le_wise_live_propagation_mode.setReadOnly(True)
        font = QFont(self.le_wise_live_propagation_mode.font())
        font.setBold(True)
        self.le_wise_live_propagation_mode.setFont(font)

        self.set_wise_live_propagation_mode()

        #* -------------------------------------------------------------------------------------------------------------

        self.tab = []
        self.tabs = oasysgui.tabWidget(plot_tab)

        self.initializeTabs()

        self.wise_output = QtWidgets.QTextEdit()
        self.wise_output.setReadOnly(True)
        self.wise_output.setStyleSheet("background-color: white;")

        out_box = gui.widgetBox(out_tab, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.wise_output)

        self.wise_output.setFixedHeight(590)
        self.wise_output.setFixedWidth(700)

        gui.rubber(self.mainArea)

    def set_wise_live_propagation_mode(self):
        self.wise_live_propagation_mode = "Element by Element" if PropagationManager.Instance().get_propagation_mode(WISE_APPLICATION) == PropagationMode.STEP_BY_STEP  else \
                                          "Whole beamline at Detector" if PropagationManager.Instance().get_propagation_mode(WISE_APPLICATION) == PropagationMode.WHOLE_BEAMLINE else \
                                          "Unknown"

        palette = QPalette(self.le_wise_live_propagation_mode.palette())

        color = 'dark green' if PropagationManager.Instance().get_propagation_mode(WISE_APPLICATION) == PropagationMode.STEP_BY_STEP  else \
                'dark red' if PropagationManager.Instance().get_propagation_mode(WISE_APPLICATION) == PropagationMode.WHOLE_BEAMLINE else \
                'black'

        palette.setColor(QPalette.Text, QColor(color))
        palette.setColor(QPalette.Base, QColor(243, 240, 140))
        self.le_wise_live_propagation_mode.setPalette(palette)

    def build_gui(self):
        pass


    def build_positioning_directive_box(self, container_box, width, element_type=ElementType.SOURCE):

        box = oasysgui.widgetBox(container_box, "Positioning Directives", orientation="vertical", width=width)

        box_combos = oasysgui.widgetBox(box, "", orientation="vertical", width=width-20)

        box_Distance = oasysgui.widgetBox(box, "", orientation="horizontal", width=width-20)
        box_Distance_check = oasysgui.widgetBox(box_Distance, "", orientation="horizontal", width=20)
        box_Distance_value = oasysgui.widgetBox(box_Distance, "", orientation="horizontal")

        box_XYCentre = oasysgui.widgetBox(box, "", orientation="horizontal", width=width-20)
        box_XYCentre_check = oasysgui.widgetBox(box_XYCentre, "", orientation="horizontal", width=20)
        box_XYCentre_value = oasysgui.widgetBox(box_XYCentre, "", orientation="vertical")

        '''
        box_GrazingAngle = oasysgui.widgetBox(box, "", orientation="horizontal", width=width-20)
        box_GrazingAngle_check = oasysgui.widgetBox(box_GrazingAngle, "", orientation="horizontal", width=20)
        box_GrazingAngle_value = oasysgui.widgetBox(box_GrazingAngle, "", orientation="horizontal")

        box_Angle = oasysgui.widgetBox(box, "", orientation="horizontal", width=width-20)
        box_Angle_check = oasysgui.widgetBox(box_Angle, "", orientation="horizontal", width=20)
        box_Angle_value = oasysgui.widgetBox(box_Angle, "", orientation="horizontal")

        def set_WhichAngle():
            box_GrazingAngle.setVisible(getattr(self, "WhichAngle") == positioning_directives_which_angle[0])
            box_Angle.setVisible(getattr(self, "WhichAngle") != positioning_directives_which_angle[0])
        '''

        def set_Distance_checked():
            box_Distance_value.setEnabled(getattr(self, "Distance_checked") == 1)

        def set_XYCentre_checked():
            box_XYCentre_value.setEnabled(getattr(self, "XYCentre_checked") == 1)

        '''
        def set_GrazingAngle_checked():
            box_GrazingAngle_value.setEnabled(getattr(self, "GrazingAngle_checked") == 1)

        def set_Angle_checked():
            box_Angle_value.setEnabled(getattr(self, "Angle_checked") == 1)
        '''

        def set_positioning_directives():
            pass
            #set_WhichAngle()

        box_what = oasysgui.widgetBox(box_combos, "", orientation="horizontal")
        gui.label(box_what, self, label="  ", labelWidth=20)
        gui.comboBox(box_what, self, "What", label="",
                     items=positioning_directives_what,
                     sendSelectedValue=True, orientation="horizontal", callback=set_positioning_directives)
        gui.label(box_what, self, label=" of this O.E.", labelWidth=80)

        box_where = oasysgui.widgetBox(box_combos, "", orientation="horizontal")
        gui.label(box_where, self, label="at", labelWidth=20)
        gui.comboBox(box_where, self, "Where", label="",
                     items=positioning_directives_where,
                     sendSelectedValue=True, orientation="horizontal", callback=set_positioning_directives)
        gui.label(box_where, self, label=" of", labelWidth=80)

        box_refer_to = oasysgui.widgetBox(box_combos, "", orientation="horizontal")
        gui.label(box_refer_to, self, label=" ", labelWidth=20)
        gui.comboBox(box_refer_to, self, "ReferTo", label="",
                     items=positioning_directives_refer_to,
                     sendSelectedValue=True, orientation="horizontal", callback=set_positioning_directives)
        gui.label(box_refer_to, self, label=" O.E.", labelWidth=80)

        '''
        gui.comboBox(box_combos, self, "WhichAngle", label="Type Of Angle",
                     items=positioning_directives_which_angle, labelWidth=box_combos.width()-150,
                     sendSelectedValue=True, orientation="horizontal", callback=set_WhichAngle)
        '''

        gui.separator(box_combos)

        gui.checkBox(box_Distance_check, self, "Distance_checked", "", callback=set_Distance_checked)
        gui.checkBox(box_XYCentre_check, self, "XYCentre_checked", "", callback=set_XYCentre_checked)
        '''
        gui.checkBox(box_GrazingAngle_check, self, "GrazingAngle_checked", "", callback=set_GrazingAngle_checked)
        gui.checkBox(box_Angle_check, self, "Angle_checked", "", callback=set_Angle_checked)
        '''

        set_Distance_checked()
        set_XYCentre_checked()
        '''
        set_Angle_checked()
        set_GrazingAngle_checked()
        '''

        self.le_Distance = oasysgui.lineEdit(box_Distance_value, self, "Distance", "Distance", labelWidth=200, valueType=float, orientation="horizontal")
        self.le_XCentre = oasysgui.lineEdit(box_XYCentre_value, self, "XCentre", "X Centre", labelWidth=200, valueType=float, orientation="horizontal")
        self.le_YCentre = oasysgui.lineEdit(box_XYCentre_value, self, "YCentre", "Y Centre", labelWidth=200, valueType=float, orientation="horizontal")

        '''
        oasysgui.lineEdit(box_Angle_value, self, "Angle", "Angle [deg]", labelWidth=200, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_GrazingAngle_value, self, "GrazingAngle", "Grazing Angle [deg]", labelWidth=200, valueType=float, orientation="horizontal")
        '''
        set_positioning_directives()

    def get_PositionDirectives(self):
        return PositioningDirectives(PlaceWhat=self.What,
                                     PlaceWhere=self.Where,
                                     ReferTo=self.ReferTo,
                                     XYCentre=None if self.XYCentre_checked == 0 else [self.XCentre*self.workspace_units_to_m, self.YCentre*self.workspace_units_to_m],
                                     Distance=None if self.Distance_checked == 0 else self.Distance*self.workspace_units_to_m) #,
                                     #WhichAngle=self.WhichAngle,
                                     #GrazingAngle=None if self.GrazingAngle_checked == 0 else numpy.deg2rad(self.GrazingAngle),
                                     #Angle = None if self.Angle_checked == 0 else numpy.deg2rad(0))


    def after_change_workspace_units(self):
        if hasattr(self, "le_Distance"):
            label = self.le_Distance.parent().layout().itemAt(0).widget()
            label.setText(label.text() + " [" + self.workspace_units_label + "]")
        if hasattr(self, "le_XCentre"):
            label = self.le_XCentre.parent().layout().itemAt(0).widget()
            label.setText(label.text() + " [" + self.workspace_units_label + "]")
        if hasattr(self, "le_YCentre"):
            label = self.le_YCentre.parent().layout().itemAt(0).widget()
            label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def initializeTabs(self):
        size = len(self.tab)
        indexes = range(0, size)

        for index in indexes:
            self.tabs.removeTab(size-1-index)

        titles = self.getTabTitles()

        self.tab = []
        self.plot_canvas = []

        for index in range(0, len(titles)):
            self.tab.append(gui.createTabPage(self.tabs, titles[index]))
            self.plot_canvas.append(None)

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

    def getTabTitles(self):
        return ["Calculation Result"]

    def getTitles(self):
        return ["Calculation Result"]

    def getXTitles(self):
        return ["Energy [eV]"]

    def getYTitles(self):
        return ["X [$\mu$m]"]

    def getVariablesToPlot(self):
        return [(0, 1)]

    def getLogPlot(self):
        return [(False, False)]

    def set_ViewType(self):
        self.progressBarInit()

        if not self.plot_data is None:
            try:
                self.initializeTabs()

                self.plot_results(self.plot_data)
            except Exception as exception:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           str(exception),
                    QtWidgets.QMessageBox.Ok)

        self.progressBarFinished()

    def plot_results(self, plot_data, progressBarValue=80):
        if not self.view_type == 0:
            if not plot_data is None:
                self.view_type_combo.setEnabled(False)

                titles = self.getTitles()
                xtitles = self.getXTitles()
                ytitles = self.getYTitles()

                progress_bar_step = (100-progressBarValue)/len(titles)

                for index in range(0, len(titles)):
                    x_index, y_index = self.getVariablesToPlot()[index]
                    log_x, log_y = self.getLogPlot()[index]

                    try:
                        self.plot_histo(plot_data[x_index, :],
                                        plot_data[y_index, :],
                                        progressBarValue + ((index+1)*progress_bar_step),
                                        tabs_canvas_index=index,
                                        plot_canvas_index=index,
                                        title=titles[index],
                                        xtitle=xtitles[index],
                                        ytitle=ytitles[index],
                                        log_x=log_x,
                                        log_y=log_y)
                    except Exception as e:
                        self.view_type_combo.setEnabled(True)

                        raise Exception("Data not plottable: bad content\n" + str(e))

                self.tabs.setCurrentIndex(0)
                self.view_type_combo.setEnabled(True)
            else:
                raise Exception("Empty Data")

    def writeStdOut(self, text):
        cursor = self.wise_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.wise_output.setTextCursor(cursor)
        self.wise_output.ensureCursorVisible()

    def plot_histo(self, x, y, progressBarValue, tabs_canvas_index, plot_canvas_index, title="", xtitle="", ytitle="", log_x=False, log_y=False):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = oasysgui.plotWindow(roi=False, control=True, position=True)
            self.plot_canvas[plot_canvas_index].setDefaultPlotLines(True)
            self.plot_canvas[plot_canvas_index].setActiveCurveColor(color='blue')
            self.plot_canvas[plot_canvas_index].setXAxisLogarithmic(log_x)
            self.plot_canvas[plot_canvas_index].setYAxisLogarithmic(log_y)

            self.tab[tabs_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        WisePlot.plot_histo(self.plot_canvas[plot_canvas_index], x, y, title, xtitle, ytitle)

        self.progressBarSet(progressBarValue)


    def compute(self):
        self.setStatusMessage("Running WISEr")

        self.progressBarInit()

        try:
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.progressBarSet(20)

            self.check_fields()

            calculation_output = self.do_wise_calculation()

            self.progressBarSet(50)

            if calculation_output is None:
                raise Exception("Wise gave no result")
            else:
                self.setStatusMessage("Plotting Results")

                self.plot_data = self.extract_plot_data_from_calculation_output(calculation_output)

                self.plot_results(self.plot_data, progressBarValue=60)

                self.setStatusMessage("")

                wise_data = self.extract_wise_data_from_calculation_output(calculation_output)
                if not wise_data is None: self.send("WiseData", wise_data)

        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       str(exception), QtWidgets.QMessageBox.Ok)

            self.setStatusMessage("Error!")

            #raise exception

        self.progressBarFinished()


    def defaults(self):
         self.resetSettings()

    def check_fields(self):
        raise Exception("This method should be reimplementd in subclasses!")

    def do_wise_calculation(self):
        raise Exception("This method should be reimplementd in subclasses!")

    def extract_plot_data_from_calculation_output(self, calculation_output):
        raise Exception("This method should be reimplementd in subclasses!")

    def extract_wise_data_from_calculation_output(self, calculation_output):
        return calculation_output

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = WiseWidget()
    ow.show()
    a.exec_()
    ow.saveSettings()
