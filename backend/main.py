import io
import json
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from PIL import Image
import onnxruntime as ort

# Initialize the FastAPI application
app = FastAPI()

# Load the pretrained ONNX model once during server startup to minimize latency
ort_session = ort.InferenceSession("model.onnx")

# Register the WebSocket route
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Accept the connection from the frontend
    await websocket.accept()
    
    try:
        # Keep an open loop to listen for multiple image uploads from the same client
        while True:
            # 1. Receive raw image bytes streamed from the frontend
            data = await websocket.receive_bytes()
            
            # 2. Preprocess the image to match the MNIST format
            image = Image.open(io.BytesIO(data)).convert("L")  # Convert to grayscale
            image = image.resize((28, 28))                     # Resize to 28x28 pixels
            
            # Convert the image pixels into a normalized numpy array (values between 0.0 and 1.0)
            img_array = np.array(image, dtype=np.float32) / 255.0
            
            # Reshape to match the model's expected input tensor: (batch_size, channels, height, width)
            img_array = img_array.reshape(1, 1, 28, 28)
            
            # 3. Run local inference using ONNX Runtime
            input_name = ort_session.get_inputs()[0].name
            outputs = ort_session.run(None, {input_name: img_array})
            logits = outputs[0]  # Extract raw prediction scores
            
            # 4. Post-process the results to find the highest score and its probability
            pred_label = int(np.argmax(logits))
            
            # Apply the Softmax formula to calculate the confidence percentage
            confidence = float(np.max(np.exp(logits) / np.sum(np.exp(logits), axis=-1)))
            
            # 5. Bundle the predicted label and confidence score into a dictionary
            response = {
                "label": str(pred_label),
                "confidence": round(confidence, 2)
            }
            
            # 6. Send the dictionary back to the frontend as a JSON string
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        # Gracefully handle the event when a user closes their browser
        print("Client disconnected")
