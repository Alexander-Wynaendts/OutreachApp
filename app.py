from flask import Flask, render_template, request, send_file
import pandas as pd
import io
import zipfile
from script.main import main

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Get the uploaded ZIP folder from the request
        file = request.files.get('file')
        if not file:
            return "No file uploaded", 400

        # Read the ZIP file in memory without storing it
        zip_data = zipfile.ZipFile(file)

        # Extract files in-memory as needed
        files = {name: zip_data.read(name) for name in zip_data.namelist()}

        # Pass the extracted files to the main function for processing
        startup_data = main(files)

        # Convert the processed DataFrame to CSV in-memory using UTF-8 encoding
        output = io.BytesIO()
        startup_data.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)

        # Send the file back as a downloadable CSV
        return send_file(output, mimetype='text/csv', as_attachment=True, download_name='cbe_website.csv')

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return f"Error processing file: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
