
class WisePreInputData:

    NONE = "None"

    def __init__(self,
                figure_error_file=NONE,
                figure_error_step=0.0,
                figure_error_amplitude_scaling=1.0,
                figure_user_units_to_m=1.0,
                roughness_file=NONE,
                roughness_x_scaling=1.0,
                roughness_y_scaling=1.0
                ):
        super().__init__()

        self.figure_error_file = figure_error_file
        self.figure_error_step = figure_error_step
        self.figure_error_amplitude_scaling = figure_error_amplitude_scaling
        self.figure_user_units_to_m = figure_user_units_to_m

        self.roughness_file = roughness_file
        self.roughness_x_scaling =roughness_x_scaling
        self.roughness_y_scaling = roughness_y_scaling


from wofrywise2.propagator.propagator1D.wise_propagator import WisePropagationElements
from wofrywise2.propagator.wavefront1D.wise_wavefront import WiseWavefront
from wofrywise2.beamline.wise_beamline_element import WiseBeamlineElement, WiseOpticalElement

import copy

class WiseData(object):
    
    def __init__(self, wise_beamline=WisePropagationElements(), wise_wavefront=WiseWavefront()):
        super().__init__()

        self.wise_beamline = wise_beamline
        self.wise_wavefront = wise_wavefront

    def duplicate(self):
        duplicated_wise_beamline = None

        if not self.wise_beamline is None:
            duplicated_wise_beamline = WisePropagationElements()
            for beamline_element in self.wise_beamline.get_propagation_elements():
                duplicated_wise_optical_element = copy.deepcopy(beamline_element.get_optical_element().wise_optical_element)
                duplicated_wise_beamline.add_beamline_element(WiseBeamlineElement(optical_element=WiseOpticalElement(wise_optical_element=duplicated_wise_optical_element)))

        duplicated_wise_wavefront = None
        if not self.wise_wavefront is None:
            duplicated_wise_wavefront = WiseWavefront(wise_computation_results=copy.deepcopy(self.wise_wavefront.wise_computation_result))

        return WiseData(wise_beamline=duplicated_wise_beamline,
                        wise_wavefront=duplicated_wise_wavefront)
