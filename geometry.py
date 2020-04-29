import re
import pandas as pd
from copy import deepcopy
from collections import defaultdict

class MGeometry(pd.Series):
    def __init__(self, series):
        super().__init__(series)

    @property
    def markdown(self):
        text = f"""
 * section: {self.module_section}
 * Layer:{self.module_layer} (Z: {self.module_z_mm:.2f}mm)
 * Ring: {self.module_ring} (R: {self.radius_mm:.2f}mm)
 * Absolute phi: {self.module_phi_deg:.2f}
 * Corrected phi: {self.module_assembly_phi_deg:.2f}
 * MFB: {self.mfb} on channel {self.opt_services_channel}
 * Power channel: {self.pwr_services_channel}  
        """
        return text

class Geometry(pd.DataFrame):
    """
    Load and filter module list from csv files
    """

    surfaces_dict = {1288.6: 1, 1288.67: 1, 1303.42: 2, 1303.49: 2, 1320.11: 3, 1320.18: 3, 1334.93: 4, 1335.0: 4, 1526.8: 1, 1526.87: 1, 1541.62: 2, 1541.69: 2, 1558.31: 3, 1558.38: 3, 1573.13: 4, 1573.2: 4, 1829.1: 1, 1830.2: 1, 1830.27: 1, 1845.02: 2, 1845.1: 2, 1846.2: 2, 1861.71: 3, 1861.78: 3, 1876.53: 4, 1876.61: 4, 2191.89: 1, 2192.99: 1, 2193.06: 1, 2207.81: 2, 2207.89: 2, 2208.99: 2, 2224.49: 3, 2224.57: 3, 2239.32: 4, 2239.39: 4, 2625.7: 1, 2626.8: 1, 2626.87: 1, 2641.62: 2, 2641.7: 2, 2642.8: 2, 2657.2: 3, 2658.3: 3, 2658.38: 3, 2673.13: 4, 2673.2: 4, 2674.3: 4, -1288.67: 1, -1288.6: 1, -1288.59: 1, -1303.5: 2, -1303.49: 2, -1303.42: 2, -1320.18: 3, -1320.11: 3, -1335.01: 4, -1335.0: 4, -1334.93: 4, -1526.87: 1, -1526.8: 1, -1526.79: 1, -1541.7: 2, -1541.69: 2, -1541.62: 2, -1558.38: 3, -1558.31: 3, -1558.3: 3, -1573.2: 4, -1573.13: 4, -1830.27: 1, -1830.2: 1, -1830.19: 1, -1829.1: 1, -1846.2: 2, -1845.1: 2, -1845.09: 2, -1845.02: 2, -1861.78: 3, -1861.71: 3, -1861.7: 3, -1876.61: 4, -1876.53: 4, -2193.06: 1, -2192.99: 1, -2191.89: 1, -2208.99: 2, -2207.89: 2, -2207.81: 2, -2224.57: 3, -2224.49: 3, -2239.39: 4, -2239.32: 4, -2626.87: 1, -2626.8: 1, -2625.7: 1, -2642.8: 2, -2641.7: 2, -2641.62: 2, -2658.38: 3, -2658.3: 3, -2657.2: 3, -2674.3: 4, -2673.2: 4, -2673.13: 4}
    
    radius = {
        15: 1095.000,
        14: 1031.981,
        13: 928.198,
        12: 859.614, 
        11: 757.251, 
        10: 683.138, 
        9: 581.516,
        8: 555.904,
        7: 508.510,
        6: 480.182,
        5: 433.104,
        4: 402.019,
        3: 355.268,
        2: 321.339,
        1: 274.925
    }

    @property
    def _constructor(self):
        """
        Needed to make subclassing work properly
        see https://pandas.pydata.org/pandas-docs/stable/development/extending.html#override-constructor-properties
        """
        return Geometry
    
    @classmethod
    def from_csv(cls, modules_to_dtc_files, aggregation_files = None, detids_file = None):
        """
        Build geometry from csv files from
        http://cms-tklayout.web.cern.ch/cms-tklayout/layouts-work/recent-layouts/OT616_IT616/cablingOuter.html
        """
        import_options = {
            "skipinitialspace":  True, 
            "index_col": "Module_DetId/i"
        }
        m_to_dtc = pd.concat([pd.read_csv(infile, **import_options) for infile in modules_to_dtc_files])
        if aggregation_files:
            aggregation = pd.concat([pd.read_csv(infile, skiprows = 18, **import_options) for infile in aggregation_files], sort = False)
            aggregation = aggregation.fillna(method="ffill")
            m_to_dtc = m_to_dtc.join(aggregation, rsuffix='_aggregation')
            to_drop = [col for col in m_to_dtc.columns if '_aggregation' in col]
            m_to_dtc = m_to_dtc.drop(axis = 1, columns = to_drop)

        if detids_file:
            detids = pd.read_csv(detids_file, index_col='DetId/i', skipinitialspace = True)
            m_to_dtc = m_to_dtc.join(detids, rsuffix='_detids')
            to_drop = [col for col in m_to_dtc.columns if '_detids' in col]
            m_to_dtc = m_to_dtc.drop(axis = 1, columns = to_drop)

        return cls(m_to_dtc).cleanup().add_radius().tedd_only().add_surfaces().add_side().add_assembly_phi()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)       
        
    def tedd_only(self):
        """
        select detids from tedd only
        """
        return self[self["module_section"].isin(["TEDD_1", "TEDD_2"])]

    def cleanup(self):
        """
        * remove extra characters in columns names and make them lowercase
        * remove extra blanks in string data
        """
        temp = deepcopy(self)
        for col in temp.columns:
            try:
                temp[col] = temp[col].str.replace(' ','')
            except AttributeError:
                pass
        
        temp = temp.rename(columns=lambda key: re.sub(r'(?<!_)(?<!\b)(?<![A-Z])[A-Z]',lambda m: "_"+m.group(0),key))
        return temp.rename(columns=lambda key: key.split("/")[0].lower().strip('_'))

    def add_radius(self):
        self["radius_mm"] = self.apply(lambda row: self.radius.get(row["module_ring"], -1), axis=1)
        return self
    
    def add_surfaces(self):
        """
        add surfaces based on dict of z position. Not very robust but very fast
        """
        self["surface"] = -1
        self["surface"] = self["module_z_mm"].map(self.surfaces_dict)
        return self

    def add_side(self):
        self['side'] = "+"
        self.loc[self["dtc_name"].str.startswith('neg_'), "side"] = "-"
        return self

    def add_assembly_phi(self):
        def assembly_phi(phi, surface, side):
            if phi < 0:
                phi += 180
            if (side == "-" and not surface%2) or (side == "+" and surface%2):
                phi = 180 - phi
            return phi
        self["module_assembly_phi_deg"] = self.apply(lambda row: assembly_phi(row["module_phi_deg"], row["surface"], row["side"]), axis=1)
        return self

    def module_ring(self, ring):
        """single module ring"""
        return self[self["module_ring"] == ring]
    
    def ted_type(self, ttype):
        """TEDD_1 or TEDD_2"""
        return self[self["module_section"] == "TEDD_{}".format(ttype)]
    
    def layer(self, layer_id):
        """Layer inside TEDD_1 or TEDD_2"""
        return self[self["module_layer"] == layer_id]

    def full_layer(self, layer_id):
        """Layer from 1 to 5, ignoring tedd type"""
        if layer_id < 3:
            return self.ted_type(1).layer(layer_id)
        else:
            return self.ted_type(2).layer(layer_id - 2)

    def surface(self, surface):
        """Surface from 1 (inside) to 4(outside)"""
        return self[self["surface"] == surface]
    
    def even(self):
        """Planes withe even ring number"""
        return self[self["module_ring"] % 2 == 0]
    
    def odd(self):
        """Planes with odd ring numbers"""
        return self[self["module_ring"] % 2 == 1]

    def odd_even(self, which):
        if which == "odd":
            return self.odd()
        else:
            return self.even()

    def ted_side(self, side):
        """+ or - side wrt to CMS z"""
        if side == "-":
            return self[self["dtc_name"].str.startswith('neg_')]
        elif side == '+':
            return self[~self["dtc_name"].str.startswith('neg_')]
        else:
            return None

    def up(self):
        """Up side (positive phi)"""
        return self[self["module_phi_deg"] > 0]
    
    def down(self):
        """Down side (negative phi)"""
        return self[self["module_phi_deg"] < 0]

    def up_down(self, which):
        if which == "up":
            return self.up()
        else:
            return self.down()
    
    def module_type(self, mtype):
        """Module type exact match"""
        return self[self["mfc_type"] == mtype]


    def full_selector(self, side, layer, surface, up_down):
        return self.ted_side(side).full_layer(layer).surface(surface).up_down(up_down)

    def get_by_detid(self, detid):
        return self.loc[detid]
    
    def list_by_ring(self):
        lists = {ring: self[self["module_ring"] == ring] for ring in sorted(list(self['module_ring'].unique()))}
        for ring, data in lists.items():
            phis = data["module_phi_deg"].tolist()
            print(f"Ring: {ring}:\t{len(phis)} modules from {phis[0]:.1f} to {phis[-1]:.1f}, R = {data['radius_mm'].to_list()[0]}")

if __name__ == "__main__":

    modules_to_dtc_files = ["ModulesToDTCsPosOuter.csv", "ModulesToDTCsNegOuter.csv"]
    aggregation_files = ["AggregationPatternsPosOuter.csv", "AggregationPatternsNegOuter.csv"]
    detids_file = "DetId_modules_list.csv"
    geometry = Geometry.from_csv(modules_to_dtc_files, aggregation_files, detids_file)

    surfaces = {}
    for side in ["+", "-"]:
        for layer in range(1,6):
            for surface in range(1,5):
                detids = pd.concat(geometry.full_selector(side, layer, surface, v) for v in ["up", "down"])
                grouped = detids.groupby(['module_z_mm'])["module_z_mm"].count().to_dict()
                # grouped = detids.groupby(['surface'])["surface"].count().to_dict()
                # grouped = detids.groupby(['side'])["side"].count().to_dict()
                print("Dee:", side, layer, surface)
                print("Z: "+", ".join([str(k) for k in grouped.keys()]))
                # for k, value in grouped.items():
                #     surfaces[k] = surface
    

