
# app.py
from flask import Flask, render_template, request, redirect, url_for
from main import initialize_knowledge_base, answer_medical_query, add_uploaded_document_to_store, FileReader  # Import necessary functions
import os
import signal
import sys

# Create Flask app instance
app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize the knowledge base before starting the web server
print("Starting app and initializing knowledge base...")
initialize_knowledge_base()  # This ensures that the knowledge base is built only once

# Initialize FileReader for report processing
file_reader = FileReader()

# Home page route
@app.route('/')
def home():
    return render_template('index.html')

# Route to handle user input and chatbot response
@app.route('/get_response', methods=['POST'])
def get_response():
    user_query = request.form['user_query']
    response = answer_medical_query(user_query)  # Knowledge base is already initialized
    return response

# Route to handle file upload and second opinion
@app.route('/upload_report', methods=['POST'])
def upload_report():
    if 'medical_report' not in request.files:
        return "No file part in the request", 400
    file = request.files['medical_report']
    if file.filename == '':
        return "No selected file", 400
    if file:
        # Save the uploaded file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # Process the file and get a second opinion
        extracted_text = file_reader.read_file(filepath)
        if not extracted_text:
            return "Could not read the uploaded medical report", 500

        # Add extracted text to the vector store
        add_uploaded_document_to_store(extracted_text)

        # Query the knowledge base for the report (2nd opinion)
        second_opinion = answer_medical_query(f"Analyze the following medical report: {extracted_text}")

        # Return the response as plain text
        return second_opinion

### Adding New blocks for shutdown
# Add a route to handle termination of the Flask app
@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return "Server shutting down..."

def shutdown_server():
    """ Function to gracefully stop the Flask server. """
    os.kill(os.getpid(), signal.SIGTERM)
## Shutdown blocks end here



# Run the app with debug mode but without the reloader
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
