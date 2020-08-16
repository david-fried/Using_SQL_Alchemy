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
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start><end><br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Convert the query results to a dictionary using `date` as the key and `prcp` as the value.
    from flask import jsonify

    results = session.query(Measurement.date, Measurement.prcp).order_by(Measurement.date.asc()).all()

    session.close()

    big_list = []
    for result in results:
        dresults = {}
        dresults['date'] = result[0]
        dresults['prcp'] = result[1]
        big_list.append(dresults)
    
    return jsonify(big_list)

@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query all stations
    stations = session.query(Station.station).all()
    
    session.close()
    
    st_list = []
    for station in stations:
        st_list.append(station[0])
    
    return jsonify(st_list)

@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query the dates and temperature observations of the most active station for the last year of data.
    station_data = session.query(Measurement.station, func.count(Measurement.station)).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).all()
    
    most_active = station_data[0][0]

    last_date = session.query(Measurement.date)[-1]
    last_date = str(last_date).replace(')','').replace('(','').replace("'",'')
    year, month, day = str(last_date).split('-')
    year = int(year) - 1
    month = month.replace(',','')
    day = day.replace(',','')
    year_ago = dt.date(year, int(month), int(day))
    
    results = session.query(Measurement.tobs)\
    .filter((Measurement.station == most_active) & \
            (Measurement.date >= year_ago))\
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
    first_date = dt.datetime.strptime(ordered_dates[0][0], '%Y-%m-%d')
    last_date = dt.datetime.strptime(ordered_dates[-1][0], '%Y-%m-%d')

    start = start.replace('/','-').replace('.','-')

    try:
        dt.datetime.strptime(start, '%Y-%m-%d')
        start = dt.datetime.strptime(start, '%Y-%m-%d')
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
    first_date = dt.datetime.strptime(ordered_dates[0][0], '%Y-%m-%d')
    last_date = dt.datetime.strptime(ordered_dates[-1][0], '%Y-%m-%d')

    start = start.replace('/','-').replace('.','-')
    end = end.replace('/','-').replace('.','-')

    try:
        dt.datetime.strptime(start, '%Y-%m-%d') and dt.datetime.strptime(end, '%Y-%m-%d')
        start = dt.datetime.strptime(start, '%Y-%m-%d')
        end = dt.datetime.strptime(end, '%Y-%m-%d')
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

