import os
import sys
import datetime
import random
from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, Boolean, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.sql import func

from geometry import Geometry

import logging
logging.basicConfig(level=logging.DEBUG)

Base = declarative_base()

class LogEvent(Base):
    __tablename__ = "log_events"
    id = Column(Integer, primary_key=True)
    barcode = Column(Integer)
    text = Column(String(250), nullable=False)
    time = Column(DateTime(),  default=func.now())

    def __repr__(self):
        return f"{self.time}: {self.text}"

class ExternalModule(Base):
    """
    Table to hold a mock of the CERN assembly database
    """
    __tablename__ = "external_module"
    id = Column(Integer, primary_key=True)
    barcode = Column(String(250))
    location = Column(String(250))
    # 2S, PS5G or PS10G
    module_type = Column(String(250))
    module_thickness = Column(String(250))
    status = relationship("ModuleStatus", uselist=False, back_populates="module")
    

class ModuleStatus(Base):
    __tablename__ = "module_status"
    id = Column(Integer, primary_key=True)
    detid = Column(Integer, nullable = False, unique = True)
    screwed = Column(DateTime())
    pwr_status = Column(DateTime())
    opt_status = Column(DateTime())
    tested = Column(DateTime())
    test_status = Column(String(250))
    barcode = Column(String(250), ForeignKey('external_module.barcode'))
    module = relationship("ExternalModule", back_populates="status")

    def __str__(self):
        return f"detid: {self.detid}\nbarcode: {self.barcode}\nscrewed: {self.screwed}\npower: {self.pwr_status}\noptical: {self.opt_status}\ntested: {self.tested}\nresults: {self.test_status}"

def db_session(infile = 'sqlite:///dee_builder.db'):
    engine = create_engine(infile)
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session

engine = create_engine('sqlite:///dee_builder.db')
DBSession = sessionmaker(bind=engine)

if __name__ == "__main__":
    engine = create_engine('sqlite:///dee_builder.db')
    Base.metadata.create_all(engine)

    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    # seed fake modules
    # tedd has 
    #  * 2792 2S 1.8mm modules
    #  * 424  2S 4.0mm modules
    #  * 1408 PS 4.0mm 5G momdules
    #  * 1312 PS 4.0mm 10G modules
    locations = ['CERN','Louvain']
    i = 0
    s2_18 = [{"barcode": str(i), "module_type": "2S", "location":random.choice(locations), "module_thickness": 1.8} for i in range(2792)]
    i = 2792
    s2_40 = [{"barcode": str(i), "module_type": "2S", "location":random.choice(locations), "module_thickness": 4.0} for i in range(i,i+424)]
    i += 424
    ps_5g = [{"barcode": str(i), "module_type": "PS5G", "location":random.choice(locations), "module_thickness": 1.8} for i in range(i,i+1408)]
    i += 1408
    ps_10g = [{"barcode": str(i), "module_type": "PS10G", "location":random.choice(locations), "module_thickness": 1.8} for i in range(i,i+1312)]
    modules = s2_18 + s2_40 + ps_5g + ps_10g
    session.add_all([ExternalModule(**data) for data in modules])

    mfiles = ["ModulesToDTCsNegOuter.csv", "ModulesToDTCsPosOuter.csv"]
    afiles = ["AggregationPatternsPosOuter.csv", "AggregationPatternsNegOuter.csv"]
    dfile = "DetId_modules_list.csv"
    geo = Geometry.from_csv(mfiles, afiles, dfile)

    # get one full dee
    test_dee_1 = geo.full_selector("+",1,1,"up")
    test_dee_5 = geo.full_selector("+",5,1,"up")

    def random_datetime(start, end):
        return start + datetime.timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

    def rand_result():
        picks = ["ok", "faulty", None]
        weights = [0.5,0.1,0.4]
        return random.choices(picks,weights=weights,k=1)[0]

    def associate_by_type(geometry_df, module_list, module_type, module_thickness = None):
        # FIXME : remove used modules from list
        d1 = datetime.datetime.strptime('1/1/2019 1:30 PM', '%m/%d/%Y %I:%M %p')
        d2 = datetime.datetime.strptime('1/1/2020 4:50 AM', '%m/%d/%Y %I:%M %p')

        detids = geometry_df[geometry_df["type"] == module_type]
        if module_thickness:
            detids = detids[detids["sensor_spacing_mm"] == module_thickness]
        num = len(detids)
        logging.debug(f"criteria: {module_type}, {module_thickness}")
        logging.debug(f"needed: {num}")
        candidates = [m["barcode"] for m in module_list if m["module_type"] == module_type and m['location'] == 'Louvain']
        logging.debug(f"candidates: {len(candidates)}")
        barcodes = random.sample(candidates, num)
        return [{"barcode":barcodes.pop(), "detid":detid, "screwed":random_datetime(d1,d2), "test_status":rand_result() } for detid, row in detids.iterrows()]

    detids = associate_by_type(test_dee_1, modules, "2S", 1.8)
    detids += associate_by_type(test_dee_1, modules, "2S", 4.0)
    detids += associate_by_type(test_dee_1, modules, "PS5G")
    detids += associate_by_type(test_dee_1, modules, "PS10G")

    detids = associate_by_type(test_dee_5, modules, "2S", 1.8)
    detids += associate_by_type(test_dee_5, modules, "2S", 4.0)
    detids += associate_by_type(test_dee_5, modules, "PS5G")
    detids += associate_by_type(test_dee_5, modules, "PS10G")

    session.add_all([ModuleStatus(**data) for data in detids])

    session.commit()
