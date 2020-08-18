from matplotlib import style
style.use('fivethirtyeight')
import matplotlib.pyplot as plt
from flask import Flask, jsonify, request
import numpy as np
import pandas as pd
import datetime as dt
import sqlalchemy
import pandas as pd
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect
from scipy.stats import ttest_ind

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)
# Base.classes.keys()

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

app = Flask(__name__)

# When user hits the index route
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/[start_date]<br/>"
        f"/api/v1.0/[start_date]/[end_date]"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
  
    session = Session(engine)

    from flask import jsonify

    results = session.query(Measurement.date, Measurement.prcp).order_by(Measurement.date.asc()).all()

    session.close()

    big_list = []
    for result in results:
        dresults = {}
        dresults[result[0]] = result[1]
        big_list.append(dresults)
    
    return jsonify(big_list)

@app.route("/api/v1.0/stations")
def stations():

    session = Session(engine)

    stations = session.query(Station.station).all()
    
    session.close()
    
    st_list = []
    for station in stations:
        st_list.append(station[0])
    
    return jsonify(st_list)

@app.route("/api/v1.0/tobs")
def tobs():

    session = Session(engine)

    station_data = session.query(Measurement.station, func.count(Measurement.station)).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).all()
    
    most_active = station_data[0][0]

    last_date = session.query(Measurement.date).order_by(Measurement.date.asc())[-1][0]

    past_year = (dt.datetime.strptime(last_date, '%Y-%m-%d') - dt.timedelta(days=365)).date()
    
    results = session.query(Measurement.tobs)\
    .filter((Measurement.station == most_active) & \
            (Measurement.date >= past_year))\
                .order_by(Measurement.date.asc()).all()

    session.close()

    temps = []

    for row in results:
        temps.append(row[0])
    
    return jsonify(temps)

@app.route("/api/v1.0/<start>")
def start_date(start):
    """TMIN, TAVG, and TMAX for a list of dates.
    
    Arg:
        start_date (string): A date string in the format %Y-%m-%d
        
    Returns:
        TMIN, TAVE, and TMAX
    """
    session = Session(engine)
    ordered_dates = session.query(Measurement.date).order_by(Measurement.date.asc()).all()
    first_date = dt.datetime.strptime(ordered_dates[0][0], '%Y-%m-%d').date()
    last_date = dt.datetime.strptime(ordered_dates[-1][0], '%Y-%m-%d').date()

    try:
        dt.datetime.strptime(start, '%Y-%m-%d').date()
        start = dt.datetime.strptime(start, '%Y-%m-%d').date()
        if start >= first_date and start <= last_date:
            results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs),\
            func.max(Measurement.tobs)).filter((Measurement.date >= start) & \
            (Measurement.date <= last_date)).all()
            session.close()
            results = list(results)
            return jsonify(results[0])
        else:
            return f"Please enter a date between {first_date} and {last_date}."
    except ValueError:
        return jsonify({"error": f"Your response, {start}, was not formatted correctly"}), 404

@app.route("/api/v1.0/<start>/<end>")
def date_range(start, end):
    """TMIN, TAVG, and TMAX for a list of dates.
    
    Args:
        start_date (string): A date string in the format %Y-%m-%d
        end_date (string): A date string in the format %Y-%m-%d
        
    Returns:
        TMIN, TAVE, and TMAX
    """
    session = Session(engine)
    ordered_dates = session.query(Measurement.date).order_by(Measurement.date.asc()).all()
    first_date = dt.datetime.strptime(ordered_dates[0][0], '%Y-%m-%d').date()
    last_date = dt.datetime.strptime(ordered_dates[-1][0], '%Y-%m-%d').date()

    try:
        dt.datetime.strptime(start, '%Y-%m-%d').date() and dt.datetime.strptime(end, '%Y-%m-%d').date()
        start = dt.datetime.strptime(start, '%Y-%m-%d').date()
        end = dt.datetime.strptime(end, '%Y-%m-%d').date()
        if (start >= first_date and start <= last_date) and \
            (end >= first_date and end <= last_date):
            results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs),\
            func.max(Measurement.tobs)).filter(Measurement.date >= start).filter\
            (Measurement.date <= end).all()
            session.close()
            results = list(results)
            return jsonify(results[0])
        else:
            return f"Please enter dates between {first_date} and {last_date}."
    except ValueError:
        return jsonify({"error": f"Your responses, {start} and {end}, were not formatted correctly"}), 404

if __name__ == '__main__':
    app.run(debug=True)

