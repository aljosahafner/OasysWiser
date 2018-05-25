import numpy
import multiprocessing

from PyQt5.QtWidgets import QApplication, QMessageBox, QInputDialog
from PyQt5.QtGui import QPalette, QColor, QFont
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from syned.widget.widget_decorator import WidgetDecorator
from syned.beamline.optical_elements.mirrors.mirror import Mirror

from wofry.propagator.propagator import PropagationManager, PropagationParameters, PropagationMode

from wofrywise2.propagator.propagator1D.wise_propagator import WisePropagator, WisePropagationElements, WISE_APPLICATION
from wofrywise2.propagator.wavefront1D.wise_wavefront import WiseWavefront
from wofrywise2.beamline.wise_beamline_element import WiseBeamlineElement

from orangecontrib.wise2.util.wise_objects import WiseData, WisePreInputData
from orangecontrib.wise2.widgets.gui.ow_wise_widget import WiseWidget, ElementType

class OWOpticalElement(WiseWidget, WidgetDecorator):
    category = ""
    keywords = ["wise", "mirror"]

    inputs = [("Input", WiseData, "set_input"), ("PreInput", WisePreInputData, "set_pre_input")]

    WidgetDecorator.append_syned_input_data(inputs)

    oe_name = Setting("Optical Element")

    alpha = Setting(2.0)
    length = Setting(400.0)
    ignore = Setting(False)

    use_small_displacements = Setting(0)
    rotation = Setting(0.0)
    transverse = Setting(0.0)
    longitudinal = Setting(0.0)

    use_figure_error = Setting(0)
    figure_error_file = Setting("figure_error.dat")
    figure_error_step = Setting(0.002)
    figure_error_amplitude_scaling = Setting(1.0)
    figure_error_um_conversion = Setting(1.0)

    use_roughness = Setting(0)
    roughness_file = Setting("roughness.dat")
    roughness_x_scaling = Setting(1.0)
    roughness_y_scaling = Setting(1.0)
    roughness_fit_data = Setting(0)

    use_multipool = Setting(0)
    n_pools = Setting(5)
    number_of_cpus = multiprocessing.cpu_count() - 1
    force_cpus = Setting(1)

    calculation_type = Setting(0)
    number_of_points = Setting(7000)

    input_data = None

    has_figure_error_box = True
    is_full_propagator   = False

    def build_gui(self):
        self.tabs_setting = oasysgui.tabWidget(self.controlArea)
        self.tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.tab_bas = oasysgui.createTabPage(self.tabs_setting, "O.E. Setting")
        self.tab_pro = oasysgui.createTabPage(self.tabs_setting, "Calculation Setting")

        main_box = oasysgui.widgetBox(self.tab_bas, "O.E. Input Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-20)

        oasysgui.lineEdit(main_box, self, "oe_name", "O.E. Name", labelWidth=120, valueType=str, orientation="horizontal")

        oasysgui.lineEdit(main_box, self, "alpha", "Incidence Angle [deg]", labelWidth=240, valueType=float, orientation="horizontal")
        self.le_length = oasysgui.lineEdit(main_box, self, "length", "Length", labelWidth=240, valueType=float, orientation="horizontal")


        self.build_mirror_specific_gui(main_box)

        gui.comboBox(main_box, self, "ignore", label="Ignore", items=["No", "Yes"], labelWidth=240, sendSelectedValue=False, orientation="horizontal")

        gui.separator(main_box)

        self.tabs_mirror = oasysgui.tabWidget(main_box)
        self.tabs_mirror.setFixedWidth(self.CONTROL_AREA_WIDTH-40)


        self.tab_pos = oasysgui.createTabPage(self.tabs_mirror, "Position")
        if self.has_figure_error_box: self.tab_err = oasysgui.createTabPage(self.tabs_mirror, "Figure Error")
        self.tab_dis = oasysgui.createTabPage(self.tabs_mirror, "Displacement")

        super(OWOpticalElement, self).build_positioning_directive_box(container_box=self.tab_pos,
                                                                      width=self.CONTROL_AREA_WIDTH-50,
                                                                      element_type=ElementType.MIRROR)

        displacement_box = oasysgui.widgetBox(self.tab_dis, "Small Displacements", orientation="vertical", width=self.CONTROL_AREA_WIDTH-50)

        gui.comboBox(displacement_box, self, "use_small_displacements", label="Small Displacements",
                     items=["No", "Yes"], labelWidth=240,
                     callback=self.set_UseSmallDisplacement, sendSelectedValue=False, orientation="horizontal")

        self.use_small_displacements_box       = oasysgui.widgetBox(displacement_box, "", addSpace=True, orientation="vertical", height=150, width=self.CONTROL_AREA_WIDTH-65)
        self.use_small_displacements_box_empty = oasysgui.widgetBox(displacement_box, "", addSpace=True, orientation="vertical", height=150, width=self.CONTROL_AREA_WIDTH-65)

        oasysgui.lineEdit(self.use_small_displacements_box, self, "rotation", "Rotation [deg]", labelWidth=240, valueType=float, orientation="horizontal")
        self.le_transverse = oasysgui.lineEdit(self.use_small_displacements_box, self, "transverse", "Transverse displacement", labelWidth=240, valueType=float, orientation="horizontal")
        self.le_longitudinal = oasysgui.lineEdit(self.use_small_displacements_box, self, "longitudinal", "Longitudinal displacement", labelWidth=240, valueType=float, orientation="horizontal")

        self.set_UseSmallDisplacement()

        # ---------------------------------------------------------------------------
        if self.has_figure_error_box:
            figure_error_tab = oasysgui.tabWidget(self.tab_err)
            error_tab = oasysgui.createTabPage(figure_error_tab, "Error Profile")
            roughness_tab = oasysgui.createTabPage(figure_error_tab, "Roughness")

            figure_error_box = oasysgui.widgetBox(error_tab, "", orientation="vertical", width=self.CONTROL_AREA_WIDTH-65)
            roughness_box = oasysgui.widgetBox(roughness_tab, "", orientation="vertical", width=self.CONTROL_AREA_WIDTH-65)

            gui.comboBox(figure_error_box, self, "use_figure_error", label="Error Profile",
                         items=["None", "User Defined"], labelWidth=240,
                         callback=self.set_UseFigureError, sendSelectedValue=False, orientation="horizontal")

            self.use_figure_error_box = oasysgui.widgetBox(figure_error_box, "", addSpace=True, orientation="vertical", height=150)
            self.use_figure_error_box_empty = oasysgui.widgetBox(figure_error_box, "", addSpace=True, orientation="vertical", height=150)


            file_box =  oasysgui.widgetBox(self.use_figure_error_box, "", addSpace=False, orientation="horizontal")
            self.le_figure_error_file = oasysgui.lineEdit(file_box, self, "figure_error_file", "File Name", labelWidth=100, valueType=str, orientation="horizontal")
            gui.button(file_box, self, "...", callback=self.selectFigureErrorFile)

            self.le_figure_error_step = oasysgui.lineEdit(self.use_figure_error_box, self, "figure_error_step", "Step", labelWidth=240, valueType=float, orientation="horizontal")
            oasysgui.lineEdit(self.use_figure_error_box, self, "figure_error_amplitude_scaling", "Amplitude scaling factor", labelWidth=240, valueType=float, orientation="horizontal")
            oasysgui.lineEdit(self.use_figure_error_box, self, "figure_error_um_conversion", "User file u.m. to [m] factor", labelWidth=240, valueType=float, orientation="horizontal")

            self.set_UseFigureError()

            gui.comboBox(roughness_box, self, "use_roughness", label="Roughness",
                         items=["None", "User Defined"], labelWidth=240,
                         callback=self.set_UseRoughness, sendSelectedValue=False, orientation="horizontal")

            self.use_roughness_box = oasysgui.widgetBox(roughness_box, "", addSpace=True, orientation="vertical", height=150)
            self.use_roughness_box_empty = oasysgui.widgetBox(roughness_box, "", addSpace=True, orientation="vertical", height=150)

            file_box = oasysgui.widgetBox(self.use_roughness_box, "", addSpace=False, orientation="horizontal")
            self.le_roughness_file = oasysgui.lineEdit(file_box, self, "roughness_file", "File Name", labelWidth=100, valueType=str, orientation="horizontal")
            gui.button(file_box, self, "...", callback=self.selectRoughnessFile)

            oasysgui.lineEdit(self.use_roughness_box, self, "roughness_x_scaling", "x user file u.m. to [m]   factor", labelWidth=240, valueType=float, orientation="horizontal")
            oasysgui.lineEdit(self.use_roughness_box, self, "roughness_y_scaling", "y user file u.m. to [m^3] factor", labelWidth=240, valueType=float, orientation="horizontal")

            gui.comboBox(self.use_roughness_box, self, "roughness_fit_data", label="Fit numeric data with power law",
                         items=["No", "Yes"], labelWidth=240, sendSelectedValue=False, orientation="horizontal")

            self.set_UseRoughness()

        # ---------------------------------------------------------------------------

        calculation_box = oasysgui.widgetBox(self.tab_pro, "Calculation Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-20)

        gui.comboBox(calculation_box, self, "calculation_type", label="Numeric Integration",
                     items=["Automatic Number of Points", "User Defined Number of Points"], labelWidth=140,
                     callback=self.set_CalculationType, sendSelectedValue=False, orientation="horizontal")


        self.empty_box = oasysgui.widgetBox(calculation_box, "", orientation="vertical", width=self.CONTROL_AREA_WIDTH-40, height=50)
        self.number_box = oasysgui.widgetBox(calculation_box, "", orientation="vertical", width=self.CONTROL_AREA_WIDTH-40, height=50)

        oasysgui.lineEdit(self.number_box, self, "number_of_points", "Number of Points", labelWidth=240, valueType=int, orientation="horizontal")

        self.set_CalculationType()

        parallel_box = oasysgui.widgetBox(self.tab_pro, "Parallel Computing", orientation="vertical", width=self.CONTROL_AREA_WIDTH-20)

        gui.comboBox(parallel_box, self, "use_multipool", label="Use Parallel Processing",
                     items=["No", "Yes"], labelWidth=240,
                     callback=self.set_Multipool, sendSelectedValue=False, orientation="horizontal")

        self.use_multipool_box = oasysgui.widgetBox(parallel_box, "", addSpace=False, orientation="vertical", height=100, width=self.CONTROL_AREA_WIDTH-40)
        self.use_multipool_box_empty = oasysgui.widgetBox(parallel_box, "", addSpace=False, orientation="vertical", height=100, width=self.CONTROL_AREA_WIDTH-40)

        oasysgui.lineEdit(self.use_multipool_box, self, "n_pools", "Nr. Parallel Processes", labelWidth=240, valueType=int, orientation="horizontal")

        gui.separator(self.use_multipool_box)

        gui.comboBox(self.use_multipool_box, self, "force_cpus", label="Ignore Nr. Processes > Nr. CPUs",
                     items=["No", "Yes"], labelWidth=240,
                     sendSelectedValue=False, orientation="horizontal")

        le = oasysgui.lineEdit(self.use_multipool_box, self, "number_of_cpus", "Nr. Available CPUs", labelWidth=240, valueType=float, orientation="horizontal")
        le.setReadOnly(True)
        font = QFont(le.font())
        font.setBold(True)
        le.setFont(font)
        palette = QPalette(le.palette())
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 140))
        le.setPalette(palette)

        self.set_Multipool()

    def selectFigureErrorFile(self):
        self.le_figure_error_file.setText(oasysgui.selectFileFromDialog(self, self.figure_error_file, "Select File", file_extension_filter="Data Files (*.dat *.txt)"))

    def selectRoughnessFile(self):
        self.le_roughness_file.setText(oasysgui.selectFileFromDialog(self, self.roughness_file, "Select File", file_extension_filter="Data Files (*.dat *.txt)"))

    def set_FigureErrorPlot(self):
        if self.use_figure_error == 1:
            self.tab[2].setEnabled(True)
            self.plot_canvas[2]._backend.fig.set_facecolor("#FEFEFE")
        else:
            self.tab[2].setEnabled(False)
            self.plot_canvas[2]._backend.fig.set_facecolor("#D7DBDD")

    def set_UseFigureError(self):
        self.use_figure_error_box.setVisible(self.use_figure_error == 1)
        self.use_figure_error_box_empty.setVisible(self.use_figure_error == 0)

    def set_UseRoughness(self):
        self.use_roughness_box.setVisible(self.use_roughness == 1)
        self.use_roughness_box_empty.setVisible(self.use_roughness == 0)

    def set_UseSmallDisplacement(self):
        self.use_small_displacements_box.setVisible(self.use_small_displacements == 1)
        self.use_small_displacements_box_empty.setVisible(self.use_small_displacements == 0)

    def set_CalculationType(self):
        self.empty_box.setVisible(self.calculation_type==0)
        self.number_box.setVisible(self.calculation_type==1)

    def set_Multipool(self):
        self.use_multipool_box.setVisible(self.use_multipool == 1)
        self.use_multipool_box_empty.setVisible(self.use_multipool == 0)

    def after_change_workspace_units(self):
        super(OWOpticalElement, self).after_change_workspace_units()

        label = self.le_length.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        if self.has_figure_error_box:
            label = self.le_figure_error_step.parent().layout().itemAt(0).widget()
            label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_transverse.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_longitudinal.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def build_mirror_specific_gui(self, container_box):
        raise NotImplementedError()

    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            try:
                if input_data.wise_beamline is None or input_data.wise_beamline.get_propagation_elements_number() == 0:
                    if input_data.wise_wavefront is None: raise ValueError("Input Data contains no wavefront and/or no source to perform wavefront propagation")

                self.input_data = input_data.duplicate()

                if self.is_automatic_run: self.compute()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok)

                self.setStatusMessage("Error")

    def set_pre_input(self, data):
        if data is not None:
            try:
                if data.figure_error_file != WisePreInputData.NONE:
                    self.figure_error_file = data.figure_error_file
                    self.figure_error_step = data.figure_error_step
                    self.figure_error_um_conversion = data.figure_user_units_to_m
                    self.use_figure_error = 1

                    self.set_UseFigureError()

                if data.roughness_file != WisePreInputData.NONE:
                    self.roughness_file=data.roughness_file
                    self.roughness_x_scaling = data.roughness_x_scaling
                    self.roughness_y_scaling = data.roughness_y_scaling
                    self.use_roughness = 1

                    self.set_UseRoughness()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok)

                self.setStatusMessage("Error")

    def check_fields(self):
        self.alpha = congruence.checkAngle(self.alpha, "Incidence Angle")
        self.length = congruence.checkStrictlyPositiveNumber(self.length, "Length")

        if self.use_figure_error == 1:
            congruence.checkFileName(self.figure_error_file)

        if self.use_roughness == 1:
            congruence.checkFileName(self.roughness_file)

        if self.calculation_type == 1:
            congruence.checkStrictlyPositiveNumber(self.number_of_points, "Number of Points")

        if self.use_multipool == 1:
            congruence.checkStrictlyPositiveNumber(self.n_pools, "Nr. Parallel Processes")

            if self.force_cpus == 0:
                if self.number_of_cpus == 1:
                    raise Exception("Parallel processing not available with 1 CPU")
                elif self.n_pools >= self.number_of_cpus:
                    raise Exception("Max number of parallel processes allowed on this computer (" + str(self.number_of_cpus) + ")")


    def do_wise_calculation(self):
        if self.input_data is None:
            raise Exception("No Input Data!")

        optical_element = self.get_optical_element(self.get_inner_wise_optical_element())

        wise_optical_element = optical_element.wise_optical_element

        wise_optical_element.CoreOptics.ComputationSettings.Ignore = (self.ignore == 1)

        if self.use_small_displacements == 1:
            wise_optical_element.CoreOptics.ComputationSettings.UseSmallDisplacements = True # serve per traslare/ruotare l'EO
            wise_optical_element.CoreOptics.SmallDisplacements.Rotation = numpy.deg2rad(self.rotation)
            wise_optical_element.CoreOptics.SmallDisplacements.Trans = self.transverse*self.workspace_units_to_m # Transverse displacement (rispetto al raggio uscente, magari faremo scegliere)
            wise_optical_element.CoreOptics.SmallDisplacements.Long = self.longitudinal*self.workspace_units_to_m # Longitudinal displacement (idem)
        else:
            wise_optical_element.CoreOptics.ComputationSettings.UseSmallDisplacements = False
            wise_optical_element.CoreOptics.SmallDisplacements.Rotation = 0.0
            wise_optical_element.CoreOptics.SmallDisplacements.Trans = 0.0
            wise_optical_element.CoreOptics.SmallDisplacements.Long = 0.0

        if self.use_figure_error == 1:
            wise_optical_element.CoreOptics.ComputationSettings.UseFigureError = True

            wise_optical_element.CoreOptics.FigureErrorLoad(File = self.figure_error_file,
                                                            Step = self.figure_error_step * self.workspace_units_to_m, # passo del file
                                                            AmplitudeScaling = self.figure_error_amplitude_scaling * self.figure_error_um_conversion # fattore di scala
                                                           )
        else:
            wise_optical_element.CoreOptics.ComputationSettings.UseFigureError = False

        if self.use_roughness == 1:
            self.use_roughness = 0
            self.set_UseRoughness()

            raise NotImplementedError("Roughness Not yet supported")
        else:
            wise_optical_element.CoreOptics.ComputationSettings.UseRoughness = False

        if self.calculation_type == 0:
            wise_optical_element.ComputationSettings.UseCustomSampling = False
        else:
            # l'utente decide di impostare a mano il campionamento
            wise_optical_element.ComputationSettings.UseCustomSampling = True
            wise_optical_element.ComputationSettings.NSamples = self.number_of_points

        output_data = self.input_data.duplicate()
        input_wavefront = output_data.wise_wavefront

        if output_data.wise_beamline is None: output_data.wise_beamline = WisePropagationElements()

        output_data.wise_beamline.add_beamline_element(WiseBeamlineElement(optical_element=optical_element))

        parameters = PropagationParameters(wavefront=input_wavefront if not input_wavefront is None else WiseWavefront(wise_computation_results=None),
                                           propagation_elements=output_data.wise_beamline)

        parameters.set_additional_parameters("single_propagation", True if PropagationManager.Instance().get_propagation_mode(WISE_APPLICATION) == PropagationMode.STEP_BY_STEP else (not self.is_full_propagator))
        parameters.set_additional_parameters("NPools", self.n_pools if self.use_multipool == 1 else 1)
        parameters.set_additional_parameters("is_full_propagator", self.is_full_propagator)

        output_data.wise_wavefront = PropagationManager.Instance().do_propagation(propagation_parameters=parameters, handler_name=WisePropagator.HANDLER_NAME)

        return output_data

    def get_inner_wise_optical_element(self):
        raise NotImplementedError()

    def get_optical_element(self, inner_wise_optical_element):
        raise NotImplementedError()

    def getTabTitles(self):
        return ["Field Intensity (O.E.)", "Phase (O.E.)", "Figure Error"]

    def getTitles(self):
        return ["Field Intensity (O.E.)", "Phase (O.E.)", "Figure Error"]

    def getXTitles(self):
        return ["S [" + self.workspace_units_label + "]", "S [" + self.workspace_units_label + "]", "S [" + self.workspace_units_label + "]"]

    def getYTitles(self):
        return ["|E0|**2", "Phase", "Height Error [nm]"]

    def getVariablesToPlot(self):
        return [(0, 1), (0, 2), (0, 1)]

    def getLogPlot(self):
        return [(False, False), (False, False), (False, False)]

    def extract_plot_data_from_calculation_output(self, calculation_output):
        output_wavefront = calculation_output.wise_wavefront

        if not output_wavefront is None and not output_wavefront.wise_computation_result is None:
            wise_optical_element = calculation_output.wise_beamline.get_wise_propagation_element(-1)

            S = output_wavefront.wise_computation_result.S
            E = output_wavefront.wise_computation_result.Field
            I = abs(E)**2
            norm = max(I)
            norm = 1.0 if norm == 0.0 else norm
            I = I/norm

            #------------------------------------------------------------

            data_to_plot = numpy.zeros((3, len(S)))
            data_to_plot[0, :] = S / self.workspace_units_to_m
            data_to_plot[1, :] = I
            data_to_plot[2, :] = numpy.imag(E)

            self.is_tab_2_enabled = False

            if not wise_optical_element.CoreOptics.FigureErrors is None and len(wise_optical_element.CoreOptics.FigureErrors) > 0:
                self.is_tab_2_enabled = True
                figure_error_x = numpy.linspace(0, self.length, len(wise_optical_element.CoreOptics.FigureErrors[0]))
                data_to_plot_fe = numpy.zeros((2, len(figure_error_x)))

                data_to_plot_fe[0, :] = figure_error_x
                data_to_plot_fe[1, :] = wise_optical_element.CoreOptics.FigureErrors[0]*1e9 # nm
            else:
                data_to_plot_fe = numpy.zeros((2, 1))

                data_to_plot_fe[0, :] = numpy.zeros(1)
                data_to_plot_fe[1, :] = numpy.zeros(1)

            return data_to_plot, data_to_plot_fe
        else:
            return None, None

    def plot_results(self, plot_data, progressBarValue=80):
        if not self.view_type == 0:
            if not plot_data is None:

                plot_data_1 = plot_data[0]
                plot_data_2 = plot_data[1]

                self.view_type_combo.setEnabled(False)

                titles = self.getTitles()
                xtitles = self.getXTitles()
                ytitles = self.getYTitles()

                progress_bar_step = (100-progressBarValue)/len(titles)

                for index in range(0, len(titles)):
                    x_index, y_index = self.getVariablesToPlot()[index]
                    log_x, log_y = self.getLogPlot()[index]

                    try:
                        if index < 2:
                            if not plot_data_1 is None:
                                self.plot_histo(plot_data_1[x_index, :],
                                                plot_data_1[y_index, :],
                                                progressBarValue + ((index+1)*progress_bar_step),
                                                tabs_canvas_index=index,
                                                plot_canvas_index=index,
                                                title=titles[index],
                                                xtitle=xtitles[index],
                                                ytitle=ytitles[index],
                                                log_x=log_x,
                                                log_y=log_y)
                        else:
                            if not plot_data_2 is None:
                                self.plot_histo(plot_data_2[x_index, :],
                                                plot_data_2[y_index, :],
                                                progressBarValue + ((index+1)*progress_bar_step),
                                                tabs_canvas_index=index,
                                                plot_canvas_index=index,
                                                title=titles[index],
                                                xtitle=xtitles[index],
                                                ytitle=ytitles[index],
                                                log_x=log_x,
                                                log_y=log_y)

                                if index == 2: self.set_FigureErrorPlot()

                    except Exception as e:
                        self.view_type_combo.setEnabled(True)

                        raise Exception("Data not plottable: bad content\n" + str(e))

                self.tabs.setCurrentIndex(0)
                self.view_type_combo.setEnabled(True)
            else:
                raise Exception("Empty Data")

    def receive_syned_data(self, data):
        if not data is None:
            try:
                beamline_element = data.get_beamline_element_at(-1)

                if beamline_element is None:
                    raise Exception("Syned Data not correct: Empty Beamline Element")

                optical_element = beamline_element._optical_element

                if optical_element is None:
                    raise Exception("Syned Data not correct: Empty Optical Element")

                if not isinstance(optical_element, Mirror):
                    raise Exception("Syned Data not correct: Optical Element is not a Mirror")

                self.check_syned_shape(optical_element)

                self.alpha = round(numpy.degrees(0.5*numpy.pi-beamline_element._coordinates._angle_radial), 4)

                boundaries = optical_element._boundary_shape.get_boundaries()

                tangential_size=round(abs(boundaries[3] - boundaries[2])/self.workspace_units_to_m, 6)
                sagittal_size=round(abs(boundaries[1] - boundaries[0])/self.workspace_units_to_m, 6)

                axis = QInputDialog.getItem(self, "Projection Axis", "Select Direction", ("Horizontal", "Vertical"), 0, False)

                if axis == 0:
                    self.length = sagittal_size
                else:
                    self.length = tangential_size

                self.receive_specific_syned_data(optical_element)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok)

                self.setStatusMessage("Error")


    def check_syned_shape(self, optical_element):
        raise NotImplementedError()

    def receive_specific_syned_data(self, optical_element):
        raise NotImplementedError()
