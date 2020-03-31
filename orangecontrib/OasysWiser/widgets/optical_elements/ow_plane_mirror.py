import numpy

from syned.widget.widget_decorator import WidgetDecorator
from syned.beamline.shape import Plane

from wiselib2 import Optics

from wofrywise2.beamline.optical_elements.wise_plane_mirror import WisePlaneMirror

from orangecontrib.wise2.widgets.gui.ow_optical_element import OWOpticalElement

class OWPlaneMirror(OWOpticalElement, WidgetDecorator):
    name = "PlaneMirror"
    id = "PlaneMirror"
    description = "Plane Mirror"
    icon = "icons/plane_mirror.png"
    priority = 1

    def after_change_workspace_units(self):
        super(OWPlaneMirror, self).after_change_workspace_units()

    def build_mirror_specific_gui(self, container_box):
        pass

    def get_inner_wise_optical_element(self):
        return Optics.MirrorPlane(L=self.length*self.workspace_units_to_m,
                                  AngleGrazing = numpy.deg2rad(self.alpha))

    def get_optical_element(self, inner_wise_optical_element):
         return WisePlaneMirror(name= self.oe_name,
                                plane_mirror=inner_wise_optical_element,
                                position_directives=self.get_PositionDirectives())


    def receive_specific_syned_data(self, optical_element):
        pass

    def check_syned_shape(self, optical_element):
        if not isinstance(optical_element._surface_shape, Plane):
            raise Exception("Syned Data not correct: Mirror Surface Shape is not Elliptical")

