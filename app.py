from flask import Flask, request, jsonify, render_template, session
import requests
import random

app = Flask(__name__)
app.secret_key = "mindfriend_seguridad_total"

def ask_ai(user_message, history):
    # Filtro de seguridad inmediato (Capa 0)
    palabras_criticas = ["suicidar", "morir", "matar", "hacerme daño", "quitarme la vida"]
    if any(palabra in user_message.lower() for palabra in palabras_criticas):
        return "ALERTA_CRISIS"

    # Construir historial limpio para evitar amnesia (Capa 1)
    contexto = ""
    for chat in history[-4:]:
        role = "Amigo" if chat['role'] == "MindFriend" else "Usuario"
        contexto += f"{role}: {chat['content']}\n"

    # Prompt con instrucciones anti-bucles (Capa 2)
    system_prompt = f"""
    Eres MindFriend, el mejor amigo de un estudiante. Hablas de forma breve y humana.
    
    CONTEXTO ANTERIOR:
    {contexto}
    
    REGLAS:
    1. Si ya preguntaste algo en el contexto, NO lo vuelvas a preguntar. 
    2. Si el usuario te responde algo específico (como un gusto musical), acéptalo y sigue la plática.
    3. Si detectas una crisis emocional muy grave, responde solo con: ALERTA_CRISIS.
    
    Usuario: {user_message}
    MindFriend:"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma3:1b", 
                "prompt": system_prompt,
                "stream": False,
                "options": {"temperature": 0.5, "num_predict": 120}
            },
            timeout=12
        )
        if response.status_code == 200:
            return response.json().get("response", "").strip()
    except:
        return "Oye, me perdí un segundo, pero aquí sigo contigo. ¿Qué me decías?"

@app.route("/")
def home():
    session['chat_history'] = []
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    history = session['chat_history']
    reply = ask_ai(user_message, history)
    
    # Guardar en memoria para evitar que olvide el tema
    history.append({"role": "Usuario", "content": user_message})
    history.append({"role": "MindFriend", "content": reply})
    session['chat_history'] = history
    session.modified = True 
    
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)