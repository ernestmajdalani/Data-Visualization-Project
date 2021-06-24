import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import json
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from sklearn import preprocessing

# Initialize app
app = dash.Dash(
    __name__
)
app.title = "IGR204 project"
server = app.server

# Load data
with open("data/custom.geo.json") as response:
    countries_geo = json.load(response)
df = pd.read_csv("data/data_merge.csv")
df_choroplet = df.copy()
df_choroplet.columns = ['country', 'year', 'Life expectancy', 'Gini coefficient', 'kg of oil equivalent per capita',
                        'Education index']
countries_id = []
countries_df = df["country"].unique()
for country_geo in countries_geo["features"]:
    country = country_geo["properties"]["admin"]
    for country_df in countries_df:
        if country_df in country:
            country_geo["id"] = country_df
            countries_id.append(country_geo)
            continue
countries_geo["features"] = countries_id
years = [1971, 1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2014]
opacity = 0.8
cols = list(df.columns[2:])
range_color = {}
for column in cols:
    range_color[column] = [df[column].min(), df[column].max()]
scaler = preprocessing.MinMaxScaler()
categories = df.columns[2:]
df_scaled = pd.DataFrame(scaler.fit_transform(df.iloc[:, 2:].values), columns=categories)
df_scaled_histo = pd.concat([df.iloc[:, :2], df_scaled], axis=1)
colorbar_labels = {'economy': 'Gini<br>coefficient', 'energy': 'kg of oil<br>equivalent<br>per capita',
                   'health': 'Life<br>expectancy', 'education': 'Education<br>index'}
bar_labels = {'economy': '<br>Economic inequalites', 'energy': '<br>Energy use', 'health': '<br>Health',
              'education': '<br>Education'}
bar_hover = {'<br>Economic inequalites': 'Gini coefficient', '<br>Energy use': 'kg of oil equivalent per capita',
             '<br>Health': 'Life expectancy', '<br>Education': 'Education index'}

# App layout
app.layout = html.Div(
    id="root",
    children=[
        html.Div(id="header",
                 children=[html.Img(id="logo", src=app.get_asset_url("Logo-Telecom-ParisTech.jpeg")),
                           html.H4(children="IGR204 Project - Economic inequalites"),
                           html.P(id="description",
                                  children="Correlation of inequalites by country in relation to exogenous factors such"
                                           " as access to education, life expectancy and energy consumption")]),
        html.Div(id="app-container",
                 children=[html.Div(id="left-column",
                                    children=[html.Div(id="slider-container",
                                                       children=[html.P(id="slider-text",
                                                                        children="Select desire year"),
                                                                 dcc.Slider(id="years-slider",
                                                                            min=min(years),
                                                                            max=max(years),
                                                                            value=min(years),
                                                                            marks={str(year): {
                                                                                "label": str(year),
                                                                                "style": {"color": "#d9b08c"},
                                                                            } for year in years})]),
                                              html.Div(id="button-container",
                                                       children=[html.P(id="button-text",
                                                                        children="Select desire factor"),
                                                                 dcc.RadioItems(
                                                                     id="button-choice",
                                                                     options=[
                                                                         {'label': 'Economic inequalites',
                                                                          'value': 'economy'},
                                                                         {'label': 'Energy use', 'value': 'energy'},
                                                                         {'label': 'Health', 'value': 'health'},
                                                                         {'label': 'Education', 'value': 'education'}
                                                                     ],
                                                                     value='economy',
                                                                     labelStyle={'display': 'inline-block',
                                                                                 "color": "#d9b08c"},
                                                                     inputStyle={"margin-left": "25px",
                                                                                 "margin-right": "10px"},
                                                                 )]),
                                              html.Div(id="heatmap-container",
                                                       children=[html.P("Heatmap of economy in year 1971",
                                                                        id="heatmap-title"),
                                                                 dcc.Graph(id="country-choropleth")])]),
                           html.Div(id="right-column",
                                    children=[html.P("Countries confrontation", id="graph-detail"),
                                              dcc.Graph(id="radar-container"),
                                              dcc.Graph(id="histo-container")])])
    ],
)


@app.callback([Output("country-choropleth", "figure"), Output("heatmap-title", "children")],
              [Input("years-slider", "value"), Input("button-choice", "value")])
