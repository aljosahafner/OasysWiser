
class WisePreInputData:

    NONE = "None"

    def __init__(self,
                figure_error_file=NONE,
                figure_error_step=0.0,
                figure_user_units_to_m=1.0,
                roughness_file=NONE,
                roughness_x_scaling=1.0,
                roughness_y_scaling=1.0
                ):
        super().__init__()

        self.figure_error_file = figure_error_file
        self.figure_error_step = figure_error_step
        self.figure_user_units_to_m = figure_user_units_to_m

        self.roughness_file = roughness_file
        self.roughness_x_scaling =roughness_x_scaling
        self.roughness_y_scaling = roughness_y_scaling


from wofry.propagator.propagator import PropagationElements
from wofrywise2.propagator.wavefront1D.wise_wavefront import WiseWavefront

class WiseData(object):
    
    def __init__(self, wise_beamline=PropagationElements(), wise_wavefront=WiseWavefront()):
        super().__init__()

        self.wise_beamline = wise_beamline
        self.wise_wavefront = wise_wavefront
