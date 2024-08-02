from dash import Dash, dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from cs_clean_data import flatten_dict
from cs_api import get_detections_list, get_detection_data, get_access_token
import io
from dash.exceptions import PreventUpdate

external_stylesheets = [
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css',  # Example of external CSS
]

token = get_access_token()
df = get_detection_data(get_detections_list(token),token)

flattened_data = ([flatten_dict(row) for row in df if row.get('show_in_ui') != False])

data = pd.DataFrame(flattened_data)
data['created_timestamp'] = pd.to_datetime(data['created_timestamp'])

oldest_date = data['created_timestamp'].min()
newest_date = data['created_timestamp'].max()

# Initialize the app
app = Dash(external_stylesheets=external_stylesheets)

# App layout
app.layout = html.Div([
    html.Div([
        html.H1(children='Metrics'),
        html.Div([html.Button(id="btn_csv", children=["Download CSV ", html.I(className="fa fa-download")],className="button"),dcc.Store(id='stored-data'),dcc.Download(id="download-csv")]),
        dcc.DatePickerRange(
            id='date-picker-range',
            start_date=oldest_date,
            end_date=newest_date
        ),
    ], style={'width': '100%', 'display': 'flex', 'justify-content': 'space-between', 'align-items': 'center'}),
    html.Div([
            dash_table.DataTable(
                id='table',
                css=[{'selector': 'table', 'rule': 'table-layout: fixed'}],
                data=data.to_dict('records'),
                style_cell={
                    'textOverflow': 'ellipsis',
                    'overflow': 'hidden'
                },
                columns=[{'name': 'Timestamp', 'id': 'created_timestamp'},
                            {'name': 'Hostname', 'id': 'hostname'},
                            {'name': 'OS', 'id': 'os_version'},
                            {'name': 'User', 'id': 'user_name'},
                            {'name': 'Severity', 'id': 'severity_name'},
                            {'name': 'Status', 'id': 'status'},
                            {'name': 'Analyst', 'id': 'assigned_to_name'},
                            {'name': 'Tag', 'id': 'tags0'},
                            {'name': 'Comment', 'id': 'comment'},
                            {'name': 'CID', 'id': 'cid'}
                        ], 
                page_size=5,
                tooltip_data=[
                    {
                        column: {'value': str(value), 'type': 'markdown'}
                        for column, value in row.items()
                    } for row in data.to_dict('records')
                ],
                tooltip_duration=None
            )
        ], style={'width':'100%', 'display': 'inline-block', 'border': '1px solid red', 'padding': '10px', 'box-sizing': 'border-box'}),
    html.Div([
        html.Div([
            dcc.Graph(id="sc_time_to_triage", style={'height': 100}),
            dcc.Graph(id="sc_time_to_resolved", style={'height': 100})
        ], style={'display': 'inline-block', 'width':'25%'}),
        html.Div([
            dcc.Graph(id="mb_time_to_triage", style={'height': 100}),
            dcc.Graph(id="mb_time_to_resolved", style={'height': 100})
        ], style={'display': 'inline-block', 'width':'25%'}),
        html.Div([
            dcc.Graph(id="os_time_to_triage", style={'height': 100}),
            dcc.Graph(id="os_time_to_resolved", style={'height': 100})
        ], style={'display': 'inline-block', 'width':'25%'}),
        html.Div([
            dcc.Graph(id="kb_time_to_triage", style={'height': 100}),
            dcc.Graph(id="kb_time_to_resolved", style={'height': 100})
        ], style={'display': 'inline-block', 'width':'25%'})
    ], style={'width': '100%', 'display': 'inline-block', 'border': '1px solid red', 'box-sizing': 'border-box'}),
    html.Div([
        html.Div([
            dcc.Graph(id='bar-plot', style={'height': 425})
        ], style={'width': '50%', 'display': 'inline-block', 'border': '1px solid red', 'box-sizing': 'border-box'}),
        html.Div([
            dcc.Graph(id="pie_status", style={'height': 425})
        ], style={'display': 'inline-block', 'border': '1px solid red', 'box-sizing': 'border-box', 'width':'25%'}),
        html.Div([
            dcc.Graph(id="pie_assigned", style={'height': 425})
        ], style={'display': 'inline-block', 'border': '1px solid red', 'box-sizing': 'border-box', 'width':'25%'}),
    ], style={'width': '100%', 'display': 'inline-block'})
        
])

