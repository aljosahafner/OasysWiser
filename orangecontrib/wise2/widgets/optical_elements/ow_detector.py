import sys, numpy

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QSlider
from PyQt5.QtCore import QRect, Qt

from orangewidget import gui
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream
from orangewidget.settings import Setting

from syned.widget.widget_decorator import WidgetDecorator

from wiselib2 import Fundation, Optics

from wofrywise2.beamline.optical_elements.wise_detector import WiseDetector

from orangecontrib.wise2.widgets.gui.ow_optical_element import OWOpticalElement

class OWDetector(OWOpticalElement, WidgetDecorator):
    name = "Detector"
    id = "Detector"
    description = "Detector"
    icon = "icons/screen.png"
    priority = 10

    has_figure_error_box = False
    is_full_propagator = True
    run_calculation = False

    defocus_sweep = Setting(0.0)
    defocus_start = Setting(-1.0)
    defocus_stop = Setting(1.0)
    defocus_step = Setting(0.1)
    show_animation = Setting(0)

    output_data_best_focus = None

    _defocus_sign = 1

    def after_change_workspace_units(self):
        super(OWDetector, self).after_change_workspace_units()

        label = self.le_defocus_start.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_defocus_stop.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_defocus_step.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")


    def check_fields(self):
        super(OWDetector, self).check_fields()

    def build_mirror_specific_gui(self, container_box):
        self.tab_best = oasysgui.createTabPage(self.tabs_setting, "Best Focus Calculation")

        best_focus_box = oasysgui.widgetBox(self.tab_best, "", orientation="vertical", width=self.CONTROL_AREA_WIDTH-20)

        self.le_defocus_start = oasysgui.lineEdit(best_focus_box, self, "defocus_start", "Defocus sweep start", labelWidth=240, valueType=float, orientation="horizontal")
        self.le_defocus_stop  = oasysgui.lineEdit(best_focus_box, self, "defocus_stop",  "Defocus sweep stop", labelWidth=240, valueType=float, orientation="horizontal")
        self.le_defocus_step  = oasysgui.lineEdit(best_focus_box, self, "defocus_step",  "Defocus sweep step", labelWidth=240, valueType=float, orientation="horizontal")

        gui.separator(best_focus_box, height=5)

        gui.checkBox(best_focus_box, self, "show_animation", "Show animation during calculation")

        gui.separator(best_focus_box, height=5)

        button_box = oasysgui.widgetBox(best_focus_box, "", orientation="horizontal", width=self.CONTROL_AREA_WIDTH-20)

        gui.button(button_box, self, "Find Best Focus Position", callback=self.do_best_focus_calculation, height=35)
        stop_button = gui.button(button_box, self, "Interrupt", callback=self.stop_best_focus_calculation, height=35)
        font = QFont(stop_button.font())
        font.setBold(True)
        stop_button.setFont(font)
        palette = QPalette(stop_button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('red'))
        stop_button.setPalette(palette) # assign new palette

        self.save_button = gui.button(best_focus_box, self, "Save Best Focus Calculation Complete Results", callback=self.save_best_focus_results, height=35)
        self.save_button.setEnabled(False)

        self.best_focus_slider = None

    def initializeTabs(self):
        super(OWDetector, self).initializeTabs()

        self.tab.append(gui.createTabPage(self.tabs, "Field Intensity (Best Focus)"))
        self.tab.append(gui.createTabPage(self.tabs, "HEW"))
        self.plot_canvas.append(None)
        self.plot_canvas.append(None)

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

    def get_inner_wise_optical_element(self):
        return Optics.Detector(L=self.length*self.workspace_units_to_m,
                               AngleGrazing = numpy.deg2rad(self.alpha))

    def get_optical_element(self, inner_wise_optical_element):
         return WiseDetector(name= self.oe_name,
                             detector=inner_wise_optical_element,
                             position_directives=self.get_PositionDirectives())


    def receive_specific_syned_data(self, optical_element):
        pass

    def check_syned_shape(self, optical_element):
        pass

    def getTabTitles(self):
        return ["Field Intensity (O.E. Focus)", "Phase (O.E. Focus)"]

    def getTitles(self):
        return ["Field Intensity (O.E. Focus)", "Phase (O.E. Focus)"]

    def getXTitles(self):
        return ["S [" + self.workspace_units_label + "]", "S [" + self.workspace_units_label + "]"]

    def getYTitles(self):
        return ["|E0|**2", "Phase"]

    def getVariablesToPlot(self):
        return [(0, 1), (0, 2)]

    def getLogPlot(self):
        return [(False, False), (False, False)]

    def stop_best_focus_calculation(self):
        self.run_calculation = False

    def do_wise_calculation(self):
        self.output_data_best_focus = super(OWDetector, self).do_wise_calculation()

        return self.output_data_best_focus

    def do_best_focus_calculation(self):
        try:
            if self.input_data is None:
                raise Exception("No Input Data!")

            if not self.output_data_best_focus:
                raise Exception("Run computation first!")

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            # TODO: TO BE CHECKED THE EQUiVALENT OF THE OLD QUANTITY!!!!
            self.oe_f2 = self.output_data_best_focus.wise_beamline.get_wise_propagation_element(-1).PositioningDirectives.Distance

            self.check_fields()
            if self.defocus_start >= self.defocus_stop: raise Exception("Defocus sweep start must be < Defocus sweep stop")
            self.defocus_step = congruence.checkStrictlyPositiveNumber(self. defocus_step, "Defocus sweep step")
            if self.defocus_step >= self.defocus_stop - self.defocus_start: raise Exception("Defocus step is too big")

            if self.best_focus_slider is None:
                self.best_focus_slider = QSlider(self.tab[1])
                self.best_focus_slider.setGeometry(QRect(0, 0, 320, 50))
                self.best_focus_slider.setMinimumHeight(30)
                self.best_focus_slider.setOrientation(Qt.Horizontal)
                self.best_focus_slider.setInvertedAppearance(False)
                self.best_focus_slider.setInvertedControls(False)

                self.tab[2].layout().addWidget(self.best_focus_slider)
            else:
                self.best_focus_slider.valueChanged.disconnect()

            self.setStatusMessage("")
            self.progressBarInit()

            self.defocus_list = numpy.arange(self.defocus_start * self.workspace_units_to_m,
                                             self.defocus_stop  * self.workspace_units_to_m,
                                             self.defocus_step  * self.workspace_units_to_m)

            n_defocus = len(self.defocus_list)

            if self.defocus_list[-1] != self.defocus_stop  * self.workspace_units_to_m:
                n_defocus += 1
                self.defocus_list.resize(n_defocus)
                self.defocus_list[-1] = self.defocus_stop  * self.workspace_units_to_m

            self.best_focus_slider.setTickInterval(1)
            self.best_focus_slider.setSingleStep(1)
            self.best_focus_slider.setMinimum(0)
            self.best_focus_slider.setMaximum(n_defocus-1)
            self.best_focus_slider.setValue(0)

            progress_bar_increment = 100/n_defocus

            n_pools = self.n_pools if self.use_multipool == 1 else 1

            hew_min = numpy.inf
            index_min_list = []

            self.best_focus_index = -1
            self.electric_fields_list = []
            self.positions_list = []
            self.hews_list = []

            import copy
            last_element = self.get_last_element()
            last_element = copy.deepcopy(last_element)

            self.setStatusMessage("Calculating Best Focus Position")

            self.run_calculation = True

            self.defocus_list[numpy.where(numpy.abs(self.defocus_list) < 1e-15)] = 0.0

            if self.show_animation == 1:
                for i, defocus in enumerate(self.defocus_list):
                    if not self.run_calculation:
                        if not self.best_focus_slider is None: self.best_focus_slider.valueChanged.connect(self.plot_detail)
                        return

                    ResultList, HewList, SigmaList, More = Fundation.FocusSweep(last_element, [self.defocus_list[i]],
                                                                               DetectorSize = self.length*self.workspace_units_to_m,
                                                                               NPools = n_pools)

                    S = ResultList[0].S
                    E = ResultList[0].Field
                    I = abs(E)**2
                    norm = max(I)
                    norm = 1.0 if norm == 0.0 else norm
                    I = I/norm
                    HEW = HewList[0]

                    # E1
                    self.electric_fields_list.append(E)
                    self.positions_list.append(S)
                    self.hews_list.append(HEW)

                    self.best_focus_slider.setValue(i)

                    self.plot_histo(S * 1e6,
                                    I,
                                    i*progress_bar_increment,
                                    tabs_canvas_index=2,
                                    plot_canvas_index=2,
                                    title="Defocus Sweep: " + str(self._defocus_sign * defocus/self.workspace_units_to_m) + " (" + str(i+1) + "/" + str(n_defocus) +
                                          "), HEW: " + str(round(HEW*1e6, 4)) + " [$\mu$m]",
                                    xtitle="Y [$\mu$m]",
                                    ytitle="Intensity",
                                    log_x=False,
                                    log_y=False)

                    self.tabs.setCurrentIndex(2)

                    hew = round(HEW*1e6, 11) # problems with double precision numbers: inconsistent comparisons

                    if hew < hew_min:
                        hew_min = hew
                        index_min_list = [i]
                    elif hew == hew_min:
                        index_min_list.append(i)
            else: # NOT INTERACTIVE
                ResultList, HewList, SigmaList, More = Fundation.FocusSweep(last_element,
                                                                            self.defocus_list,
                                                                            DetectorSize = self.length*self.workspace_units_to_m,
                                                                            NPools = n_pools)

                i=0
                for Result, HEW in zip(ResultList, HewList):
                    self.electric_fields_list.append(Result.Field)
                    self.positions_list.append(Result.S)
                    self.hews_list.append(HEW)

                    hew = round(HEW*1e6, 11) # problems with double precision numbers: inconsistent comparisons

                    if hew < hew_min:
                        hew_min = hew
                        index_min_list = [i]
                    elif hew == hew_min:
                        index_min_list.append(i)

                    i += 1

            index_min = index_min_list[int(len(index_min_list)/2)] # choosing the central value, when hew reach a pletau

            self.best_focus_index = index_min
            best_focus_electric_fields = self.electric_fields_list[index_min]
            best_focus_I = abs(best_focus_electric_fields)**2
            norm = max(best_focus_I)
            norm = 1.0 if norm == 0.0 else norm
            best_focus_I = best_focus_I/norm

            best_focus_positions       = self.positions_list[index_min]

            QMessageBox.information(self,
                                    "Best Focus Calculation",
                                    "Best Focus Found!\n\nPosition: " + str(self.oe_f2 + (self._defocus_sign * self.defocus_list[index_min]/self.workspace_units_to_m)) +
                                    "\nHEW: " + str(round(self.hews_list[index_min]*1e6, 4)) + " [" + u"\u03BC" + "m]",
                                    QMessageBox.Ok
                                    )

            self.plot_histo(best_focus_positions * 1e6,
                            best_focus_I,
                            100,
                            tabs_canvas_index=2,
                            plot_canvas_index=2,
                            title="(BEST FOCUS) Defocus Sweep: " + str(self._defocus_sign * self.defocus_list[index_min]/self.workspace_units_to_m) +
                                  " ("+ str(index_min+1) + "/" + str(n_defocus) + "), Position: " +
                                  str(self.oe_f2 + (self._defocus_sign * self.defocus_list[index_min]/self.workspace_units_to_m)) +
                                  ", HEW: " + str(round(self.hews_list[index_min]*1e6, 4)) + " [$\mu$m]",
                            xtitle="Y [$\mu$m]",
                            ytitle="Intensity",
                            log_x=False,
                            log_y=False)

            self.plot_histo(self._defocus_sign * self.defocus_list,
                            numpy.multiply(self.hews_list, 1e6),
                            100,
                            tabs_canvas_index=3,
                            plot_canvas_index=3,
                            title="HEW vs Defocus Sweep",
                            xtitle="",
                            ytitle="",
                            log_x=False,
                            log_y=False)

            self.plot_canvas[3].setDefaultPlotLines(True)
            self.plot_canvas[3].setDefaultPlotPoints(True)
            self.plot_canvas[3].setGraphXLabel("Defocus [" + self.workspace_units_label + "]")
            self.plot_canvas[3].setGraphYLabel("HEW [$\mu$m]")

            self.best_focus_slider.setValue(index_min)

            self.tabs.setCurrentIndex(3 if self.show_animation == 1 else 2)
            self.setStatusMessage("")

            self.save_button.setEnabled(True)

        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            self.setStatusMessage("Error!")

            #raise exception

        if not self.best_focus_slider is None: self.best_focus_slider.valueChanged.connect(self.plot_detail)
        self.progressBarFinished()

    def get_last_element(self):
        last_element = self.output_data_best_focus.wise_beamline.get_wise_propagation_element(-1)

        if isinstance(last_element.CoreOptics, Optics.Detector):
            return last_element.Parent
        else:
            return last_element

    def plot_detail(self, value):
        try:
            index = value
            n_defocus = len(self.positions_list)

            electric_fields = self.electric_fields_list[index]
            I = abs(electric_fields)**2
            norm = max(I)
            norm = 1.0 if norm == 0.0 else norm
            I = I/norm
            positions       = self.positions_list[index]

            if index == self.best_focus_index:
                title = "(BEST FOCUS) Defocus Sweep: " + str(self._defocus_sign * self.defocus_list[index]/self.workspace_units_to_m) + \
                        " ("+ str(index+1) + "/" + str(n_defocus) + "), Position: " + \
                        str(self.oe_f2 + (self.defocus_list[index]/self.workspace_units_to_m)) + \
                        ", HEW: " + str(round(self.hews_list[index]*1e6, 4)) + " [$\mu$m]"
            else:
                title = "Defocus Sweep: " + str(self._defocus_sign * self.defocus_list[index]/self.workspace_units_to_m) + \
                        " (" + str(index+1) + "/" + str(n_defocus) + "), HEW: " + str(round(self.hews_list[index]*1e6, 4)) + " [$\mu$m]"

            self.plot_histo(positions * 1e6,
                            I,
                            100,
                            tabs_canvas_index=1,
                            plot_canvas_index=1,
                            title=title,
                            xtitle="Y [$\mu$m]",
                            ytitle="Intensity",
                            log_x=False,
                            log_y=False)

            self.tabs.setCurrentIndex(2)
        except:
            pass

    def save_best_focus_results(self):
        try:
            path_dir = QFileDialog.getExistingDirectory(self, "Select destination directory", ".", QFileDialog.ShowDirsOnly)

            if not path_dir is None:
                if not path_dir.strip() == "":
                    if QMessageBox.question(self,
                                            "Save Data",
                                            "Data will be saved in :\n\n" + path_dir + "\n\nConfirm?",
                                            QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                        for index in range(0, len(self.electric_fields_list)):
                            file_name = "best_focus_partial_result_" + str(index) + ".dat"

                            file = open(path_dir + "/" + file_name, "w")

                            intensities = abs(self.electric_fields_list[index])**2
                            norm = max(intensities)
                            norm = 1.0 if norm == 0.0 else norm
                            intensities = intensities/norm

                            file.write("# Defocus Sweep: " + str(self.defocus_list[index]) + " [m]\n")
                            file.write("# HEW          : " + str(self.hews_list[index]) + " [m]\n")
                            file.write("# Position [m]  Intensity\n")

                            for i in range (0, len(self.positions_list[index])):
                                file.write(str(self.positions_list[index][i]) + " " + str(intensities[i]) + "\n")


                            file.close()

                        QMessageBox.information(self,
                                                "Best Focus Calculation",
                                                "Best Focus Calculation complete results saved on directory:\n\n" + path_dir,
                                                QMessageBox.Ok
                                                )

        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            self.setStatusMessage("Error!")
