from flask import Flask, request, jsonify
import os
import dspy
import logging
import requests
import httpx
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from groq import Groq
from flask_cors import CORS

try:
    from dspy import Example
except ImportError as e:
    print(f"dspy module not found or class definition missing: {e}")
    raise

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/')
def home():
    return "DSPy service est en cours d'exécution !"

# Fonction pour obtenir la date actuelle au format '%Y-%m-%d'
def get_current_date():
    return datetime.now().strftime('%Y-%m-%d')


# Fonction pour obtenir la date d'il y a une semaine
def get_date_one_week_ago():
    one_week_ago = datetime.now() - timedelta(days=7)
    return one_week_ago.strftime('%Y-%m-%d')
#########################################
# Créer un message système détaillé basé sur la requête
def create_system_message(query, search_results, embed_sources=False):
    current_date = get_current_date()
    one_week_ago_date = get_date_one_week_ago()
    template_text = (
        f"Vous êtes un moteur de recherche et un agent conversationnel extrêmement utile, fiable, et perspicace."
        f"Votre mission est de fournir une réponse complète, détaillée, et analytique à la requête de l'utilisateur: \"{query}\"."
        f"Utilisez les résultats de recherche fournis pour créer une réponse riche en détails, en informations récentes, et en analyses pertinentes."
        f"Les informations doivent être comprises entre le {one_week_ago_date} et le {current_date}, et doivent être supportées par des données statistiques et des insights du marché lorsque cela est pertinent."
        f"Assurez-vous d'inclure la date spécifique associée à chaque information ou événement mentionné."
        f"La réponse doit être précise, pertinente, et de haute qualité, en se concentrant sur les points les plus importants, tout en offrant une analyse approfondie."
        f"Rédigez la réponse en français, même si des résultats sont dans une autre langue."
        f"Vous devez citer les résultats de recherche les plus pertinents en réponse à la requête de l'utilisateur."
        f"Ne mentionnez aucun résultat qui ne soit pas directement pertinent pour la requête."
        f"Si possible, intégrez des statistiques, des exemples, et des études de cas pour enrichir la réponse et fournir des informations supplémentaires aux professionnels du secteur."
    )
    if embed_sources:
        template_text += " Retournez les sources utilisées dans la réponse avec des annotations de style markdown numérotées de manière itérative.numérotées de manière séquentielle."
    
    example = Example(text=template_text)
    return example.text

# Créer un message utilisateur pour inclure les résultats de recherche
def create_user_message(results):
    template_text = (
    f"Voici les meilleurs résultats d'une recherche de similarité : {results}. "
    f"Utilisez ces informations pour fournir une réponse détaillée, complète, et pertinente à la question posée. "
    f"Incluez toutes les informations importantes, soutenez-les avec des données statistiques ou des insights de marché lorsque cela est pertinent, et ajoutez des explications ou des contextes supplémentaires pour enrichir la réponse. "
    f"Votre réponse doit être bien structurée, rédigée en français, et adaptée à un public professionnel qui recherche des analyses approfondies. "
    f"Assurez-vous que chaque point est clair, précis, et directement lié à la question. "
    f"Intégrez les sources dans votre réponse sous forme de références claires et précises, en utilisant un format de style markdown."

)
    example = Example(text=template_text)
    return example.text

# Créer des questions de suivi basées sur la requête et les sources
def create_followup_questions_message(query, sources):
    template_text = f"Générez 3 questions de suivi basées sur le texte suivant : {sources}. La requête de recherche initiale est : '{query}'. Retournez les questions au format tableau : ['Question 1', 'Question 2', 'Question 3']"
    example = Example(text=template_text)
    follow_up_questions_text = example.text
    
    followup_questions = follow_up_questions_text.strip("[]").replace("'", "").split(", ")
    
    followup_questions_json = {
        "original": query,
        "followUp": followup_questions
    }
    
    return followup_questions_json

@app.route('/process-system-message', methods=['POST'])
def process_system_message_route():
    data = request.json
    query = data.get('query')
    embed_sources = data.get('embed_sources', True)
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    system_message = create_system_message(query, embed_sources)
    return jsonify({'system_message': system_message})

@app.route('/process-user-message', methods=['POST'])
def process_user_message_route():
    data = request.json
    results = data.get('results')
    if not results:
        return jsonify({'error': 'Results parameter is required'}), 400
    user_message = create_user_message(results)
    return jsonify({'user_message': user_message})

