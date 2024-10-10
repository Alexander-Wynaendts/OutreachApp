from flask import Flask, render_template, request, send_file, Response
import subprocess
import pandas as pd
import io
from script.main import main

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        file = request.files.get('file')
        if not file:
            return "No file uploaded", 400

        df = pd.read_csv(file)

        # Call the main processing function
        startup_data = main(df)

        # Log the processed dataframe
        if startup_data is None:
            return "Error processing file", 400

        # Convert the processed DataFrame to CSV in-memory using UTF-8 encoding
        output = io.BytesIO()
        startup_data.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)

        # Send the file back as a downloadable CSV
        return send_file(output, mimetype='text/csv', as_attachment=True, download_name='processed_data.csv')

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return f"Error processing file: {str(e)}", 500

# Endpoint to get real-time log output
@app.route('/logs')
def stream_logs():
    def generate():
        with subprocess.Popen(["tail", "-f", "path_to_your_log_file.log"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
            for line in iter(p.stdout.readline, b''):
                yield line.decode('utf-8')
    return Response(generate(), mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True)
