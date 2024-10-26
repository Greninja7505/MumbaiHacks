from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load your dataset
file_path = r'C:\Users\chira\OneDrive\Desktop\Hackethon(New)\crime_visualization\uploads\districtwise-crime-against-women-2017-onwards.csv'
df = pd.read_csv(file_path)

# Load your model
model = joblib.load(r'C:\Users\chira\OneDrive\Desktop\Hackethon(New)\crime_visualization\uploads\my_model.pkl')

@app.route('/')
def index():
    # Get unique states from the dataset
    states = sorted(df['State'].unique())
    return render_template('index.html', states=states)

@app.route('/get_districts/<state>')
def get_districts(state):
    districts = sorted(df[df['State'] == state]['District'].unique())
    return jsonify(districts)

@app.route('/get_reg_circles/<state>/<district>')
def get_reg_circles(state, district):
    reg_circles = sorted(df[(df['State'] == state) & 
                          (df['District'] == district)]['RegCircle'].unique())
    return jsonify(reg_circles)

@app.route('/visualize', methods=['POST'])
def visualize_data():
    try:
        state = request.form['state']
        district = request.form['district']
        reg_circle = request.form['reg_circle']
        selected_year = request.form.get('year')
        crime_types = request.form.getlist('crime_type')
        
        # Base filtering
        filtered_data = df[
            (df['State'] == state) & 
            (df['District'] == district)
        ]
        
        # Additional filters
        if reg_circle and reg_circle != "All":
            filtered_data = filtered_data[filtered_data['RegCircle'] == reg_circle]
            
        if selected_year:
            filtered_data = filtered_data[filtered_data['Year'] == int(selected_year)]

        if filtered_data.empty:
            flash('No data found for the selected criteria.')
            return redirect(url_for('index'))

        # Define crime columns to plot
        crime_columns = [
            'MurderRape', 'DowryDeaths', 'SuicideAbetment', 'Miscarriage', 'AcidAttack',
            'AttemptAcidAttack', 'DomesticCruelty', 'Kidnapping', 'Trafficking',
            'RapeAbove18', 'RapeBelow18', 'AssaultAbove18', 'DomesticViolence',
            'ChildSexualAssault', 'IndecentRepresentation'
        ]

        # Filter crime columns based on selection
        if crime_types:
            crime_columns = [col for col in crime_columns if col in crime_types]

        crime_counts = filtered_data[crime_columns].sum()

        # Create visualization
        plt.figure(figsize=(12, 8))
        ax = sns.barplot(x=crime_counts.index, y=crime_counts.values, palette="viridis")

        # Customize plot
        plt.title(f"Crime Against Women in {district}, {state}", fontsize=16)
        plt.xlabel("Crime Types", fontsize=12)
        plt.ylabel("Number of Cases", fontsize=12)
        plt.xticks(rotation=45, ha="right", fontsize=10)

        # Add value labels
        for i, v in enumerate(crime_counts.values):
            ax.text(i, v + 1, f'{int(v)}', ha='center', va='bottom')

        plt.tight_layout()

        # Save plot
        plot_path = os.path.join(app.config['UPLOAD_FOLDER'], 'crime_visualization.png')
        plt.savefig(plot_path)
        plt.close()

        # Calculate summary statistics
        total_crimes = crime_counts.sum()
        most_common_crime = crime_counts.idxmax()
        avg_crimes = crime_counts.mean()

        # Prepare analysis data
        analysis_data = {
            'total_crimes': int(total_crimes),
            'most_common_crime': most_common_crime,
            'avg_crimes': round(avg_crimes, 2),
            'state': state,
            'district': district,
            'year': selected_year if selected_year else 'All Years'
        }

        return render_template('result.html', 
                             plot_path=plot_path,
                             analysis=analysis_data)

    except Exception as e:
        flash(f'Error generating visualization: {str(e)}')
        return redirect(url_for('index'))

@app.route('/download/<format>')
def download_data(format):
    try:
        if format == 'csv':
            # Generate CSV file
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'crime_data.csv')
            filtered_data.to_csv(output_path, index=False)
            return send_file(output_path, as_attachment=True)
        elif format == 'pdf':
            # Generate PDF report
            # Add PDF generation logic here
            pass
    except Exception as e:
        flash(f'Error downloading data: {str(e)}')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)