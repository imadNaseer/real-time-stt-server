import asyncio
import json
import websockets
import logging
import sys
import os
import time
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveOptions,
    LiveResultResponse,
    LiveTranscriptionEvents,
)
# Ensure Python version is 3.10 or higher
if sys.version_info < (3, 10):
    raise Exception("Deepgram SDK requires Python 3.10 or higher. Please upgrade your Python version.")

# New Key
deepgram_api_key = "deepgram_api_key" 
if not deepgram_api_key:
    raise ValueError("Deepgram API key not found. Please set the 'DEEPGRAM_API_KEY' environment variable.")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
config = DeepgramClientOptions(
    api_key=deepgram_api_key,
    options={
        "keepalive": "true",
    },
)

class DeepgramHandler:
    deepgram: DeepgramClient = DeepgramClient(config)

    def __init__(self):
        self.dg_connection = None
        self.is_finals = []
        self.last_sentence_timestamp = None

    async def connect_to_deepgram(self):
        try:
            print("Connecting to Deepgram")
            print(self.deepgram)
            # Correct WebSocket Connection Method
            self.dg_connection = self.deepgram.listen.asyncwebsocket.v("1")
            logger.info(f"Deepgram connection established, {self.dg_connection}")

            # Register Event Handlers
            self.dg_connection.on(LiveTranscriptionEvents.Transcript, self.on_message)
            self.dg_connection.on(LiveTranscriptionEvents.Open, self.on_open)
            self.dg_connection.on(LiveTranscriptionEvents.Close, self.on_close)
            self.dg_connection.on(LiveTranscriptionEvents.Error, self.on_error)
            self.dg_connection.on(LiveTranscriptionEvents.Unhandled, self.on_unhandled)
            self.dg_connection.on(LiveTranscriptionEvents.Metadata, self.on_metadata)
            self.dg_connection.on(LiveTranscriptionEvents.SpeechStarted, self.on_speech_started)
            self.dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, self.on_utterance_end)

            options = LiveOptions(
                model="nova-2",
                language="en-US",
                smart_format=True,
                punctuate=True,
                endpointing=900,
                utterance_end_ms=1000,
                interim_results=True,
                vad_events=True,
                encoding="linear16",
                channels=1,
                sample_rate=16000,
                # diarize=True,
                # multichannel=False
            )
            addons = {
                "no_delay": "true"  # Changed from string "true" to boolean True
            }

            try:    
                if not self.dg_connection.start(options, addons=addons):
                    raise Exception("Could not start connection to Deepgram")
            except Exception as e:
                logger.error(f'Could not open socket: {e}')
                raise

            logger.info("Connected to Deepgram and configuration sent")

        except Exception as e:
            logger.error(f'Could not open socket: {e}')
            raise

    async def on_message(self, result):
        transcript = result.channel.alternatives[0].transcript
        logger.info(f"Received transcript: {transcript}")
        if not transcript:
            return
        self.last_sentence_timestamp = time.time()
        if result.is_final:
            logger.info(f"Final words: {result.channel.alternatives[0].words}")

            self.is_finals.append(transcript)

            user_message = ' '.join(self.is_finals)
            if result.speech_final:
                logger.info(f'Speech Final: {user_message}')
                await self.send({
                    "text": user_message,
                    "is_final": True,
                })
                self.is_finals = []
                deepgram_flag_latency = time.time() - self.last_sentence_timestamp
                logger.info(f'Deepgram speech_final flag delay in (sec): {round(deepgram_flag_latency, 3)}')

                # TODO: Implement filter_text_and_send_result
            else:
                logger.info(f'Is Final: {transcript}')
                await self.send({
                    "text": user_message,
                    "is_final": False,
                })
        else:
            logger.info(f'Interim Results: {transcript}')

    async def on_utterance_end(self, utterance_end):
        logger.info(f"Utterance end: {utterance_end}")
        deepgram_flag_latency = time.time() - self.last_sentence_timestamp
        if self.is_finals and deepgram_flag_latency >= 1:
            user_message = ' '.join(self.is_finals)
            logger.info(f'on_utterance_end: {user_message}')
            await self.send({
                "text": user_message,
                "is_final": True,
            })
            logger.info(f'Deepgram speech_final flag delay in (sec): {round(deepgram_flag_latency, 3)}')

            # TODO: Implement filter_text_and_send_result
            self.is_finals = []

    async def on_open(self):
        logger.info("Deepgram connection opened")

    async def on_close(self):
        logger.info("Deepgram connection closed")

    async def on_error(self, error):
        logger.error(f"Deepgram error: {error}")

    async def on_unhandled(self, message):
        logger.warning(f"Unhandled Deepgram message: {message}")

    async def on_metadata(self, metadata):
        logger.info(f"Received metadata: {metadata}")

    async def on_speech_started(self):
        logger.info("Speech started")

    async def send(self, message):
        # Implement this method to send messages back to the client
        logger.info(f"Sending message: {message}")

    async def receive(self, bytes_data):
        logger.info(f"Received bytes data")
        await self.dg_connection.send(bytes_data)

async def handle_websocket(websocket, path):
    try:
        async for message in websocket:
            if isinstance(message, bytes):
                logger.info(f"Received binary message")
                await deepgram_handler.receive(message)
            else:
                logger.info(f"Received non-binary message: {message}")
                # For non-binary messages, we don't finish the connection
                continue
    except websockets.exceptions.ConnectionClosed:
        logger.info("Connection closed by client")
    finally:
        # Only finish the Deepgram connection if it was a binary message
        if isinstance(message, bytes):
            await deepgram_handler.dg_connection.finish()
            logger.info("Deepgram connection finished")

deepgram_handler = DeepgramHandler()

async def main():
    host = "0.0.0.0"
    port = 8765    
    print ("In Main")
    await deepgram_handler.connect_to_deepgram()

    logger.info(f"Starting WebSocket server on {host}:{port}")
    async with websockets.serve(handle_websocket, host, port):
        logger.info("WebSocket server is running. Press Ctrl+C to stop.")
        try:
            await asyncio.Future()  # Run forever
        except asyncio.CancelledError:
            logger.info("Server shutting down")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
