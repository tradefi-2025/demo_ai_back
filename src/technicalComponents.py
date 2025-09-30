from typing import Dict, Callable, Optional
from technical_tools import VAEbasedPatternDetector
# Base class

class Indicator:
    def __init__(self,signal):
        self.signal=signal
        pass
    def Compute(self):
        pass


class Min(Indicator):
    def __init__(self,signal):
        super(Min,self).__init__(signal)
        self.value=signal.min()

    def F(self,t):
        return self.value
    
class Min(Indicator):
    def __init__(self,signal):
        super(Min,self).__init__(signal)
        self.value=signal.max()

    def F(self,t):
        return self.value
    
class Component:
    def __init__(self, name: str, previous: Optional['Component'] = None):
        self.name = name
        self.All_const_resp = False
        self.previous = previous

    def check_constraint(self,signal,eps) -> bool:
        """
        Base method to check constraints.
        Should be overridden in child classes.
        """
        raise NotImplementedError("Must be implemented in subclass.")


# Child class: Pattern
class Pattern(Component):
    def __init__(self, name: str, detector: VAEbasedPatternDetector, previous: Optional[Component] = None):
        super().__init__(name, previous=previous)
        self.Detector = detector
        self.ind: Dict[str, 'Indicator'] = {}

    def check_constraint(self,signal,eps) -> bool:
        """
        Override: check constraints specific to the pattern.
        """
        if self.All_const_resp:
            return True
        for c in self.previous:
            if not c.check_constraint(signal,eps):
                return False

        signal=(signal-signal.mean(dim=-1,keepdim=True))/(signal.std(dim=-1,keepdim=True)+1e-4)
        latents = self.Detector.Encode(signal)
        distances = self.Detector.compute_dist(latents)
        self.All_const_resp=distances<=eps
        return self.All_const_resp

    def add_ind(self, name: str, indicator: 'Indicator'):
        """
        Add an indicator to the pattern.
        """
        self.ind[name] = indicator


# Child class: Line
class Line(Component):
    def __init__(self, name: str, F: Callable, previous: Optional[Component] = None):
        super().__init__(name, previous=previous)
        self.F = F

    def check_constraint(self,signal,eps) -> bool:
        """
        Override: check constraints specific to the line.
        """
        if self.All_const_resp:
            return True
        for c in self.previous:
            if not c.check_constraint(signal,eps):
                return False
        self.All_const_resp=True
        return True

    def hits_from_above(self, signal) -> bool:
        """
        Determine if signal hits the line from above.
        """
        # Placeholder logic
        return False

    def hits_from_below(self, signal) -> bool:
        """
        Determine if signal hits the line from below.
        """
        # Placeholder logic
        return False
