"""WebSocket routes for real-time pipeline streaming.

Provides WebSocket endpoint for subscribing to extract-and-ingest job events with
automatic reconnection support and event replay.
"""

import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from .manager import get_pipeline_ws_manager

logger = logging.getLogger(__name__)
websocket_router = APIRouter()


@websocket_router.websocket("/ws/pipelines/{job_id}")
async def pipeline_websocket(
    websocket: WebSocket,
    job_id: str,
    last_event_id: Optional[str] = Query(None, description="Last seen event ID for replay on reconnect")
):
    """WebSocket endpoint for real-time pipeline streaming.
    
    Connect to this endpoint to receive live updates about extract-and-ingest progress,
    stage transitions, and ingestion status.
    
    **Connection**
    ```javascript
    const ws = new WebSocket(
        'ws://localhost:8000/v1/ws/pipelines/job-123?last_event_id=evt-123456'
    );
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data.event_type, data.payload);
    };
    ```
    
    **Event Types**
    - `connection_established`: Initial connection confirmation with replay count
    - `stage_start`: Pipeline stage beginning (chunking, entity_extraction, etc.)
    - `stage_progress`: Granular progress within a stage (items processed, percent complete)
    - `stage_complete`: Stage finished with result summary
    - `ingestion_status`: Layer 3 ingestion updates (queued, retrying, completed)
    - `pipeline_complete`: Final completion/failure event with full results
    - `error`: Error events with recoverable flag
    - `ping`: Server heartbeat (respond with `pong`)
    
    **Client Messages**
    ```javascript
    // Acknowledge receipt
    ws.send(JSON.stringify({type: 'ack', event_id: 'evt-123'}));
    
    // Respond to ping
    ws.send(JSON.stringify({type: 'pong'}));
    
    // Request history replay
    ws.send(JSON.stringify({type: 'subscribe_history'}));
    ```
    
    **Reconnection Strategy**
    Store the last `event_id` received. On reconnect, pass it as `last_event_id`
    query parameter to receive all missed events.
    
    **Progress Tracking Example**
    ```javascript
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.event_type === 'stage_progress') {
            const { stage, stage_number, overall_percent, items_processed, items_total } = data.payload;
            updateProgressBar(overall_percent);
            updateStageStatus(stage, stage_percent, `${items_processed}/${items_total}`);
        }
        
        if (data.event_type === 'pipeline_complete') {
            const { status, entities_extracted, entities_loaded } = data.payload;
            showResults({ status, entities_extracted, entities_loaded });
        }
    };
    ```
    
    Args:
        job_id: Pipeline job ID to subscribe to
        last_event_id: Optional last seen event for replay on reconnect
    """
    ws_manager = get_pipeline_ws_manager()
    
    try:
        # Accept connection and send replay if reconnecting
        await ws_manager.connect(websocket, job_id, last_event_id)
        
        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for messages from client (acks, pong responses)
                message = await websocket.receive_json()
                await ws_manager.handle_client_message(websocket, job_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"Client disconnected from pipeline job {job_id}")
                break
            except Exception as e:
                logger.warning(f"Error handling client message for job {job_id}: {e}")
                # Continue rather than break to keep connection alive
                
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
    finally:
        # Cleanup connection
        await ws_manager.disconnect(websocket, job_id)
