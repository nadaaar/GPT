from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from openai import OpenAI
from pdf2image import convert_from_bytes
import io, base64,os
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", None)
# OpenAI and PDF processing setup
MODEL_NAME="gpt-4o-2024-05-13"
client = OpenAI(api_key=OPENAI_API_KEY)
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Serve a simple HTML form as the frontend
@app.route('/')
def home():
    return render_template('index.html')

# Route to handle the PDF upload and description processing
@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    description = request.form.get('description', '')
    selector=request.form.get('selector', '')

    # Check if a file was selected and if it's a PDF
    if file.filename == '' or not file.filename.endswith('.pdf'):
        return jsonify({"error": "File is not a PDF or no file selected"}), 400

    # Read the PDF file content
    pdf_bytes = file.read()
    print(description)
    print(selector)
    # Convert PDF to images
    images = pdf_to_images_complete(pdf_bytes)

    # Process images with GPT
    gpt_results = process_images_with_gpt(description, images, selector)

    # Return the response as JSON
    return jsonify({"result": gpt_results})

# Function to convert PDF to base64 images
def pdf_to_images_complete(pdf_bytes):
    images = []
    pages = convert_from_bytes(pdf_bytes)
    for page in pages:
        buffer = io.BytesIO()
        page.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        images.append(base64_image)
    return images

# Function to process images with GPT
def process_images_with_gpt(description, images, selector):
    if selector=="HR":
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Check the job Description: {description} and the attached CV of me and give me a perfectly crafted message to send to the hiring person to stand a chance to get hired. Just give the answer dont explain your answer."
                    }
                ]
            }
        ]
    elif selector=="CEO":
                messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Check the Company description: {description} and the attached CV of me and give me a perfectly crafted message to send to the companys CEO to stand a chance to get hired.  Just give the answer dont explain your answer"
                    }
                ]
            }
        ]

    # Add images to the content
    for image in images:
        messages[0]["content"].append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image}"
            }
        })

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.0,
    )
    return response.choices[0].message.content

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
