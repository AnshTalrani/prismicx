from fastapi import FastAPI
import asyncio

# Import our event manager
from common.event_manager import EventManager

app = FastAPI()

# Global or module-level event manager instance
kafka_config = {
    'bootstrap.servers': 'localhost:9092',
    # other configs...
}
event_manager = EventManager(kafka_config)

@app.on_event("startup")
async def startup_event():
    """
    FastAPI startup event hook to start the Kafka consumer in a background task.
    """
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, event_manager.start_consumer, 'analysis_topic', 'analysis-group')

@app.on_event("shutdown")
async def shutdown_event():
    """
    FastAPI shutdown event hook to stop the Kafka consumer gracefully.
    """
    event_manager.stop_consumer()

@app.get("/analyze")
def analyze():
    """
    Basic synchronous endpoint for analysis.
    Publishes a 'completed' event after returning the result.
    """
    result = {"analysis": "Basic analysis result"}
    # Publish an event indicating the analysis is done
    event_manager.send_event("analysis_complete", "Analysis completed payload")
    return result