def display_map(year, choice):
    fig = px.choropleth_mapbox(df_choroplet.loc[df_choroplet["year"] == year],
                               geojson=countries_geo,
                               locations='country',
                               color=bar_hover[bar_labels[choice]],
                               animation_frame="year",
                               color_continuous_scale="Viridis", #"jet" #inferno
                               mapbox_style='dark',
                               zoom=1,
                               opacity=opacity,
                               animation_group="country",
                               center={"lat": 20, "lon": 0},
                               range_color=range_color[choice])
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},
                      width=1030,
                      height=560,
                      paper_bgcolor="#33322f",
                      font={"size": 15, "color": "#d9b08c"},
                      coloraxis_colorbar=dict(x=-0.1),
                      clickmode='event+select',
                      mapbox_accesstoken="pk.eyJ1IjoibW9yZ2FuZmEiLCJhIjoiY2txOGllMWhqMGdldzJwbXY2d2lwdHlibiJ9.xFYPp0Cnv"
                                         "ptPswh_NPT3KA",
                      coloraxis=dict(colorbar=dict(title=colorbar_labels[choice])))
    # for mapbox_accesstoken info : see https://docs.mapbox.com/help/glossary/access-token/
    fig.update_geos(fitbounds="locations", visible=False)

    return fig, f"Heatmap of {choice} in year {year}"


@app.callback([Output("radar-container", "figure"), Output("histo-container", "figure")],
              [Input("country-choropleth", "selectedData"), Input("years-slider", "value")])
def display_radar_chart(selectedData, year):
    # default
    if selectedData is None:  # if no data selected, return template
        fig = dict(data=[dict(x=0, y=0)],
                   layout=dict(title="Select countries with click & shift / lasso / box",
                               paper_bgcolor="#23221e",
                               plot_bgcolor="#23221e",
                               font=dict(color="#d9b08c"),
                               margin=dict(t=75, r=50, b=100, l=75),
                               yaxis={'visible': False, 'showticklabels': False},
                               xaxis={'visible': False, 'showticklabels': False}))

        return fig, fig

    # radar chart
    fig1 = go.Figure()
    countries = []
    for point in selectedData["points"]:
        countries_val = df_scaled.loc[(df['year'] == year) & (df['country'] == point["id"])]\
                                 .apply(lambda x: round(x, 3)).values
        countries.append(point["id"])
        fig1.add_trace(go.Scatterpolar(r=list(countries_val[0]) + [countries_val[0][0]],
                                       theta=cols + [cols[0]],
                                       fill='toself',
                                       opacity=opacity,
                                       name=point["id"],
                                       text=["", "Gini coefficient", "kg of oil equivalent per capita",
                                             "Education index", "Life expectancy"],
                                       hovertemplate='<b>Normed value</b>: %{r}<br><b>Factor</b>: %{text}<br>'))
    fig1.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1]),
                                  angularaxis=dict(tickmode="array",
                                                   tickvals=[0, 1, 2, 3, 4],
                                                   ticktext=["    Health", "Economic inequalites<br>", "Energy use    ",
                                                             '<br>Education'],
                                                   )),
                       showlegend=True,
                       title=f'Radar Chart comparison',
                       paper_bgcolor="#23221e",
                       polar_bgcolor="#23221e",
                       font=dict(color="#d9b08c"),
                       margin={"r": 0, "t": 50, "l": 0, "b": 50},
                       legend=dict(yanchor="top",
                                   y=0.99,
                                   xanchor="left",
                                   x=-0.2))

    # bar chart
    fig2 = go.Figure()
    df_histo = pd.DataFrame()
    for category in categories:
        df_temp = pd.concat([df_scaled_histo[['country', 'year', category]],
                             pd.DataFrame(df[category]).rename(columns={category: 'true_value'})], axis=1)
        df_temp['theme'] = bar_labels[category]
        df_temp = df_temp.rename(columns={category: 'value'})
        df_histo = pd.concat([df_histo, df_temp])
    df_histo = df_histo[(df_histo['country'].isin(countries)) & (df_histo['year'] == int(year))].groupby("country")
    for value, group in df_histo:
        temp = pd.concat([pd.DataFrame(group["theme"]), pd.DataFrame(group["year"]), pd.DataFrame(group["true_value"])],
                          axis=1).values
        text = []
        for elt in temp:
            text.append(f'<b>{value}</b> in <b>{str(int(elt[1]))}<br>{bar_hover[str(elt[0])]}</b> = '
                        f'{str(round(elt[2], 3))}')
        fig2.add_trace(go.Bar(x=group["theme"],
                              y=group["value"],
                              name=value,
                              text=text,
                              hovertemplate="%{text}<extra></extra>",
                              showlegend=False,
                              opacity=opacity))
    fig2.update_xaxes(title_text="Theme")
    fig2.update_yaxes(visible=False)
    fig2.update_layout(paper_bgcolor="#23221e",
                       plot_bgcolor="#23221e",
                       font=dict(color="#d9b08c"),
                       margin={"r": 0, "t": 10, "l": 10, "b": 30},
                       legend=dict(yanchor="top",
                                   y=0.90,
                                   xanchor="left",
                                   x=-0.45))

    return fig1, fig2


if __name__ == "__main__":
    app.run_server(debug=True)
