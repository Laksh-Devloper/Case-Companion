# chat/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import ChatMessage
import google.generativeai as genai
import json
from pathlib import Path

@login_required
def chat_room(request):
    # Configure Gemini API
    API_KEY = "AIzaSyADjOZy8ZrnvoHo-syfNcW_VT0_5Vln1Nw"
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }
    )

    # Load knowledge base
    def load_knowledge_base():
        try:
            knowledge_base_path = Path("C:\\Users\\Lakshya Bhawsar\\Desktop\\case_companion\\chat\\bns.json")
            with open(knowledge_base_path, "r", encoding="utf-8") as f:
                parts = json.load(f)
            knowledge_base = []
            for i in range(0, len(parts), 2):
                input_text = parts[i]["text"].replace("input: ", "")
                output = parts[i + 1]["text"].replace("output: ", "").strip() if i + 1 < len(parts) else None
                if output:
                    knowledge_base.append(f"Q: {input_text} A: {output}")
            return "\n".join(knowledge_base)
        except Exception as e:
            print(f"Error loading bns.json: {str(e)}")
            return ""

    knowledge_base = load_knowledge_base()
    conversation_history = request.session.get('chat_history', [])

    if request.method == 'POST':
        message = request.POST.get('message')
        if message:
            # Build history context
            history_context = "\n".join(
                f"Q: {entry['query']} A: {entry['answer']}"
                for entry in conversation_history
            )

            # Construct prompt
            prompt = (
                "You are an expert AI whose name is Case Companion. Provide Guidance to the user how he can fight a case legally and what tips he should follow in a particular situation given. You can talk in Both Language Hindi and English, use hindi if the query tells you to speak in hindi otherwise set default language as english. You have knowledge of bns, Civil Laws, family laws and special laws.\n"
                "Use this knowledge base as your primary source and quote it exactly if the query matches:\n\n"
                f"{knowledge_base}\n\n"
                "Here’s the conversation history:\n\n"
                f"{history_context}\n\n"
                "If the query isn’t in the knowledge base, use your general knowledge to answer naturally.\n\n"
                f"Query: {message}"
            )

            try:
                response = model.generate_content(prompt)
                raw_response = response.text

                # Format the response
                bot_response = format_response(raw_response)
            except Exception as e:
                bot_response = f"<p><strong>Error with AI:</strong> {str(e)}</p>"

            # Save to database
            ChatMessage.objects.create(
                user=request.user,
                message=message,
                bot_response=bot_response
            )

            # Update session history
            conversation_history.append({"query": message, "answer": bot_response})
            request.session['chat_history'] = conversation_history[-10:]  # Keep last 10 for context

    # Get chat history from database
    chat_history = ChatMessage.objects.filter(user=request.user).order_by('timestamp')
    return render(request, 'chat.html', {'chat_history': chat_history})

def format_response(raw_text):
    """Format Gemini's raw text into HTML for better display."""
    # Split into lines
    lines = raw_text.strip().split('\n')
    formatted = []

    for line in lines:
        line = line.strip()
        if not line:
            continue  # Skip empty lines
        elif line.startswith('*') or line.startswith('-'):  # Bullets
            formatted.append(f"<li>{line[1:].strip()}</li>")
        elif line.startswith('Q:') or line.startswith('A:'):  # Q&A from knowledge base
            formatted.append(f"<p><strong>{line[:2]}</strong> {line[2:].strip()}</p>")
        else:  # Paragraphs or headings
            if len(line) < 50 and line.isupper():  # Guessing it's a heading
                formatted.append(f"<h3>{line}</h3>")
            else:
                formatted.append(f"<p>{line}</p>")

    # Wrap bullets in <ul>
    result = []
    in_list = False
    for item in formatted:
        if item.startswith('<li>'):
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append(item)
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append(item)
    if in_list:
        result.append('</ul>')

    return ''.join(result)