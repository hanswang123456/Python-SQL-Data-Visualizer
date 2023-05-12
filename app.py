from flask import Flask, render_template
from bokeh.models import ColumnDataSource, Select, Slider
from bokeh.resources import INLINE
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.layouts import column, row
from bokeh.models.callbacks import CustomJS
from flask import Flask, render_template
from datetime import date

from bokeh.models import CustomJS, DateRangeSlider

#Bokeh graphing
from bokeh.models import ColumnDataSource, Div, Select, Slider
from bokeh.io import curdoc
from bokeh.resources import INLINE
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.palettes import Category20c
from bokeh.transform import cumsum
from bokeh.layouts import column, row

from bokeh.models import ColumnDataSource, GMapOptions, TableColumn, DataTable
from bokeh.plotting import gmap

#Other libries to treat data
import pandas as pd
from math import pi

#sql get data
import mysql.connector

#import gensim
#from gensim.models import Word2Vec




#theme
from bokeh.themes import Theme

curdoc().theme = 'dark_minimal'

# Creating connection object
mydb = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "PW",
    database = "company_example"
)

API_KEY = 'API_KEY_HERE'
cursor = mydb.cursor(buffered = True)
cursor.execute("select * from ufo limit 30000")
all_data = cursor.fetchall()

cursor.execute("select date_time, duration_seconds, city, country, shape, comments from ufo order by duration_seconds desc;")
longest = cursor.fetchall()


cursor.execute("select  date_time, duration_seconds, city, country, shape, comments from ufo order by date_time desc;")
latest = cursor.fetchall()


cursor.execute("select shape, count(shape) from ufo group by shape order by count(shape) desc limit 5;")
type_data = cursor.fetchall()

cursor.execute("select city, count(city) from ufo group by city order by count(city) desc limit 5;")
city_data = cursor.fetchall()

cursor.execute("select state, count(state) from ufo group by state order by count(state) desc limit 5;")
state_data = cursor.fetchall()

cursor.execute("select country, count(country) from ufo group by country order by count(country) desc limit 5;")
region_data = cursor.fetchall()

app = Flask(__name__)