@app.route('/process-followup-questions-message', methods=['POST'])
def process_followup_questions_message_route():
    data = request.json
    query = data.get('query')
    sources = data.get('sources')
    if not query or not sources:
        return jsonify({'error': 'Query and sources parameters are required'}), 400
    followup_questions_message = create_followup_questions_message(query, sources)
    return jsonify(followup_questions_message)

@app.route('/process-query', methods=['POST'])
def process_query_route():
    data = request.json
    query = data.get('query')
    category = data.get('category')
    if not query or not category:
        return jsonify({'error': 'Query and category parameters are required'}), 400
    
    # Map the category to a specific template text
    category_map = {
        "market_trends": "Tendances du marché : ",
        "competitor_activity": "Activités des concurrents : ",
        "financial_performance": "Performances financières : ",
        "marketing_strategies": "Stratégies marketing et commerciales : ",
        "partnerships_collaborations": "Partenariats et collaborations : ",
        "startups_innovations": "Startups et innovations : ",
        "market_opportunities": "Opportunités de marché : ",
        "threats": "Risques et menaces : ",
        "hr_trends": "Tendances RH : ",
        "recruitment_training": "Recrutement et formation : ",
        "upcoming_events": "Événements à venir : ",
        "event_reviews": "Retour sur événements : "
    }
    
    if category not in category_map:
        return jsonify({'error': 'Invalid category parameter'}), 400
    
    template_text = category_map[category] + query
    system_message = create_system_message(template_text, embed_sources=True)
    return jsonify({'message': system_message})




#########################################

SERPER_API_KEY = os.getenv("SERPER_API")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

def load_categories():
    with open("categories.json", "r", encoding="utf-8") as file:
        return json.load(file)

categories = load_categories()

def fetch_images(query):
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "q": query
    }
    try:
        response = httpx.post("https://google.serper.dev/images", json=payload, headers=headers)
        response.raise_for_status()
        images = response.json().get('images', [])
        return images
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def fetch_news(query):
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "q": query,
        "gl": "fr",
        "hl": "fr",
        "tbs": "qdr:w"
    }
    try:
        response = httpx.post("https://google.serper.dev/search", json=payload, headers=headers)
        response.raise_for_status()
        articles = response.json().get('organic', [])
        
        images = fetch_images(query)
        image_index = 0
        
        for article in articles:
            if image_index < len(images):
                article['image'] = images[image_index].get('thumbnailUrl')
                image_index += 1
            else:
                article['image'] = None
        
        return articles
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

@app.route('/api/news', methods=['GET'])
def get_news():
    news_results = {category: [] for category in categories}
    with ThreadPoolExecutor() as executor:
        future_to_category = {
            executor.submit(fetch_news, query): category
            for category, queries in categories.items()
            for query in queries
        }
        for future in as_completed(future_to_category):
            category = future_to_category[future]
            try:
                articles = future.result()
                for article in articles[:6]:
                    title_and_desc = generate_summary(article["snippet"])
                    if title_and_desc:
                        title, *desc_lines = title_and_desc.split('\n')
                        description = ' '.join(desc_lines)
                        news_results[category].append({
                            "title": title,
                            "description": description,
                            "link": article["link"],
                            "image": article["image"]
                        })
            except Exception as e:
                print(f"Error processing query results for category '{category}': {e}")
                news_results[category].append({
                    "title": "Service Unavailable",
                    "description": "The news service is currently unavailable. Please try again later.",
                    "link": "#",
                    "image": None
                })
    return jsonify(news_results)



def generate_summary(article_snippet):
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {
                    "role": "user",
                    "content": (f"Voici un extrait d'article : \"{article_snippet}\". "
                                f"Répondez en français avec un titre et une description complète et concise."
                                f"la description elle doit être résumée et ne doit pas dépasser 100 Tokens."
                                f"N'incluez aucune note ou source dans la description. "
                                f"N'incluez aucune note dans titre. "
                                f"Les informations doivent être récentes, datées entre {get_date_one_week_ago()} et {get_current_date()}. "
                                f"Si vous ne trouvez aucun résultat pertinent, répondez par \"Aucun résultat pertinent trouvé\".")
                }
            ],
            temperature=1,
            top_p=1,
            stream=False,
            stop=None,
        )
        result = completion.choices[0].message.content.strip()
        result = result.replace('**', '').replace('"', '').replace('Titre :', '').replace('Description :', '').strip()  # Remove unwanted characters
        return result
    except Exception as e:
        print(f"An error occurred: {e}")
        return None




@app.route('/api/categories', methods=['GET'])
def get_categories():
    return jsonify(list(categories.keys()))

if __name__ == '__main__':
    app.run(debug=True)