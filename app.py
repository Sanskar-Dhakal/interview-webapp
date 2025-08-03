from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import random
import io
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Mock data storage
interview_sessions = {}
current_session_id = None

# Hardcoded interview questions
INTERVIEW_QUESTIONS = [
    "Can you walk me through your experience with the technologies mentioned in your resume?",
    "Describe a challenging project you worked on and how you overcame obstacles.",
    "How do you handle working in a team environment with different personalities?"
]

@app.route('/start_interview', methods=['POST'])
def start_interview():
    """Start a new interview session"""
    global current_session_id
    
    try:
        data = request.get_json()
        resume_file = request.files.get('resume')
        job_role = data.get('job_role', 'Unknown Role')
        
        # Generate session ID
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
        current_session_id = session_id
        
        # Initialize session data
        interview_sessions[session_id] = {
            'job_role': job_role,
            'resume_filename': resume_file.filename if resume_file else 'No file uploaded',
            'start_time': datetime.now().isoformat(),
            'questions': INTERVIEW_QUESTIONS.copy(),
            'answers': [],
            'current_question': 0,
            'metrics': {
                'attention': random.randint(70, 95),
                'positivity': random.randint(70, 95),
                'confidence': random.randint(70, 95)
            }
        }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Interview session started successfully',
            'first_question': INTERVIEW_QUESTIONS[0],
            'total_questions': len(INTERVIEW_QUESTIONS)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    """Submit an answer and get next question"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        answer_text = data.get('answer', '')
        audio_data = data.get('audio', None)  # For future audio processing
        
        if session_id not in interview_sessions:
            return jsonify({
                'success': False,
                'error': 'Invalid session ID'
            }), 400
        
        session = interview_sessions[session_id]
        
        # Store the answer
        session['answers'].append({
            'question': session['questions'][session['current_question']],
            'answer': answer_text,
            'timestamp': datetime.now().isoformat()
        })
        
        # Move to next question
        session['current_question'] += 1
        
        # Update metrics (simulate real-time analysis)
        session['metrics'] = {
            'attention': random.randint(70, 95),
            'positivity': random.randint(70, 95),
            'confidence': random.randint(70, 95)
        }
        
        # Check if interview is complete
        if session['current_question'] >= len(session['questions']):
            return jsonify({
                'success': True,
                'interview_complete': True,
                'message': 'Interview completed successfully',
                'metrics': session['metrics'],
                'total_questions': len(session['questions']),
                'total_answers': len(session['answers'])
            }), 200
        else:
            # Return next question
            next_question = session['questions'][session['current_question']]
            return jsonify({
                'success': True,
                'interview_complete': False,
                'next_question': next_question,
                'question_number': session['current_question'] + 1,
                'total_questions': len(session['questions']),
                'metrics': session['metrics']
            }), 200
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/get_report', methods=['GET'])
def get_report():
    """Generate and return a PDF report"""
    try:
        session_id = request.args.get('session_id')
        
        if not session_id or session_id not in interview_sessions:
            return jsonify({
                'success': False,
                'error': 'Invalid session ID'
            }), 400
        
        session = interview_sessions[session_id]
        
        # Generate PDF report
        pdf_buffer = generate_pdf_report(session)
        pdf_buffer.seek(0)
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'interview_report_{session_id}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/get_metrics', methods=['GET'])
def get_metrics():
    """Get current metrics for a session"""
    try:
        session_id = request.args.get('session_id')
        
        if not session_id or session_id not in interview_sessions:
            return jsonify({
                'success': False,
                'error': 'Invalid session ID'
            }), 400
        
        session = interview_sessions[session_id]
        
        return jsonify({
            'success': True,
            'metrics': session['metrics'],
            'current_question': session['current_question'],
            'total_questions': len(session['questions'])
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200

def generate_pdf_report(session):
    """Generate a PDF report for the interview session"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    story.append(Paragraph("AI Interview Report", title_style))
    story.append(Spacer(1, 20))
    
    # Session Information
    story.append(Paragraph(f"<b>Job Role:</b> {session['job_role']}", styles['Normal']))
    story.append(Paragraph(f"<b>Resume:</b> {session['resume_filename']}", styles['Normal']))
    story.append(Paragraph(f"<b>Interview Date:</b> {session['start_time'][:10]}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Metrics Summary
    story.append(Paragraph("<b>Performance Metrics:</b>", styles['Heading2']))
    metrics_table_data = [
        ['Metric', 'Score'],
        ['Attention', f"{session['metrics']['attention']}%"],
        ['Positivity', f"{session['metrics']['positivity']}%"],
        ['Confidence', f"{session['metrics']['confidence']}%"]
    ]
    
    metrics_table = Table(metrics_table_data, colWidths=[2*inch, 1*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 20))
    
    # Q&A Section
    story.append(Paragraph("<b>Interview Questions & Answers:</b>", styles['Heading2']))
    
    for i, qa in enumerate(session['answers'], 1):
        story.append(Paragraph(f"<b>Question {i}:</b> {qa['question']}", styles['Normal']))
        story.append(Paragraph(f"<b>Answer:</b> {qa['answer']}", styles['Normal']))
        story.append(Spacer(1, 12))
    
    # Overall Assessment
    story.append(Paragraph("<b>Overall Assessment:</b>", styles['Heading2']))
    avg_score = (session['metrics']['attention'] + session['metrics']['positivity'] + session['metrics']['confidence']) / 3
    
    if avg_score >= 90:
        assessment = "Excellent performance! The candidate demonstrated strong communication skills and relevant experience."
    elif avg_score >= 80:
        assessment = "Good performance! The candidate showed solid understanding and relevant experience."
    elif avg_score >= 70:
        assessment = "Fair performance. The candidate has potential but could benefit from more practice."
    else:
        assessment = "Needs improvement. The candidate should focus on providing more detailed and specific examples."
    
    story.append(Paragraph(assessment, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    return buffer

if __name__ == '__main__':
    print("Starting Flask AI Interview Backend...")
    print("Available endpoints:")
    print("- POST /start_interview")
    print("- POST /submit_answer")
    print("- GET /get_report")
    print("- GET /get_metrics")
    print("- GET /health")
    app.run(debug=True, host='0.0.0.0', port=5000) 
