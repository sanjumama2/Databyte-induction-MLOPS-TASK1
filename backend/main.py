from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from model import predict 

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    
    # Accept connection
    await websocket.accept()
    print("Client successfully connected!")
    
    try:
        # Keep connection open 
        while True:
            # Receive raw image bytes from the frontend
            image_bytes = await websocket.receive_bytes()
            
            # Pass the bytes for local inference
             
            result_json = predict(image_bytes)
            
            # Send the prediction result back to frontend
            await websocket.send_json(result_json)
            
    except WebSocketDisconnect:
        print("Client disconnected from the server.")