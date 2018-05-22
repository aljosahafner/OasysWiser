import numpy

from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from syned.widget.widget_decorator import WidgetDecorator
from syned.beamline.shape import Ellipsoid

from wiselib2 import Optics

from wofrywise2.beamline.optical_elements.wise_elliptic_mirror import WiseEllipticMirror

from orangecontrib.wise2.widgets.gui.ow_optical_element import OWOpticalElement


class OWEllipticMirror(OWOpticalElement, WidgetDecorator):
    name = "EllipticMirror"
    id = "EllipticMirror"
    description = "Elliptic Mirror"
    icon = "icons/ellipsoid_mirror.png"
    priority = 2

    f1 = Setting(98.0)
    f2 = Setting(1.2)

    def after_change_workspace_units(self):
        label = self.le_f1.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_f2.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def check_fields(self):
        super(OWEllipticMirror, self).check_fields()

        self.f1 = congruence.checkStrictlyPositiveNumber(self.f1, "F1")
        self.f2 = congruence.checkStrictlyPositiveNumber(self.f2, "F2")

    def build_mirror_specific_gui(self, container_box):
        self.le_f1 = oasysgui.lineEdit(container_box, self, "f1", "F1", labelWidth=240, valueType=float, orientation="horizontal")
        self.le_f2 = oasysgui.lineEdit(container_box, self, "f2", "F2", labelWidth=240, valueType=float, orientation="horizontal")


    def get_inner_wise_optical_element(self):
        return Optics.MirrorElliptic(f1=self.f1*self.workspace_units_to_m,
                                     f2=self.f2*self.workspace_units_to_m,
                                     L=self.length*self.workspace_units_to_m,
                                     Alpha = numpy.deg2rad(self.alpha))

    def get_optical_element(self, inner_wise_optical_element):
         return WiseEllipticMirror(name= self.oe_name,
                                   elliptic_mirror=inner_wise_optical_element,
                                   position_directives=self.get_PositionDirectives())


    def receive_specific_syned_data(self, optical_element):
        p, q = optical_element._surface_shape.get_p_q(numpy.radians(self.alpha))

        self.f1 = numpy.round(p/self.workspace_units_to_m, 6)
        self.f2 = numpy.round(q/self.workspace_units_to_m, 6)

    def check_syned_shape(self, optical_element):
        if not isinstance(optical_element._surface_shape, Ellipsoid):
            raise Exception("Syned Data not correct: Mirror Surface Shape is not Elliptical")
