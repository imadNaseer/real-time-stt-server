# Real-Time Speech-to-Text WebSocket Server

This project implements a real-time speech-to-text WebSocket server using Python, Deepgram API, and WebSockets. It allows clients to send audio data and receive transcriptions in real-time.

## Features

- Real-time audio transcription using Deepgram API
- WebSocket server for bidirectional communication
- Supports both interim and final transcription results
- Configurable transcription options

## Prerequisites

- Python 3.10 or higher
- Deepgram API key

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/subramanya1997/real-time-stt-server.git
   cd real-time-stt-server
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your Deepgram API key:
   - Sign up for a Deepgram account and obtain an API key
   - Set the API key in the `app.py` file:
     ```python
     deepgram_api_key = "your_api_key_here"
     ```

## Usage

1. Start the WebSocket server:
   ```
   python app.py
   ```

2. The server will start running on `0.0.0.0:8765`.

3. To make the server accessible from the internet, you can use ngrok:
   - Install ngrok: https://ngrok.com/download
   - Run ngrok to expose your local server:
     ```
     ngrok http 8765
     ```
   - ngrok will provide a public URL that forwards to your local server

4. Connect to the WebSocket server using a client application or WebSocket testing tool.

5. Send audio data as binary messages to the server for real-time transcription.

## Configuration

You can modify the transcription options in the `LiveOptions` object within the `connect_to_deepgram` method in `app.py`:
