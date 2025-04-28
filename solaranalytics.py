
from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import os
import plotly.graph_objs as go

app = Flask(__name__)
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            session['uploaded_file'] = filepath
            return redirect(url_for('index'))

    return render_template('index.html')

@app.route('/view_data')
def view_data():
    filepath = session.get('uploaded_file', None)
    if filepath:
        df = pd.read_csv(filepath)
        return render_template('view_data.html', tables=[df.to_html(classes='data', header="true", index=False)])
    return redirect(url_for('index'))

@app.route('/visualize', methods=['GET', 'POST'])
def visualize():
    filepath = session.get('uploaded_file', None)
    if not filepath:
        return redirect(url_for('index'))

    df = pd.read_csv(filepath)
    columns = df.columns.tolist()
    chart = None

    if request.method == 'POST':
        x_axis = request.form['x_axis']
        y_axis = request.form['y_axis']
        chart_type = request.form['chart_type']
        data = df[[x_axis, y_axis]].dropna().to_dict(orient='list')
        chart = {'x': data[x_axis], 'y': data[y_axis], 'type': chart_type}

    return render_template('visualize.html', columns=columns, chart=chart)

@app.route('/analysis')
def analysis():
    filepath = session.get('uploaded_file', None)
    if not filepath:
        return redirect(url_for('index'))

    df = pd.read_csv(filepath)
    trend_plot = None

    if 'Year' in df.columns and 'Month' in df.columns and 'Day' in df.columns and 'Daily global solar exposure (MJ/m*m)' in df.columns:
        df['Date'] = pd.to_datetime(df[['Year', 'Month', 'Day']])
        monthly_avg = df.groupby(df['Date'].dt.to_period('M'))['Daily global solar exposure (MJ/m*m)'].mean()
        monthly_avg.index = monthly_avg.index.to_timestamp()

        # Seasonal Patterns
        monthly_seasonal = df.groupby(df['Month'])['Daily global solar exposure (MJ/m*m)'].mean().round(2).to_dict()

        # Anomaly Detection
        Q1 = monthly_avg.quantile(0.25)
        Q3 = monthly_avg.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        anomalies = monthly_avg[(monthly_avg < lower_bound) | (monthly_avg > upper_bound)].round(2).to_dict()

        # Trend Plot
        trend_fig = go.Figure()
        trend_fig.add_trace(go.Scatter(
            x=monthly_avg.index,
            y=monthly_avg.values,
            mode='lines+markers',
            name='Monthly Avg Solar Exposure'
        ))
        trend_fig.update_layout(
            title='Monthly Average Solar Exposure Over Time',
            xaxis_title='Date',
            yaxis_title='Daily Global Solar Exposure (MJ/m²)',
            height=500
        )
        trend_plot = trend_fig.to_html(full_html=False)

        return render_template('analysis.html', seasonal_patterns=monthly_seasonal, anomalies=anomalies, trend_plot=trend_plot)

    return render_template('analysis.html', seasonal_patterns=None, anomalies=None, trend_plot=None)

if __name__ == '__main__':
    app.run(debug=True)