@app.callback(
    [Output('table', 'data'), 
     Output('bar-plot', 'figure'), 
     Output('pie_status', 'figure'), 
     Output('pie_assigned', 'figure'), 
     Output('sc_time_to_triage', 'figure'),
     Output('sc_time_to_resolved', 'figure'),
     Output('mb_time_to_triage', 'figure'),
     Output('mb_time_to_resolved', 'figure'),
     Output('os_time_to_triage', 'figure'),
     Output('os_time_to_resolved', 'figure'),
     Output('kb_time_to_triage', 'figure'),
     Output('kb_time_to_resolved', 'figure'),
     Output('stored-data', 'data')],
    [Input('date-picker-range', 'start_date'), Input('date-picker-range', 'end_date')]
)
def update_table(start_date, end_date):
    if start_date is not None and end_date is not None:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        # Filter the DataFrame based on the selected date range
        filtered_data = data[(data['created_timestamp'] >= start_date) & (data['created_timestamp'] <= end_date)]

        total_sc_detections = filtered_data['assigned_to_name'].value_counts().get('Steven Caraballo', 0)
        total_mb_detections = filtered_data['assigned_to_name'].value_counts().get('Mathew Benitez', 0)
        total_os_detections = filtered_data['assigned_to_name'].value_counts().get('Omar Santiago', 0)
        total_kb_detections = filtered_data['assigned_to_name'].value_counts().get('Keith Blackler', 0)

        table_data = filtered_data.to_dict('records')

        # Create the bar plot
        counts = filtered_data.pivot_table(index='assigned_to_name', columns='severity_name', aggfunc='size', fill_value=0).reset_index()
        fig = go.Figure()

        # Define the order and colors for the legend
        detection_order = ['Informational','Low', 'Medium', 'High', 'Critical']
        colors = {
            'Critical': 'red',
            'High': '#ff8200',
            'Medium': '#ffc000',
            'Low': '#04AA6D',
            'Informational': 'blue'
        }

        # Add traces in the specified order
        for detection_type in detection_order:
            if detection_type in counts.columns:
                fig.add_trace(go.Bar(
                    x=counts['assigned_to_name'],
                    y=counts[detection_type],
                    name=detection_type,
                    marker=dict(color=colors[detection_type]),
                    text=counts[detection_type],  # Set the text to display on each bar
                    textposition='auto'  # Position the text automatically
                ))
                
        fig.update_layout(
            barmode='stack',
            title='Detections Closed Out Per User',
            xaxis_title='User',
            yaxis_title='Count'
        )
        pie_status_colors = {
            'new': 'red',       
            'in_progress': '#ffc000',     
            'closed': '#04AA6D' 
        }
        status_counts = filtered_data['status'].value_counts(normalize=True) * 100
        pie_status = px.pie(values=status_counts.values,
                      names=status_counts.index, 
                      hole=.3,
                      title='Status Percentage',
                      color=status_counts.index,
                      color_discrete_map=pie_status_colors   # Map the colors
                      )
        
        analyst_name_mapping = {'Steven Caraballo':'SC','Mathew Benitez':'MB','Omar Santiago':'OS','Keith Blackler':'KB'}
        pie_assigned_colors = {
            'Steven Caraballo': '#04AA6D',   # Red
            'Mathew Benitez': '#ffc000',   # Green
            'Omar Santiago': '#ff8200',    # Blue
            'Keith Blackler':'red'
        }
        pie_assigned_legend_order = ['Steven Caraballo', 'Mathew Benitez', 'Omar Santiago', 'Keith Blackler']
        status_counts2 = filtered_data['assigned_to_name'].value_counts(normalize=True) * 100

        status_counts_df = status_counts2.reset_index()
        status_counts_df.columns = ['assigned_to_name', 'percentage']

        pie_assigned = px.pie(
                      status_counts_df,
                      values='percentage',
                      names='assigned_to_name', 
                      hole=.3,
                      title='Assigned Percentage',
                      color='assigned_to_name',
                      color_discrete_map=pie_assigned_colors,
                      category_orders={'assigned_to_name': pie_assigned_legend_order}  # Specify legend order
                      )

        #STEVE TIME TO TRIAGED
        total_seconds_to_triaged_sc = filtered_data[filtered_data['assigned_to_name'] == 'Steven Caraballo']['seconds_to_triaged'].sum()
        total_hours_to_triaged_sc = (total_seconds_to_triaged_sc / total_sc_detections) / 3600
        total_minutes_to_triaged_sc = (total_seconds_to_triaged_sc / total_sc_detections) / 60
        total_days_to_triaged_sc = (total_seconds_to_triaged_sc / total_sc_detections) / 86400

        if total_hours_to_triaged_sc >= 1 and total_hours_to_triaged_sc < 24:
            sc_ttt = {'data': [go.Indicator(mode="number", value=round(total_hours_to_triaged_sc, 2),title={"text": "Total Time to Triaged for Steven"},number={"suffix": " Hrs","font": {"size": 48}})]}
        elif total_hours_to_triaged_sc >= 24:
            sc_ttt = {'data': [go.Indicator(mode="number", value=round(total_days_to_triaged_sc, 2),title={"text": "Total Time to Triaged for Steven"},number={"suffix": " Days","font": {"size": 48}})]}
        else:
            sc_ttt = {'data': [go.Indicator(mode="number", value=round(total_minutes_to_triaged_sc, 2),title={"text": "Total Time to Triaged for Steven"},number={"suffix": " Mins","font": {"size": 48}})]}            

        #STEVE TIME TO RESOLVED
        total_seconds_to_resolved_sc = filtered_data[filtered_data['assigned_to_name'] == 'Steven Caraballo']['seconds_to_resolved'].sum()
        total_hours_to_resolved_sc = (total_seconds_to_resolved_sc / total_sc_detections) / 3600
        total_minutes_to_resolved_sc = (total_seconds_to_resolved_sc / total_sc_detections) / 60
        total_days_to_resolved_sc = (total_seconds_to_resolved_sc / total_sc_detections) / 86400

        if total_hours_to_resolved_sc >= 1 and total_hours_to_resolved_sc < 24:
            sc_ttr = {'data': [go.Indicator(mode="number", value=round(total_hours_to_resolved_sc, 2),title={"text": "Total Time to Resolved for Steven"},number={"suffix": " Hrs","font": {"size": 48}})]}
        elif total_hours_to_resolved_sc >= 24:
            sc_ttr = {'data': [go.Indicator(mode="number", value=round(total_days_to_resolved_sc, 2),title={"text": "Total Time to Resolved for Steven"},number={"suffix": " Days","font": {"size": 48}})]}
        else:
            sc_ttr = {'data': [go.Indicator(mode="number", value=round(total_minutes_to_resolved_sc, 2),title={"text": "Total Time to Resolved for Steven"},number={"suffix": " Mins","font": {"size": 48}})]}

        #MATT TIME TO TRIAGED
        total_seconds_to_triaged_mb = filtered_data[filtered_data['assigned_to_name'] == 'Mathew Benitez']['seconds_to_triaged'].sum()
        total_hours_to_triaged_mb = (total_seconds_to_triaged_mb / total_mb_detections) / 3600
        total_minutes_to_triaged_mb = (total_seconds_to_triaged_mb / total_mb_detections) / 60
        total_days_to_triaged_mb = (total_seconds_to_triaged_mb / total_mb_detections) / 86400

        if total_hours_to_triaged_mb >= 1 and total_hours_to_triaged_mb < 24:
            mb_ttt = {'data': [go.Indicator(mode="number", value=round(total_hours_to_triaged_mb, 2),title={"text": "Total Time to Triaged for Matt"},number={"suffix": " Hrs","font": {"size": 48}})]}
        elif total_hours_to_triaged_mb >= 24:
            mb_ttt = {'data': [go.Indicator(mode="number", value=round(total_days_to_triaged_mb, 2),title={"text": "Total Time to Triaged for Matt"},number={"suffix": " Days","font": {"size": 48}})]}
        else:
            mb_ttt = {'data': [go.Indicator(mode="number", value=round(total_minutes_to_triaged_mb, 2),title={"text": "Total Time to Triaged for Matt"},number={"suffix": " Mins","font": {"size": 48}})]}

        #MATT TIME TO RESOLVED
        total_seconds_to_resolved_mb = filtered_data[filtered_data['assigned_to_name'] == 'Mathew Benitez']['seconds_to_resolved'].sum()
        total_hours_to_resolved_mb = (total_seconds_to_resolved_mb / total_mb_detections) / 3600
        total_minutes_to_resolved_mb = (total_seconds_to_resolved_mb / total_mb_detections) / 60
        total_days_to_resolved_mb = (total_seconds_to_resolved_mb / total_mb_detections) / 86400

        if total_hours_to_resolved_mb >= 1 and total_hours_to_resolved_mb < 24:
            mb_ttr = {'data': [go.Indicator(mode="number", value=round(total_hours_to_resolved_mb, 2),title={"text": "Total Time to Resolved for Matt"},number={"suffix": " Hrs","font": {"size": 48}})]}
        elif total_hours_to_resolved_mb >= 24:
            mb_ttr = {'data': [go.Indicator(mode="number", value=round(total_days_to_resolved_mb, 2),title={"text": "Total Time to Resolved for Matt"},number={"suffix": " Days","font": {"size": 48}})]}
        else:
            mb_ttr = {'data': [go.Indicator(mode="number", value=round(total_minutes_to_resolved_mb, 2),title={"text": "Total Time to Resolved for Matt"},number={"suffix": " Mins","font": {"size": 48}})]}

        #OMAR TIME TO TRIAGED
        total_seconds_to_triaged_os = filtered_data[filtered_data['assigned_to_name'] == 'Omar Santiago']['seconds_to_triaged'].sum()
        total_hours_to_triaged_os = (total_seconds_to_triaged_os / total_os_detections) / 3600
        total_minutes_to_triaged_os = (total_seconds_to_triaged_os / total_os_detections) / 60
        total_days_to_triaged_os = (total_seconds_to_triaged_os / total_os_detections) / 86400

        if total_hours_to_triaged_os >= 1 and total_hours_to_triaged_os < 24:
            os_ttt = {'data': [go.Indicator(mode="number", value=round(total_hours_to_triaged_os, 2),title={"text": "Total Time to Triaged for Omar"},number={"suffix": " Hrs","font": {"size": 48}})]}
        elif total_hours_to_triaged_os >= 24:
            os_ttt = {'data': [go.Indicator(mode="number", value=round(total_days_to_triaged_os, 2),title={"text": "Total Time to Triaged for Omar"},number={"suffix": " Days","font": {"size": 48}})]}
        else:
            os_ttt = {'data': [go.Indicator(mode="number", value=round(total_minutes_to_triaged_os, 2),title={"text": "Total Time to Triaged for Omar"},number={"suffix": " Mins","font": {"size": 48}})]}

        #OMAR TIME TO RESOLVED
        total_seconds_to_resolved_os = filtered_data[filtered_data['assigned_to_name'] == 'Omar Santiago']['seconds_to_resolved'].sum()
        total_hours_to_resolved_os = (total_seconds_to_resolved_os / total_os_detections) / 3600
        total_minutes_to_resolved_os = (total_seconds_to_resolved_os / total_os_detections) / 60
        total_days_to_resolved_os = (total_seconds_to_resolved_os / total_os_detections) / 86400

        if total_hours_to_resolved_os >= 1 and total_hours_to_resolved_os < 24:
            os_ttr = {'data': [go.Indicator(mode="number", value=round(total_hours_to_resolved_os, 2),title={"text": "Total Time to Resolved for Omar"},number={"suffix": " Hrs","font": {"size": 48}})]}
        elif total_hours_to_resolved_os >= 24:
            os_ttr = {'data': [go.Indicator(mode="number", value=round(total_days_to_resolved_os, 2),title={"text": "Total Time to Resolved for Omar"},number={"suffix": " Days","font": {"size": 48}})]}
        else:
            os_ttr = {'data': [go.Indicator(mode="number", value=round(total_minutes_to_resolved_os, 2),title={"text": "Total Time to Resolved for Omar"},number={"suffix": " Mins","font": {"size": 48}})]}

        #KEITH TIME TO TRIAGED
        total_seconds_to_triaged_kb = filtered_data[filtered_data['assigned_to_name'] == 'Keith Blackler']['seconds_to_triaged'].sum()
        total_hours_to_triaged_kb = (total_seconds_to_triaged_kb / total_kb_detections) / 3600
        total_minutes_to_triaged_kb = (total_seconds_to_triaged_kb / total_kb_detections) / 60
        total_days_to_triaged_kb = (total_seconds_to_triaged_kb / total_kb_detections) / 86400

        if total_hours_to_triaged_kb >= 1 and total_hours_to_triaged_kb < 24:
            kb_ttt = {'data': [go.Indicator(mode="number", value=round(total_hours_to_triaged_kb, 2),title={"text": "Total Time to Triaged for Keith"},number={"suffix": " Hrs","font": {"size": 48}})]}
        elif total_hours_to_triaged_kb >= 24:
            kb_ttt = {'data': [go.Indicator(mode="number", value=round(total_days_to_triaged_kb, 2),title={"text": "Total Time to Triaged for Keith"},number={"suffix": " Days","font": {"size": 48}})]}
        else:
            kb_ttt = {'data': [go.Indicator(mode="number", value=round(total_minutes_to_triaged_kb, 2),title={"text": "Total Time to Triaged for Keith"},number={"suffix": " Mins","font": {"size": 48}})]}

        #KEITH TIME TO RESOLVED
        total_seconds_to_resolved_kb = filtered_data[filtered_data['assigned_to_name'] == 'Keith Blackler']['seconds_to_resolved'].sum()
        total_hours_to_resolved_kb = (total_seconds_to_resolved_kb / total_kb_detections) / 3600
        total_minutes_to_resolved_kb = (total_seconds_to_resolved_kb / total_kb_detections) / 60
        total_days_to_resolved_kb = (total_seconds_to_resolved_kb / total_kb_detections) / 86400

        if total_hours_to_resolved_kb >= 1 and total_hours_to_resolved_kb < 24:
            kb_ttr = {'data': [go.Indicator(mode="number", value=round(total_hours_to_resolved_kb, 2),title={"text": "Total Time to Resolved for Keith"},number={"suffix": " Hrs","font": {"size": 48}})]}
        elif total_hours_to_resolved_kb >= 24:
            kb_ttr = {'data': [go.Indicator(mode="number", value=round(total_days_to_resolved_kb, 2),title={"text": "Total Time to Resolved for Keith"},number={"suffix": " Days","font": {"size": 48}})]}
        else:
            kb_ttr = {'data': [go.Indicator(mode="number", value=round(total_minutes_to_resolved_kb, 2),title={"text": "Total Time to Resolved for Keith"},number={"suffix": " Mins","font": {"size": 48}})]}


        return table_data, fig, pie_status, pie_assigned, sc_ttt, sc_ttr, mb_ttt, mb_ttr, os_ttt, os_ttr, kb_ttt, kb_ttr, filtered_data.to_dict(orient='records')
    
    # Return the unfiltered data and an empty figure if no dates are selected
    return data.to_dict('records'), go.Figure()

@callback([
    Output("download-csv", "data")],
    [Input("btn_csv", "n_clicks"),
     State('stored-data', 'data')],
    prevent_initial_call=True
)
def func(n_clicks, stored_data):
    if n_clicks is None:
        raise PreventUpdate
    
    # Retrieve DataFrame from stored data
    df_dict = pd.DataFrame.from_records(stored_data)

    return [dcc.send_data_frame(df_dict.to_csv, "some_name.csv")]

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port = 9000)