@app.route('/')
def index():
    UFO_shape=["All", "circle", "light", "triangle", "chevron", "cigar", "other"]

    controls = {
        "result": Slider(title="Limit result to", value=100, start=10, end=30000, step=5),
        "year": DateRangeSlider(title="Date Range", value=(date(2016, 1, 1), date(2016, 12, 31)), start=date(1910, 1, 1), end=date(2020, 12, 31)),
        "shape": Select(title="UFO Shape", value="All", options=UFO_shape)
    }

    controls_array = controls.values()

    la = [row[9] for row in all_data]
    long = [row[10] for row in all_data]

    c = [row[1] for row in all_data]
    t = [row[0] for row in all_data]
    d = [row[7] for row in all_data]
    s = [row[4] for row in all_data]
    r = [3000 for row in all_data]
    
    source = ColumnDataSource(data=dict(lat=la, lon=long, time = t, desc = d, shape = s, city = c, radius = r))


    year_cb = CustomJS(args=dict(source=source, controls=controls), code="""
        const data = source.data;
        const val = cb_obj.value
        const s  =new Date(val[0]).getTime()/1000
        const e  =new Date(val[1]).getTime()/1000  

        for (let i = 0; i < data.time.length; i++) {
            
            if(new Date(data.time[i]).getTime()/1000 >= s && new Date(data.time[i]).getTime()/1000 <= e) {
            data.radius[i] = 2500;
            } else {
           data.radius[i] = 0;
            }
        }
        source.change.emit();
    """)

    result_cb = CustomJS(args=dict(source=source, controls=controls), code="""
        const data = source.data;
        const val = cb_obj.value
        const time = data['time']

        for (let i = 0; i < data.length; i++) {
        console.log(time[i], val);
            if(time[i] <= val) {
            time[i].visible = True;
            } else {
            time[i].visible = False;
            }
        }
        source.change.emit();
    """)

    shape_cb = CustomJS(args=dict(source=source, controls=controls), code="""
        const data = source.data;
        const val = cb_obj.value

        for (let i = 0; i < data.shape.length; i++) {
        if(val == 'All') {
            data.radius[i] = 2500;
            continue;
        }
            if(data.shape[i] == val) {
            data.radius[i] = 2500;
            } else {
           data.radius[i] = 0;
            }
        }
        source.change.emit();
    """)
    
    controls['year'].js_on_change('value', year_cb)
    controls['shape'].js_on_change('value', shape_cb)
    controls['result'].js_on_change('value', result_cb)

    TT = [("location","@city"),("time","@time"), ("description","@desc"), ("shape","@shape")]
    map_options = GMapOptions(lat=all_data[0][9], lng=all_data[0][10], map_type="roadmap", zoom=5)

    #create a gmap and draw on circles
    p = gmap(API_KEY, map_options, title="UFO Sightings", active_scroll="auto", active_drag="auto", tooltips = TT, height_policy = 'fit',  width_policy = 'max')
    p.circle(x="lon", y="lat", size=15, fill_color="blue", radius="radius", fill_alpha=0.8, source=source)

    chart_colors = ['#44e5e2', '#e29e44', '#e244db', '#d8e244', '#eeeeee']
    shape_idx, shape_values = zip(*type_data)
    shape_data = pd.Series(shape_values, shape_idx).reset_index(name='value').rename(columns={'index': 'shape'})

    shape_data['angle'] = shape_data['value']/shape_data['value'].sum() * 2 * pi
    shape_data['color'] = chart_colors
    ufo_shape = figure(plot_height=250, plot_width=450, title="Common UFO Shapes", toolbar_location=None,
        tools="hover", tooltips="@shape: @value")
    ufo_shape.xgrid.visible = False
    ufo_shape.ygrid.visible = False
    ufo_shape.xaxis.visible = False
    ufo_shape.yaxis.visible = False

    ufo_shape.wedge(x=0, y=1, radius=0.4,
        start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
        line_color="white",fill_color = 'color', legend='shape', source=shape_data)  
    
    
    
    city_idx, city_values = zip(*city_data)
    loc1_data = pd.Series(city_values, city_idx).reset_index(name='value').rename(columns={'index': 'city'})

    loc1_data['angle'] = loc1_data['value']/loc1_data['value'].sum() * 2 * pi
    loc1_data['color'] = chart_colors 
    ufo_city = figure(plot_height=250, plot_width=450, title="Common UFO citys", toolbar_location=None,
        tools="hover", tooltips="@city: @value")
    ufo_city.xgrid.visible = False
    ufo_city.ygrid.visible = False
    ufo_city.xaxis.visible = False
    ufo_city.yaxis.visible = False

    ufo_city.wedge(x=0, y=1, radius=0.4,
        start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
        line_color="white",fill_color = 'color', legend='city', source=loc1_data)  
    

    state_idx, state_values = zip(*state_data)
    loc2_data = pd.Series(state_values, state_idx).reset_index(name='value').rename(columns={'index': 'state'})

    loc2_data['angle'] = loc2_data['value']/loc2_data['value'].sum() * 2 * pi
    loc2_data['color'] = chart_colors
    ufo_state = figure(plot_height=250, plot_width=450, title="Common UFO states", toolbar_location=None,
        tools="hover", tooltips="@state: @value")
    ufo_state.xgrid.visible = False
    ufo_state.ygrid.visible = False
    ufo_state.xaxis.visible = False
    ufo_state.yaxis.visible = False

    ufo_state.wedge(x=0, y=1, radius=0.4,
        start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
        line_color="white",fill_color = 'color', legend='state', source=loc2_data)  
    

    region_idx, region_values = zip(*region_data)
    loc3_data = pd.Series(region_values, region_idx).reset_index(name='value').rename(columns={'index': 'region'})

    loc3_data['angle'] = loc3_data['value']/loc3_data['value'].sum() * 2 * pi
    loc3_data['color'] = chart_colors
    ufo_region = figure(plot_height=250, plot_width=450, title="Common UFO regions", toolbar_location=None,
        tools="hover", tooltips="@region: @value")
    ufo_region.xgrid.visible = False
    ufo_region.ygrid.visible = False
    ufo_region.xaxis.visible = False
    ufo_region.yaxis.visible = False

    ufo_region.wedge(x=0, y=1, radius=0.4,
        start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
        line_color="white",fill_color = 'color', legend='region', source=loc3_data)  
    latest_stats = pd.DataFrame(latest, columns = [ 'date_time', 'duration_seconds', 'city', 'country', 'shape', 'description' ])#.describe().reset_index()
    latest_data = ColumnDataSource(latest_stats)
    latest_data_col = [TableColumn(field = col, title = col) for col in latest_stats.columns]
    latest_data_table = DataTable(source = latest_data, columns = latest_data_col , height=200)

    longest_stats = pd.DataFrame(longest, columns = [ 'date_time', 'duration_seconds', 'city', 'country', 'shape', 'description' ])#.describe().reset_index()
    longest_duration = ColumnDataSource(longest_stats)
    longest_duration_col =  [TableColumn(field = col, title = col) for col in longest_stats.columns]
    longest_data_table = DataTable(source = longest_duration,  columns = longest_duration_col, height=200)

    ufo_region.background_fill_color = ufo_region.border_fill_color = "black"
    ufo_state.background_fill_color  =  ufo_state.border_fill_color= "black"
    ufo_shape.background_fill_color = ufo_shape.border_fill_color = "black"
    ufo_city.background_fill_color = ufo_city.border_fill_color = "black"
    p.border_fill_color = "black"
    p.yaxis.major_label_text_color  = p.xaxis.major_label_text_color= "white"
    p.yaxis.minor_tick_line_color = p.xaxis.major_tick_line_color = "lightgreen"
    p.title.text_color = ufo_city.title.text_color = ufo_region.title.text_color =  ufo_state.title.text_color = ufo_shape.title.text_color = "white"


    inputs_column = column(*controls_array, Div(text="""Latest Sightings""",width=200, height=20),
                            latest_data_table,Div(text="""Longest Sightings""", width=200, height=20), longest_data_table, width=500)
    
    layout_row = column(row(p, inputs_column ), row(ufo_shape, ufo_city, ufo_region, ufo_state))

    script, div = components(layout_row)
    return render_template(
        'index.html',
        plot_script=script,
        plot_div=div,
        js_resources=INLINE.render_js(),
        css_resources=INLINE.render_css(),
    )
if __name__ == "__main__":
    app.run(debug=True)