import re
import pandas as pd
from copy import deepcopy

class Geometry(pd.DataFrame):
    """
    Load and filter module list from csv files
    """
    
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

        return cls(m_to_dtc).cleanup().add_radius()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)       
        
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
        """Layer from 1 to 5, ignoring ted type"""
        if layer_id < 3:
            return self.ted_type(1).layer(layer_id)
        else:
            return self.ted_type(2).layer(layer_id - 2)
    
    def surface_tedd1(self, surface_number):
        """Surfaces from 1 (inside) to 4 (outside) in tedd 1"""
        temp = deepcopy(self)
        if surface_number <= 2:
            temp = temp.odd()
        else:
            temp = temp.even()

        if surface_number%2:
            return temp.plane_side(0)
        else:
            return temp.plane_side(1)

    def surface_tedd2(self, surface_number):
        """Surfaces from 1 (inside) to 4 (outside) in tedd 2"""
        temp = deepcopy(self)
        if surface_number <= 2:
            temp = temp.even()
        else:
            temp = temp.odd()

        if surface_number%2:
            return temp.plane_side(0)
        else:
            return temp.plane_side(1)

    def surface(self, surface_number, ted_type):
        if ted_type == 1:
            return self.surface_tedd1(surface_number)
        else:
            return self.surface_tedd2(surface_number)

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
        
    def plane_side(self, side_index):
        """Side of a single plane based on phi angle (odd or even indices for each ring)"""
        to_keep =  []
        for ring in self['module_ring'].unique():
            to_keep.append(self[self["module_ring"] == ring].sort_values(by=['module_phi_deg']).iloc[1-side_index::2])
        return pd.concat(to_keep)
    
    def plane_relative_side(self, which):
        if which == "inside":
            return self.plane_side(0)
        else:
            return self.plane_side(1)

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

    def full_selector(self, side, layer, surface, up_down, fix_phi = False):
        odd_surfaces_first_index = 1
        even_surfaces_first_index = 0
        if side == "-":
            odd_surfaces_first_index = 0
            even_surfaces_first_index = 1

        tedd_type = 1
        if layer >= 3:
            tedd_type = 2

        first_ring_first_disk = "odd"
        first_ring_second_disk = "even"
        if tedd_type == 2:
            first_ring_first_disk = "even"
            first_ring_second_disk = "odd"

        temp = self.ted_side(side).full_layer(layer)

        if surface <= 2:
            temp = temp.odd_even(first_ring_first_disk)
        else:
            temp = temp.odd_even(first_ring_second_disk)

        first_index = odd_surfaces_first_index if surface%2 else even_surfaces_first_index  
        to_keep =  []
        for ring in self['module_ring'].unique():
            to_keep.append(temp[temp["module_ring"] == ring].sort_values(by=['module_phi_deg']).iloc[first_index::2])

        temp = pd.concat(to_keep)

        if fix_phi and ((side == "+" and surface%2) or (side == "-" and not surface%2)):
            temp = temp.flip_hz()

        if fix_phi and up_down == "down":
            temp = temp.bring_up()

        return temp.up_down(up_down)

    def flip_hz(self):
        """layers 1 and 3 have to be flipped horizontally"""
        temp = deepcopy(self)
        temp["module_phi_deg"] = 180 - temp["module_phi_deg"]
        return temp.sort_values(by=['module_phi_deg'])

    def bring_up(self):
        """down dees have to be rotated"""
        temp = deepcopy(self)
        temp["module_phi_deg"] = temp["module_phi_deg"] - 180
        return temp.sort_values(by=['module_phi_deg'])

    def get_by_detid(self, detid):
        return self.loc[detid]
    
    def list_by_ring(self):
        lists = {ring: self[self["module_ring"] == ring] for ring in sorted(list(self['module_ring'].unique()))}
        for ring, data in lists.items():
            phis = data["module_phi_deg"].tolist()
            print(f"Ring: {ring}:\t{len(phis)} modules from {phis[0]:.1f} to {phis[-1]:.1f}, R = {data['radius_mm'].to_list()[0]}")

if __name__ == "__main__":

    test = Geometry.from_csv("ModulesToDTCsPosOuter.csv", "ModulesToDTCsNegOuter.csv").cleanup().add_radius()
    print("** Layer 1, surface 1, up**")
    test.ted_side("+").full_layer(1).surface(1, 1).up_down("up").flip_hz().list_by_ring()
    print("** Layer 1, surface 1, down**")
    test.ted_side("+").full_layer(1).surface(1, 1).up_down("down").flip_hz().bring_up().list_by_ring()
    print("** Layer 1, surface 2**")
    test.ted_side("+").full_layer(1).surface(2, 1).up_down("up").list_by_ring()
    # print("** Layer 3 **")
    # test.ted_side("+").full_layer(3).surface(1, 2).up_down("up").list_by_ring()
