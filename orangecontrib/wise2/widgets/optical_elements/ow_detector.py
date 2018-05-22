import numpy

from syned.widget.widget_decorator import WidgetDecorator
from syned.beamline.shape import Plane

from wiselib2 import Optics

from wofrywise2.beamline.optical_elements.wise_detector import WiseDetector

from orangecontrib.wise2.widgets.gui.ow_optical_element import OWOpticalElement

class OWDetector(OWOpticalElement, WidgetDecorator):
    name = "Detector"
    id = "Detector"
    description = "Detector"
    icon = "icons/screen.png"
    priority = 10

    def after_change_workspace_units(self):
        super(OWDetector, self).after_change_workspace_units()

    def check_fields(self):
        super(OWDetector, self).check_fields()

    def build_mirror_specific_gui(self, container_box):
        pass

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
        return ["Field Intensity (O.E.)", "Phase (O.E.)"]

    def getTitles(self):
        return ["Field Intensity (O.E.)", "Phase (O.E.)"]

    def getXTitles(self):
        return ["S [" + self.workspace_units_label + "]", "S [" + self.workspace_units_label + "]"]

    def getYTitles(self):
        return ["|E0|**2", "Phase"]

    def getVariablesToPlot(self):
        return [(0, 1), (0, 2)]

    def getLogPlot(self):
        return [(False, False), (False, False)]
