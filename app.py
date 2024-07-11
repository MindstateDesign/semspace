import pandas as pd
from flask import Flask
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, html, dcc, Input, Output
from flask_cors import CORS

import matplotlib.pyplot as plt




server = Flask(__name__)
server.config['CSP_DIRECTIVES'] = {"frame-ancestors": "*"}

app = Dash(server=server)
CORS(app.server, resources={r"/*": {"origins": "*"}})

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='dropdown-container'),  # Container for the dynamically loaded dropdown
    html.Div(id='content')  # Placeholder for the graph
])

@app.callback(
    [Output('dropdown-container', 'children'),
     Output('content', 'children')],
    [Input('url', 'search')]
)
def update_output(url_search):
    if not url_search:
        return ["No file specified! Append ?file=filename.csv to the URL.", None]

    # Parsing the URL search parameter
    query = url_search.lstrip('?')
    params = dict(x.split('=') for x in query.split('&'))
    filename = params.get('file')
    
    if not filename:
        return ["No file specified! Use the parameter ?file=filename.csv.", None]

    try:
        df = pd.read_csv(filename, sep='\t' if filename.endswith('.tsv') else ',')

        if 'j_semantic_space.tsv' in filename:
            x_col, y_col, z_col = 'PC1_normalized', 'PC2_normalized', 'PC3_normalized'
            title = "J Semantic Space"
            df['probe'].fillna('5-meo-dmt', inplace=True)

            # Color map with gray for '5-meo-dmt'
            #color_map = {probe: 'gray' if probe == '5-meo-dmt' else f'rgba({(i * 89) % 255}, {(i * 107) % 255}, {(i * 123) % 255}, 0.8)' for i, probe in enumerate(df['probe'].unique())}
            cmap = plt.get_cmap('hsv')
            num_probes = len(df['probe'].unique())
            colors = [cmap(float(i) / num_probes) for i in range(num_probes)]  # Normalize index within colormap
            color_map = {probe: 'gray' if probe == '5-meo-dmt' else f'rgba({int(color[0]*255)}, {int(color[1]*255)}, {int(color[2]*255)}, {color[3]})' for probe, color in zip(df['probe'].unique(), colors)}
            fig = go.Figure()

            # Handling normal probes and '5-meo-dmt'
            for probe in df['probe'].unique():
                probe_df = df[df['probe'] == probe]
                # Separate trace for 'Fear, Anxiety, Panic etc.'
                anxiety_df = probe_df[probe_df['anxiety_fear_panic'] == 'Fear, Anxiety, Panic etc.']
                if not anxiety_df.empty:
                    fig.add_trace(go.Scatter3d(
                        x=anxiety_df[x_col],
                        y=anxiety_df[y_col],
                        z=anxiety_df[z_col],
                        mode='markers',
                        marker=dict(size=5, color='darkgreen', opacity=0.74),
                        name=f'{probe} - Anxiety'
                    ))

                # Normal trace
                normal_df = probe_df[probe_df['anxiety_fear_panic'] != 'Fear, Anxiety, Panic etc.']
                if not normal_df.empty:
                    fig.add_trace(go.Scatter3d(
                        x=normal_df[x_col],
                        y=normal_df[y_col],
                        z=normal_df[z_col],
                        mode='markers',
                        marker=dict(size=5, color=color_map[probe], opacity=0.74),
                        name=probe
                    ))

            fig.update_layout(title=title, height=650, legend_title_text='Probe Type')
        else:
            x_col, y_col, z_col = 'e0', 'e1', 'e2'
            color_col = 'drugs'
            title = "Semantic Space Visualization"
            df_sorted_for_legend = df.sort_values(by='drugs')
            fig = px.scatter_3d(df_sorted_for_legend, x=x_col, y=y_col, z=z_col, color=color_col, title=title)
            fig.update_traces(marker=dict(size=3))
            fig.update_layout(height=600)
        config = {'doubleClickDelay': 1000}
        return [None, dcc.Graph(figure=fig, config=config)]
    except Exception as e:
        return [f"An error occurred while trying to read the file: {e}", None]

if __name__ == '__main__':
    app.run_server(debug=True)
