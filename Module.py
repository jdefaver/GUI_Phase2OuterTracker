class Module:
    """
    wrap all module information in a single object
    """
    def __init__(self, external_module, geometry_series = None, geometry_df = None):
        """
        external_module is a ExternalModule sqlalchemy object
        geometry_series is a Pandas Series
        """
        self.module = external_module
        self.__dict__.update(external_module.__dict__)
        self.detid = None
        self.status = self.module.status

        if self.status != None:
            if geometry_series is not None:
                self.geometry = geometry_series.to_dict()
            elif geometry_df is not None:
                self.geometry = geometry_df.loc[self.status.detid].to_dict()

            self.detid = self.status.detid
            self.__dict__.update(self.geometry)

        steps = {'screwed': 'Screw', 'pwr_status': 'Connect power', 'opt_status': 'Connect optics', 'tested': 'Test'}
        try:
            self.next_step = [action for step, action in steps.items() if getattr(self.status, step, None) is None][0] 
        except IndexError:
            self.next_step = None 
            self.next_step_order = -1
        else:
            self.next_step_order = list(steps.values()).index(self.next_step)

    @property
    def markdown(self):
        return f" * detid : {self.detid},  Location : ring {self.ring}, phi = {self.module_phi_deg:.2f}"