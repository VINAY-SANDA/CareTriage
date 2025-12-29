"""
AI Clinical Pipeline - FastAPI Backend
Main application entry point with all API endpoints.
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import uuid
import logging
import asyncio
from datetime import datetime
from pathlib import Path

from .config import settings
from .models.schemas import (
    SymptomInput, AnalysisRequest, AnalysisResponse,
    ChatRequest, ChatResponse, DocumentUploadResponse,
    UserPreferences, VitalSigns, DisambiguationResult, 
    ClinicalAssessment, RiskAssessment, ClinicianReport, PatientReport
)
from .agents.symptom_agent import symptom_agent
from .agents.retrieval_agent import retrieval_agent
from .agents.triage_agent import triage_agent
from .agents.personalization_agent import personalization_agent
from .agents.risk_engine import risk_engine
from .agents.report_generator import report_generator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Clinical Pipeline",
    description="Comprehensive medical AI system for symptom analysis and clinical reasoning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active sessions
chat_sessions = {}


# ==================== Health Check ====================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI Clinical Pipeline",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "analyze": "/api/analyze",
            "chat": "/api/chat",
            "reports": "/api/reports/{report_id}"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "symptom_agent": "ready",
            "retrieval_agent": retrieval_agent.get_index_stats(),
            "triage_agent": "ready",
            "risk_engine": "ready"
        }
    }


# ==================== Full Analysis Pipeline ====================

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_symptoms(request: AnalysisRequest):
    """
    Complete symptom analysis pipeline.
    
    This endpoint runs the full pipeline:
    1. Symptom Disambiguation
    2. Knowledge Retrieval (RAG)
    3. Clinical Triage
    4. Risk Assessment
    5. Report Generation
    """
    try:
        session_id = str(uuid.uuid4())
        logger.info(f"Starting analysis session: {session_id}")
        
        # Step 1: Symptom Disambiguation
        symptom_input = SymptomInput(description=request.symptoms)
        disambiguation_result = symptom_agent.disambiguate(symptom_input)
        
        logger.info(f"Identified {len(disambiguation_result.symptoms)} symptoms")
        
        # Step 2: Clinical Triage Assessment
        patient_info = {}
        if request.patient_age:
            patient_info["age"] = request.patient_age
        if request.patient_gender:
            patient_info["gender"] = request.patient_gender
        if request.medical_history:
            patient_info["medical_history"] = request.medical_history
        
        clinical_assessment = triage_agent.quick_assess(
            symptoms=disambiguation_result.symptoms,
            patient_info=patient_info if patient_info else None
        )
        
        # Step 3: Risk Assessment
        risk_assessment = risk_engine.assess_risk(
            symptoms=disambiguation_result.symptoms,
            vital_signs=request.vital_signs,
            patient_age=request.patient_age
        )
        
        # Step 4: Personalization
        personalized_recs = None
        if request.user_preferences:
            personalized_recs = personalization_agent.personalize_recommendations(
                recommendations=risk_assessment.recommendations,
                user_preferences=request.user_preferences
            )
        
        # Step 5: Generate Reports
        clinician_report = report_generator.generate_clinician_report(
            symptoms=disambiguation_result.symptoms,
            assessment=clinical_assessment,
            risk_assessment=risk_assessment
        )
        
        patient_report = report_generator.generate_patient_report(
            symptoms=disambiguation_result.symptoms,
            assessment=clinical_assessment,
            risk_assessment=risk_assessment,
            personalized_recommendations=personalized_recs
        )
        
        return AnalysisResponse(
            session_id=session_id,
            disambiguation_result=disambiguation_result,
            clinical_assessment=clinical_assessment,
            risk_assessment=risk_assessment,
            clinician_report=clinician_report,
            patient_report=patient_report
        )
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Chat Interface ====================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Interactive chat endpoint for symptom collection.
    """
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        # Initialize session if new
        if session_id not in chat_sessions:
            chat_sessions[session_id] = {
                "messages": [],
                "symptoms": [],
                "state": "collecting",
                "clarification_count": 0
            }
        
        session = chat_sessions[session_id]
        session["messages"].append({"role": "user", "content": request.message})
        
        # Process based on state
        if session["state"] == "collecting":
            # Try to extract symptoms
            symptom_input = SymptomInput(description=request.message)
            result = symptom_agent.disambiguate(symptom_input)
            
            # Always add found symptoms
            if result.symptoms:
                session["symptoms"].extend(result.symptoms)
                logger.info(f"Found {len(result.symptoms)} symptoms, total: {len(session['symptoms'])}")
            
            # If we have symptoms, proceed to assessment (don't keep asking for clarification)
            if session["symptoms"]:
                # Move to assessment phase
                risk = risk_engine.assess_risk(session["symptoms"])
                
                # Build symptom summary
                symptom_names = [s.clinical_term for s in session["symptoms"]]
                symptom_list = ", ".join(symptom_names)
                
                response_msg = f"Thank you for sharing. I've identified the following symptoms: **{symptom_list}**.\n\n"
                
                if risk.escalation_required:
                    response_msg += f"⚠️ **Alert**: Risk score is {risk.risk_score:.1%} - some symptoms require attention.\n\n"
                else:
                    response_msg += f"Risk assessment: {risk.risk_level.value} ({risk.risk_score:.1%})\n\n"
                
                response_msg += "Would you like me to generate a detailed assessment report?"
                session["state"] = "ready_for_report"
                
                return ChatResponse(
                    message=response_msg,
                    session_id=session_id,
                    risk_alert=risk if risk.escalation_required else None,
                    report_ready=True
                )
            else:
                # No symptoms found, ask for more details (but limit attempts)
                session["clarification_count"] = session.get("clarification_count", 0) + 1
                
                if session["clarification_count"] >= 3:
                    # Give up and try to help anyway
                    return ChatResponse(
                        message="I'm having trouble understanding your symptoms. Could you try describing:\n- What specific part of your body is affected?\n- How severe is the discomfort (mild/moderate/severe)?\n- How long have you had these symptoms?",
                        session_id=session_id,
                        requires_clarification=True
                    )
                
                return ChatResponse(
                    message="I'd like to help you better. Could you describe your symptoms in more detail? For example: 'I have a headache and fever for 2 days'",
                    session_id=session_id,
                    requires_clarification=True
                )
        
        elif session["state"] == "ready_for_report":
            if any(word in request.message.lower() for word in ["yes", "sure", "ok", "generate", "report", "please", "yeah"]):
                # Generate full assessment
                logger.info(f"Generating report for {len(session['symptoms'])} symptoms")
                
                assessment = triage_agent.quick_assess(session["symptoms"])
                risk = risk_engine.assess_risk(session["symptoms"])
                
                report = report_generator.generate_patient_report(
                    symptoms=session["symptoms"],
                    assessment=assessment,
                    risk_assessment=risk
                )
                
                formatted_report = report_generator.format_report_as_text(report)
                
                # Reset session for new conversation
                session["state"] = "done"
                
                return ChatResponse(
                    message=formatted_report,
                    session_id=session_id,
                    report_ready=True
                )
            else:
                # User said no or wants to add more
                session["state"] = "collecting"
                return ChatResponse(
                    message="No problem. Is there anything else you'd like to share about your symptoms?",
                    session_id=session_id
                )
        
        elif session["state"] == "done":
            # Start fresh
            session["symptoms"] = []
            session["state"] = "collecting"
            session["clarification_count"] = 0
            return ChatResponse(
                message="Starting a new assessment. Please describe your symptoms.",
                session_id=session_id
            )
        
        return ChatResponse(
            message="I'm here to help. Please describe your symptoms.",
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WebSocket Chat ====================

@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Process message
            request = ChatRequest(
                message=data.get("message", ""),
                session_id=session_id
            )
            
            response = await chat(request)
            
            await websocket.send_json(response.dict())
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()


# ==================== Document Upload ====================

@app.post("/api/upload-documents", response_model=DocumentUploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Upload ICMR PDF documents for RAG indexing.
    """
    try:
        uploaded_count = 0
        
        for file in files:
            if file.filename.endswith('.pdf'):
                file_path = settings.ICMR_DOCS_DIR / file.filename
                
                with open(file_path, 'wb') as f:
                    content = await file.read()
                    f.write(content)
                
                uploaded_count += 1
                logger.info(f"Uploaded: {file.filename}")
        
        if uploaded_count > 0:
            # Re-index documents
            result = retrieval_agent.ingest_documents()
            
            return DocumentUploadResponse(
                success=result["success"],
                documents_processed=result["documents_processed"],
                chunks_created=result["chunks_created"],
                message=result["message"]
            )
        else:
            return DocumentUploadResponse(
                success=False,
                documents_processed=0,
                chunks_created=0,
                message="No PDF files were uploaded"
            )
            
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Reports ====================

@app.get("/api/reports/{report_id}")
async def get_report(report_id: str):
    """Retrieve a generated report by ID."""
    report = report_generator.get_report(report_id)
    
    if report:
        return report
    else:
        raise HTTPException(status_code=404, detail="Report not found")


# ==================== Knowledge Base ====================

@app.get("/api/knowledge/search")
async def search_knowledge(query: str, top_k: int = 5):
    """Search the ICMR knowledge base."""
    results = retrieval_agent.retrieve(query, top_k=top_k)
    return {"query": query, "results": results}


@app.get("/api/knowledge/stats")
async def knowledge_stats():
    """Get knowledge base statistics."""
    return retrieval_agent.get_index_stats()


# ==================== Risk Assessment ====================

@app.post("/api/risk-assess")
async def assess_risk(
    symptoms: List[str],
    vital_signs: Optional[VitalSigns] = None,
    patient_age: Optional[int] = None
):
    """Quick risk assessment endpoint."""
    try:
        # Convert symptom strings to structured symptoms
        symptom_input = SymptomInput(description=", ".join(symptoms))
        result = symptom_agent.disambiguate(symptom_input)
        
        assessment = risk_engine.assess_risk(
            symptoms=result.symptoms,
            vital_signs=vital_signs,
            patient_age=patient_age
        )
        
        return assessment
        
    except Exception as e:
        logger.error(f"Risk assessment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Startup Events ====================

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    logger.info("="*50)
    logger.info("AI Clinical Pipeline Starting...")
    logger.info("="*50)
    
    # Validate configuration
    try:
        settings.validate()
        logger.info("✓ Configuration validated")
    except Exception as e:
        logger.warning(f"Configuration warning: {e}")
    
    # Check knowledge base
    stats = retrieval_agent.get_index_stats()
    if stats["total_chunks"] > 0:
        logger.info(f"✓ Knowledge base loaded: {stats['total_chunks']} chunks")
    else:
        logger.info("○ Knowledge base empty - upload ICMR documents via /api/upload-documents")
    
    # Check ML model
    if risk_engine.model:
        logger.info("✓ Risk assessment model loaded")
    else:
        logger.info("○ Risk model not found - run 'python train_model.py' to train")
    
    logger.info("="*50)
    logger.info("Server ready!")
    logger.info("API Docs: http://localhost:8000/docs")
    logger.info("="*50)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
