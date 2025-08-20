# import asyncio
# import json
# import os
# import logging
# import requests
# import mysql.connector
# from typing import Dict, Any, List, Optional
# from dataclasses import dataclass
# from dotenv import load_dotenv
# from datetime import datetime, timedelta

# # Charge les variables d'environnement
# load_dotenv('.env')

# # Import MCP
# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client

# # Configuration du logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# @dataclass
# class EmailMessage:
#     """Structure pour représenter un email"""
#     id: str
#     subject: str
#     sender: str
#     body: str
#     date: str

# @dataclass
# class LeaveRequest:
#     """Structure pour représenter une demande de congé"""
#     leave_id: Optional[int] = None
#     employee_id: int = None
#     manager_id: int = None
#     start_date: str = None
#     end_date: str = None
#     type: str = None
#     status: str = "Pending"
#     created_at: Optional[str] = None

# class DatabaseManager:
#     """Gestionnaire de base de données pour les demandes de congé"""
    
#     def __init__(self):
#         self.connection = None
#         self.config = self._load_db_config()
#         self.connect()
    
#     def _load_db_config(self) -> Dict[str, str]:
#         """Charge la configuration de la base de données depuis .env"""
#         config = {
#             'host': os.getenv("DB_HOST"),
#             'port': int(os.getenv("DB_PORT", "3306")),
#             'user': os.getenv("DB_USER"),
#             'password': os.getenv("DB_PASSWORD"),
#             'database': os.getenv("DB_NAME"),
#             'charset': 'utf8mb4',
#             'collation': 'utf8mb4_unicode_ci',
#             'autocommit': True,
#             'use_unicode': True
#         }
        
#         # Vérification des paramètres obligatoires
#         required_params = ['host', 'user', 'password', 'database']
#         missing_params = [param for param in required_params if not config.get(param)]
        
#         if missing_params:
#             logger.error(f"❌ Paramètres DB manquants dans .env: {missing_params}")
#             logger.info("📝 Ajoutez ces variables à votre fichier .env:")
#             logger.info("DB_HOST=votre_host_sql")
#             logger.info("DB_PORT=3306")
#             logger.info("DB_USER=votre_username")
#             logger.info("DB_PASSWORD=votre_password")
#             logger.info("DB_NAME=votre_database_name")
#             raise ValueError(f"Configuration DB incomplète: {missing_params}")
        
#         logger.info(f"✅ Configuration DB chargée: {config['host']}:{config['port']}/{config['database']}")
#         return config
    
#     def connect(self):
#         """Établit la connexion à la base de données"""
#         try:
#             self.connection = mysql.connector.connect(**self.config)
#             logger.info(f"✅ Connexion à la base de données établie: {self.config['host']}")
            
#             # Test de la connexion
#             cursor = self.connection.cursor()
#             cursor.execute("SELECT 1")
#             cursor.fetchone()
#             cursor.close()
#             logger.info("✅ Test de connexion DB réussi")
            
#         except mysql.connector.Error as e:
#             logger.error(f"❌ Erreur connexion DB: {e}")
#             logger.error(f"🔧 Vérifiez vos paramètres DB dans .env:")
#             logger.error(f"   Host: {self.config.get('host', 'NON DÉFINI')}")
#             logger.error(f"   Port: {self.config.get('port', 'NON DÉFINI')}")
#             logger.error(f"   User: {self.config.get('user', 'NON DÉFINI')}")
#             logger.error(f"   Database: {self.config.get('database', 'NON DÉFINI')}")
#             raise
    
#     def ensure_connection(self):
#         """Vérifie et rétablit la connexion si nécessaire"""
#         try:
#             if not self.connection or not self.connection.is_connected():
#                 self.connect()
#         except Exception as e:
#             logger.error(f"❌ Erreur reconnexion DB: {e}")
#             raise
    
#     def insert_leave_request(self, leave_request: LeaveRequest) -> int:
#         """Insère une nouvelle demande de congé"""
#         try:
#             self.ensure_connection()
#             cursor = self.connection.cursor()
            
#             query = """
#             INSERT INTO leave_requests 
#             (employee_id, manager_id, start_date, end_date, type, status) 
#             VALUES (%s, %s, %s, %s, %s, %s)
#             """
            
#             values = (
#                 leave_request.employee_id,
#                 leave_request.manager_id,
#                 leave_request.start_date,
#                 leave_request.end_date,
#                 leave_request.type,
#                 leave_request.status
#             )
            
#             cursor.execute(query, values)
#             self.connection.commit()
            
#             leave_id = cursor.lastrowid
#             cursor.close()
            
#             logger.info(f"✅ Demande de congé insérée avec ID: {leave_id}")
#             return leave_id
            
#         except mysql.connector.Error as e:
#             logger.error(f"❌ Erreur insertion DB: {e}")
#             raise
    
#     def update_leave_status(self, leave_id: int, status: str) -> bool:
#         """Met à jour le statut d'une demande de congé"""
#         try:
#             self.ensure_connection()
#             cursor = self.connection.cursor()
            
#             query = "UPDATE leave_requests SET status = %s WHERE leave_id = %s"
#             cursor.execute(query, (status, leave_id))
#             self.connection.commit()
            
#             affected_rows = cursor.rowcount
#             cursor.close()
            
#             if affected_rows > 0:
#                 logger.info(f"✅ Statut mis à jour pour leave_id {leave_id}: {status}")
#                 return True
#             else:
#                 logger.warning(f"⚠️ Aucune ligne mise à jour pour leave_id {leave_id}")
#                 return False
                
#         except mysql.connector.Error as e:
#             logger.error(f"❌ Erreur mise à jour DB: {e}")
#             raise
    
#     def get_leave_request(self, leave_id: int) -> Optional[LeaveRequest]:
#         """Récupère une demande de congé par son ID"""
#         try:
#             self.ensure_connection()
#             cursor = self.connection.cursor(dictionary=True)
            
#             query = "SELECT * FROM leave_requests WHERE leave_id = %s"
#             cursor.execute(query, (leave_id,))
#             result = cursor.fetchone()
#             cursor.close()
            
#             if result:
#                 return LeaveRequest(**result)
#             return None
            
#         except mysql.connector.Error as e:
#             logger.error(f"❌ Erreur récupération DB: {e}")
#             raise
    
#     def get_pending_requests_by_employee(self, employee_id: int) -> List[LeaveRequest]:
#         """Récupère les demandes en attente d'un employé"""
#         try:
#             self.ensure_connection()
#             cursor = self.connection.cursor(dictionary=True)
            
#             query = """
#             SELECT * FROM leave_requests 
#             WHERE employee_id = %s AND status = 'Pending' 
#             ORDER BY created_at DESC
#             """
#             cursor.execute(query, (employee_id,))
#             results = cursor.fetchall()
#             cursor.close()
            
#             return [LeaveRequest(**row) for row in results]
            
#         except mysql.connector.Error as e:
#             logger.error(f"❌ Erreur récupération demandes: {e}")
#             raise
    
#     def close(self):
#         """Ferme la connexion à la base de données"""
#         if self.connection and self.connection.is_connected():
#             self.connection.close()
#             logger.info("🔌 Connexion DB fermée")

# class SmartGmailAgent:
#     """Agent Gmail Intelligent avec Interface par Prompt et Base de Données"""
    
#     def __init__(self):
#         self.session: ClientSession = None
#         self.connected = False
#         self.gemini_model = None
#         self._connection = None
#         self._session_context = None
        
#         # Base de données
#         self.db = DatabaseManager()
        
#         # Email du CEO (fixe)
#         self.ceo_email = "nassim.younes@ensi-uma.tn"
#         self.ceo_employee_id = 1  # ID du CEO dans la table employees
        
#         # Extraction automatique du nom du CEO depuis l'email
#         self.ceo_name = self._extract_ceo_name_from_email(self.ceo_email)
        
#         # Configuration des APIs
#         self.setup_gemini()
#         self.setup_search_api()
    
#     def _extract_ceo_name_from_email(self, email: str) -> str:
#         """Extrait le nom et prénom du CEO à partir de son adresse email"""
#         try:
#             username = email.split('@')[0]
#             parts = username.replace('.', ' ').replace('-', ' ').replace('_', ' ').split()
#             formatted_parts = [part.capitalize() for part in parts if part]
            
#             if len(formatted_parts) >= 2:
#                 return f"{formatted_parts[0]} {formatted_parts[1]}"
#             elif len(formatted_parts) == 1:
#                 return formatted_parts[0].capitalize()
#             else:
#                 return "Monsieur le CEO"
                
#         except Exception as e:
#             logger.warning(f"⚠️ Erreur extraction nom CEO: {e}")
#             return "Monsieur le CEO"
    
#     def _get_current_date_formatted(self) -> str:
#         """Retourne la date actuelle formatée en français"""
#         try:
#             now = datetime.now()
#             mois_fr = ["", "janvier", "février", "mars", "avril", "mai", "juin",
#                       "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
#             jours_fr = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
            
#             jour_semaine = jours_fr[now.weekday()]
#             jour = now.day
#             mois = mois_fr[now.month]
#             annee = now.year
            
#             return f"{jour_semaine} {jour} {mois} {annee}"
#         except Exception as e:
#             logger.warning(f"⚠️ Erreur formatage date: {e}")
#             return datetime.now().strftime("%d/%m/%Y")
    
#     def setup_gemini(self):
#         """Configure le client Gemini"""
#         gemini_key = os.getenv("GEMINI_API_KEY")
#         if gemini_key:
#             try:
#                 import google.generativeai as genai
#                 genai.configure(api_key=gemini_key)
                
#                 models_to_try = ['gemini-2.5-flash']
                
#                 self.gemini_model = None
#                 for model_name in models_to_try:
#                     try:
#                         self.gemini_model = genai.GenerativeModel(model_name)
#                         test_response = self.gemini_model.generate_content("Hello")
#                         if test_response.text:
#                             logger.info(f"✅ Client Gemini configuré avec le modèle: {model_name}")
#                             break
#                     except Exception as e:
#                         logger.debug(f"Modèle {model_name} non disponible: {e}")
#                         continue
                        
#             except ImportError:
#                 logger.warning("⚠️ Module google-generativeai non installé")
#             except Exception as e:
#                 logger.error(f"❌ Erreur configuration Gemini: {e}")
#         else:
#             logger.warning("⚠️ Clé GEMINI_API_KEY non trouvée dans .env")
    
#     def setup_search_api(self):
#         """Configure les APIs de recherche et météo"""
#         self.openweather_api_key = os.getenv("OPENWEATHER_API_KEY")
#         if self.openweather_api_key:
#             self.weather_enabled = True
#             logger.info("✅ API OpenWeather configurée")
#         else:
#             self.weather_enabled = False
#             logger.warning("⚠️ Clé OPENWEATHER_API_KEY non trouvée dans .env")
        
#         self.search_enabled = True
#         logger.info("✅ Recherche web configurée")
    
#     async def connect_to_mcp_server(self, server_script: str = "mcp_gmail_server.py"):
#         """Se connecte au serveur MCP Gmail"""
#         try:
#             logger.info("🚀 Connexion au serveur MCP Gmail...")
            
#             server_params = StdioServerParameters(
#                 command="python",
#                 args=[server_script],
#                 env=None
#             )
            
#             self._connection = stdio_client(server_params)
#             read, write = await self._connection.__aenter__()
            
#             self._session_context = ClientSession(read, write)
#             self.session = await self._session_context.__aenter__()
            
#             self.connected = True
#             logger.info("✅ Connecté au serveur MCP Gmail")
            
#             await self.session.initialize()
#             return self.session
                    
#         except Exception as e:
#             logger.error(f"❌ Erreur de connexion MCP: {e}")
#             self.connected = False
#             raise
    
#     def search_web(self, query: str) -> str:
#         """Effectue une recherche web simple avec DuckDuckGo"""
#         try:
#             url = f"https://api.duckduckgo.com/"
#             params = {
#                 'q': query,
#                 'format': 'json',
#                 'no_html': '1',
#                 'skip_disambig': '1'
#             }
            
#             response = requests.get(url, params=params, timeout=10)
#             data = response.json()
            
#             abstract = data.get('Abstract', '')
#             answer = data.get('Answer', '')
            
#             if answer:
#                 return f"Réponse directe: {answer}"
#             elif abstract:
#                 return f"Information trouvée: {abstract}"
#             else:
#                 return f"Recherche effectuée pour: {query} - Consultez les sources d'actualités locales"
                
#         except Exception as e:
#             logger.error(f"❌ Erreur de recherche web: {e}")
#             return f"Impossible d'effectuer la recherche pour: {query}"

#     def get_weather_from_openweather(self, city: str = "Tunis") -> Dict[str, Any]:
#         """Récupère les données météo depuis OpenWeatherMap API"""
#         if not self.weather_enabled or not self.openweather_api_key:
#             return {"error": "API OpenWeather non configurée"}
        
#         try:
#             current_url = f"https://api.openweathermap.org/data/2.5/weather"
#             forecast_url = f"https://api.openweathermap.org/data/2.5/forecast"
            
#             params = {
#                 'q': f"{city},TN",
#                 'appid': self.openweather_api_key,
#                 'units': 'metric',
#                 'lang': 'fr'
#             }
            
#             current_response = requests.get(current_url, params=params, timeout=10)
            
#             if current_response.status_code == 200:
#                 current_data = current_response.json()
#                 forecast_response = requests.get(forecast_url, params=params, timeout=10)
#                 forecast_data = forecast_response.json() if forecast_response.status_code == 200 else None
                
#                 return {
#                     "current": current_data,
#                     "forecast": forecast_data,
#                     "success": True
#                 }
#             else:
#                 logger.error(f"Erreur OpenWeather API: {current_response.status_code}")
#                 return {
#                     "error": f"Erreur API météo (Code: {current_response.status_code})",
#                     "success": False
#                 }
                
#         except requests.exceptions.Timeout:
#             logger.error("Timeout OpenWeather API")
#             return {"error": "Délai d'attente dépassé pour la météo", "success": False}
#         except Exception as e:
#             logger.error(f"Erreur OpenWeather: {e}")
#             return {"error": f"Erreur météo: {str(e)}", "success": False}
    
#     async def get_weather_info(self, city: str = "Tunis") -> str:
#         """Récupère et formate les informations météo"""
#         weather_data = self.get_weather_from_openweather(city)
        
#         if not weather_data.get("success", False):
#             return f"❌ {weather_data.get('error', 'Erreur inconnue')}"
        
#         try:
#             current = weather_data["current"]
#             forecast = weather_data.get("forecast")
            
#             temp = current["main"]["temp"]
#             feels_like = current["main"]["feels_like"]
#             humidity = current["main"]["humidity"]
#             description = current["weather"][0]["description"]
#             wind_speed = current["wind"]["speed"]
            
#             result = f"""📍 {current["name"]}, Tunisie
# 🌡️ Température: {temp}°C (ressenti {feels_like}°C)
# ☁️ Conditions: {description.title()}
# 💨 Vent: {wind_speed} m/s
# 💧 Humidité: {humidity}%"""
            
#             if forecast and "list" in forecast:
#                 result += "\n\n🔮 Prévisions courtes:"
#                 for i, item in enumerate(forecast["list"][:3]):
#                     dt = datetime.fromtimestamp(item["dt"])
#                     temp_forecast = item["main"]["temp"]
#                     desc_forecast = item["weather"][0]["description"]
#                     result += f"\n• {dt.strftime('%H:%M')}: {temp_forecast}°C, {desc_forecast}"
            
#             return result
            
#         except KeyError as e:
#             logger.error(f"Erreur parsing météo: {e}")
#             return f"❌ Erreur lors de l'analyse des données météo: {e}"
    
#     async def send_email(self, subject: str, body: str) -> bool:
#         """Envoie un email au CEO"""
#         if not self.connected or not self.session:
#             raise Exception("Pas connecté au serveur MCP")
            
#         try:
#             logger.info(f"✉️ Envoi d'email au CEO: {self.ceo_email}")
            
#             result = await self.session.call_tool(
#                 "gmail_send_message",
#                 arguments={
#                     "to": self.ceo_email,
#                     "subject": subject,
#                     "body": body
#                 }
#             )
            
#             logger.info(f"✅ Email envoyé au CEO")
#             return True
            
#         except Exception as e:
#             logger.error(f"❌ Erreur lors de l'envoi: {e}")
#             return False
    
#     async def check_ceo_replies(self):
#         """Vérifie les réponses du CEO et met à jour les statuts des demandes"""
#         if not self.connected or not self.session:
#             logger.warning("⚠️ Pas connecté au serveur MCP pour vérifier les réponses")
#             return
        
#         try:
#             # Récupère les emails récents du CEO
#             result = await self.session.call_tool(
#                 "gmail_list_messages",
#                 arguments={
#                     "query": f"from:{self.ceo_email}",
#                     "max_results": 10
#                 }
#             )
            
#             if result and hasattr(result, 'content'):
#                 emails = json.loads(result.content[0].text) if result.content else []
                
#                 for email in emails:
#                     await self._process_ceo_reply(email)
                    
#         except Exception as e:
#             logger.error(f"❌ Erreur vérification réponses CEO: {e}")
    
#     async def _process_ceo_reply(self, email: dict):
#         """Traite une réponse du CEO et met à jour le statut de la demande"""
#         try:
#             subject = email.get('subject', '')
#             body = email.get('body', '')
            
#             # Recherche d'un ID de demande dans le sujet ou le corps
#             leave_id = self._extract_leave_id_from_email(subject, body)
            
#             if not leave_id:
#                 logger.debug(f"Aucun ID de demande trouvé dans l'email: {subject}")
#                 return
            
#             # Vérifier que la demande existe et est en Pending
#             leave_request = self.db.get_leave_request(leave_id)
#             if not leave_request or leave_request.status != "Pending":
#                 logger.debug(f"Demande {leave_id} non trouvée ou déjà traitée")
#                 return
            
#             # Analyse de la réponse du CEO avec Gemini
#             if self.gemini_model:
#                 analysis_prompt = f"""
# Analyse cette réponse du CEO concernant une demande de congé et détermine si c'est:
# - APPROVED (approuvé) - mots comme: approuvé, accepté, d'accord, oui, OK, validé, autorisé
# - REJECTED (rejeté) - mots comme: refusé, rejeté, non, impossible, pas d'accord, refus
# - UNCLEAR (pas clair) - réponse ambiguë ou demande de clarification

# EMAIL DU CEO:
# Sujet: {subject}
# Corps: {body}

# Analyse le ton et le contenu. Même si c'est poli, "non" = REJECTED.

# Réponds UNIQUEMENT par: APPROVED, REJECTED, ou UNCLEAR
# """
                
#                 analysis = self.gemini_model.generate_content(analysis_prompt)
#                 decision = analysis.text.strip().upper() if analysis.text else "UNCLEAR"
                
#                 if decision in ["APPROVED", "REJECTED"]:
#                     status = "Approved" if decision == "APPROVED" else "Rejected"
                    
#                     # Met à jour la base de données
#                     success = self.db.update_leave_status(leave_id, status)
                    
#                     if success:
#                         logger.info(f"✅ Demande #{leave_id} mise à jour: {status}")
#                         logger.info(f"📧 Réponse CEO analysée: {decision}")
#                     else:
#                         logger.warning(f"⚠️ Échec mise à jour demande #{leave_id}")
#                 else:
#                     logger.info(f"🤔 Réponse CEO pas claire pour demande #{leave_id}: {decision}")
                
#         except Exception as e:
#             logger.error(f"❌ Erreur traitement réponse CEO: {e}")
    
#     def _extract_leave_id_from_email(self, subject: str, body: str) -> Optional[int]:
#         """Extrait l'ID de demande de congé depuis un email"""
#         import re
        
#         text = f"{subject} {body}"
        
#         # Recherche de patterns comme "demande #123", "leave_id: 123", etc.
#         patterns = [
#             r'demande[:\s#]*(\d+)',
#             r'leave[_\s]*id[:\s]*(\d+)',
#             r'ID[:\s]*(\d+)',
#             r'#(\d+)',
#             r'demande\s*(\d+)',
#             r'request[:\s#]*(\d+)'
#         ]
        
#         for pattern in patterns:
#             match = re.search(pattern, text, re.IGNORECASE)
#             if match:
#                 return int(match.group(1))
        
#         return None
    
#     def _create_leave_request_from_info(self, parsed_info: Dict[str, str], original_request: str) -> LeaveRequest:
#         """Crée un objet LeaveRequest à partir des informations analysées"""
#         # ID employé par défaut (à adapter selon votre système)
#         default_employee_id = int(os.getenv("DEFAULT_EMPLOYEE_ID", "2"))
        
#         # Parse les dates
#         start_date = self._parse_date(parsed_info.get('DATE', ''))
#         end_date = start_date  # Même jour par défaut
        
#         # Détermine le type de congé
#         reason = parsed_info.get('REASON', '').lower()
#         leave_type = "Personal"  # Défaut
        
#         if any(word in reason for word in ['maladie', 'malade', 'médical', 'santé']):
#             leave_type = "Sick"
#         elif any(word in reason for word in ['vacances', 'congé', 'repos']):
#             leave_type = "Vacation"
#         elif any(word in reason for word in ['grève', 'perturbation', 'transport', 'météo']):
#             leave_type = "Disruption"
        
#         return LeaveRequest(
#             employee_id=default_employee_id,
#             manager_id=self.ceo_employee_id,
#             start_date=start_date,
#             end_date=end_date,
#             type=leave_type,
#             status="Pending"
#         )
    
#     def _parse_date(self, date_str: str) -> str:
#         """Parse une date depuis le texte et retourne au format YYYY-MM-DD"""
#         if not date_str or date_str == "Non spécifiée":
#             return datetime.now().strftime("%Y-%m-%d")
        
#         try:
#             # Gestion des mots-clés français
#             date_str_lower = date_str.lower()
#             now = datetime.now()
            
#             if "aujourd'hui" in date_str_lower or "aujourd hui" in date_str_lower:
#                 return now.strftime("%Y-%m-%d")
#             elif "demain" in date_str_lower:
#                 return (now + timedelta(days=1)).strftime("%Y-%m-%d")
#             elif "après-demain" in date_str_lower or "apres demain" in date_str_lower:
#                 return (now + timedelta(days=2)).strftime("%Y-%m-%d")
            
#             # Essaie plusieurs formats
#             formats = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m", "%d-%m"]
            
#             for fmt in formats:
#                 try:
#                     if fmt in ["%d/%m", "%d-%m"]:
#                         # Ajoute l'année courante
#                         date_str_with_year = f"{date_str}/{now.year}"
#                         parsed_date = datetime.strptime(date_str_with_year, f"{fmt}/%Y")
#                     else:
#                         parsed_date = datetime.strptime(date_str, fmt)
#                     return parsed_date.strftime("%Y-%m-%d")
#                 except ValueError:
#                     continue
            
#             # Si aucun format ne marche, utilise aujourd'hui
#             return now.strftime("%Y-%m-%d")
            
#         except Exception:
#             return datetime.now().strftime("%Y-%m-%d")
    
#     async def process_user_request(self, user_input: str) -> str:
#         """Traite la demande de l'utilisateur et décide quoi faire"""
#         if not self.gemini_model:
#             return "❌ Client Gemini non configuré. Impossible de traiter la demande."
        
#         try:
#             # Vérifie d'abord les réponses du CEO
#             await self.check_ceo_replies()
            
#             # Analyse de l'intention avec Gemini
#             analysis_prompt = f"""
# Analyse cette demande d'un employé et détermine l'action à effectuer:

# DEMANDE: "{user_input}"

# Identifie si c'est:
# 1. ABSENCE - Demande d'absence/congé
# 2. RECHERCHE - Demande d'information (météo, grèves, etc.)  
# 3. EMAIL_CONDITIONNEL - Email à envoyer selon une condition
# 4. EMAIL_SIMPLE - Email simple à envoyer
# 5. AUTRE - Autre type de demande

# Format de réponse OBLIGATOIRE:
# TYPE: [ABSENCE|RECHERCHE|EMAIL_CONDITIONNEL|EMAIL_SIMPLE|AUTRE]
# EMPLOYEE_NAME: [Nom si mentionné, sinon "Non spécifié"]
# REASON: [Raison de l'absence si applicable]
# DATE: [Date si mentionnée, sinon "Non spécifiée"]
# CONDITION: [Condition à vérifier si applicable]
# SEARCH_QUERY: [Requête de recherche si applicable]
# SUBJECT: [Sujet d'email si applicable]
# ACTION_NEEDED: [Description de l'action à effectuer]
# """
            
#             analysis = self.gemini_model.generate_content(analysis_prompt)
#             analysis_text = analysis.text if analysis.text else ""
            
#             # Parse la réponse
#             parsed_info = self._parse_analysis(analysis_text)
            
#             # Exécute l'action selon le type identifié
#             if parsed_info['TYPE'] == 'ABSENCE':
#                 return await self._handle_absence_request(parsed_info, user_input)
#             elif parsed_info['TYPE'] == 'RECHERCHE':
#                 return await self._handle_search_request(parsed_info, user_input)
#             elif parsed_info['TYPE'] == 'EMAIL_CONDITIONNEL':
#                 return await self._handle_conditional_email(parsed_info, user_input)
#             elif parsed_info['TYPE'] == 'EMAIL_SIMPLE':
#                 return await self._handle_simple_email(parsed_info, user_input)
#             else:
#                 return await self._handle_other_request(parsed_info, user_input)
                
#         except Exception as e:
#             logger.error(f"❌ Erreur traitement demande: {e}")
#             return f"❌ Erreur lors du traitement de votre demande: {e}"
    
#     def _parse_analysis(self, analysis_text: str) -> Dict[str, str]:
#         """Parse la réponse d'analyse de Gemini"""
#         parsed = {
#             'TYPE': 'AUTRE',
#             'EMPLOYEE_NAME': 'Non spécifié',
#             'REASON': '',
#             'DATE': 'Non spécifiée',
#             'CONDITION': '',
#             'SEARCH_QUERY': '',
#             'SUBJECT': '',
#             'ACTION_NEEDED': ''
#         }
        
#         for line in analysis_text.split('\n'):
#             for key in parsed.keys():
#                 if line.startswith(f"{key}:"):
#                     parsed[key] = line.replace(f"{key}:", "").strip()
        
#         return parsed
    
#     async def _handle_absence_request(self, info: Dict[str, str], original_request: str) -> str:
#         """Gère une demande d'absence avec insertion en base de données"""
#         try:
#             logger.info("🏠 Traitement demande d'absence")
            
#             # Crée la demande de congé
#             leave_request = self._create_leave_request_from_info(info, original_request)
            
#             # Insère en base de données
#             leave_id = self.db.insert_leave_request(leave_request)
            
#             # Collecte des informations automatiquement
#             employee_name = info['EMPLOYEE_NAME'] if info['EMPLOYEE_NAME'] != 'Non spécifié' else "Employé"
#             reason = info['REASON'] or "Raison personnelle"
#             date = info['DATE'] if info['DATE'] != 'Non spécifiée' else datetime.now().strftime("%d/%m/%Y")
#             location = "Tunis"
            
#             # Recherche contextuelle automatique selon la raison
#             additional_info = ""
#             search_queries = []
            
#             reason_lower = reason.lower()
#             if any(word in reason_lower for word in ['météo', 'temps', 'pluie', 'neige', 'orage', 'intempéries']):
#                 weather_info = await self.get_weather_info(location)
#                 additional_info += f"\n🌤️ Vérification météo OpenWeather: {weather_info}"
            
#             if any(word in reason_lower for word in ['grève', 'manifestation', 'perturbation', 'transport']):
#                 search_queries.append("grèves Tunisie transport aujourd'hui")
#                 search_queries.append("perturbations transport public Tunis")
            
#             if any(word in reason_lower for word in ['catastrophe', 'urgence', 'accident', 'santé']):
#                 search_queries.append("actualités urgentes Tunisie catastrophes")
            
#             if any(word in reason_lower for word in ['covid', 'maladie', 'épidémie', 'virus']):
#                 search_queries.append("situation sanitaire Tunisie aujourd'hui")
            
#             # Effectue les recherches
#             for query in search_queries:
#                 result = self.search_web(query)
#                 additional_info += f"\n🔍 {query}: {result}"
            
#             # Génère l'email avec Gemini
#             current_date = self._get_current_date_formatted()
            
#             email_prompt = f"""
# Rédige un email professionnel de demande d'absence pour:

# INFORMATIONS:
# - Employé: {employee_name}
# - Date d'absence: {date}
# - Raison: {reason}
# - Demande originale: "{original_request}"
# - Recherches effectuées: {additional_info}
# - Date actuelle: {current_date}
# - Destinataire: {self.ceo_name}
# - ID de demande: {leave_id}

# L'email doit être:
# - Professionnel et respectueux
# - Commencer par la date actuelle en haut
# - S'adresser personnellement au CEO par son nom
# - Incluant les informations de contexte pertinentes
# - Incluant l'ID de demande pour suivi
# - Demandant la compréhension
# - Signé par l'employé
# - En français

# IMPORTANT: Respecte EXACTEMENT ce format:

# SUJET: Demande d'absence #{leave_id} - {employee_name} - {date}

# CORPS:
# {current_date}

# Cher Monsieur {self.ceo_name},

# [Corps du message professionnel avec justification et contexte]

# Je vous prie d'agréer, Monsieur {self.ceo_name.split()[-1]}, l'expression de mes sentiments respectueux.

# Cordialement,
# {employee_name}
# """
            
#             email_response = self.gemini_model.generate_content(email_prompt)
#             email_text = email_response.text if email_response.text else ""
            
#             # Parse sujet et corps
#             subject, body = self._parse_email_content(email_text, f"Demande d'absence #{leave_id} - {employee_name}")
            
#             # Envoie l'email
#             success = await self.send_email(subject, body)
            
#             if success:
#                 return f"✅ Email de demande d'absence envoyé au CEO avec succès!\n\n📧 Sujet: {subject}\n🗂️ ID Demande: #{leave_id} (statut: Pending)\n📄 Contenu: {body[:200]}...\n\n💡 Le statut sera automatiquement mis à jour quand le CEO répondra."
#             else:
#                 return f"❌ Erreur lors de l'envoi de l'email, mais demande #{leave_id} créée en base"
                
#         except Exception as e:
#             logger.error(f"❌ Erreur demande absence: {e}")
#             return f"❌ Erreur lors du traitement de la demande d'absence: {e}"
    
#     async def _handle_search_request(self, info: Dict[str, str], original_request: str) -> str:
#         """Gère une demande de recherche"""
#         try:
#             query = info['SEARCH_QUERY'] or original_request
#             logger.info(f"🔍 Recherche: {query}")
            
#             # Détecte si c'est une demande météo
#             query_lower = query.lower()
#             is_weather_query = any(word in query_lower for word in ['météo', 'temps', 'température', 'pluie', 'climat', 'weather'])
            
#             if is_weather_query and self.weather_enabled:
#                 logger.info("🌤️ Demande météo détectée - Utilisation OpenWeather API")
#                 weather_result = await self.get_weather_info("Tunis")
                
#                 if self.gemini_model:
#                     analysis_prompt = f"""
# Analyse ce résultat météo et fournis une réponse claire et utile:

# RECHERCHE: {query}
# DONNÉES MÉTÉO: {weather_result}

# Fournis:
# - Résumé des conditions météo actuelles
# - Prévisions si disponibles
# - Recommandations pratiques
# - Réponse en français, style conversationnel
# """
#                     analysis = self.gemini_model.generate_content(analysis_prompt)
#                     analyzed_result = analysis.text if analysis.text else weather_result
                    
#                     return f"🌤️ Météo pour: {query}\n\n📊 {analyzed_result}"
                
#                 return f"🌤️ Météo: {weather_result}"
#             else:
#                 # Pour les autres recherches, utilise DuckDuckGo
#                 result = self.search_web(query)
                
#                 # Analyse avec Gemini pour une réponse plus claire
#                 if self.gemini_model:
#                     analysis_prompt = f"""
# Analyse ce résultat de recherche et fournis une réponse claire et utile:

# RECHERCHE: {query}
# RÉSULTAT: {result}

# Fournis:
# - Résumé des informations importantes
# - Réponse directe à la question
# - Implications pratiques s'il y en a
# """
#                     analysis = self.gemini_model.generate_content(analysis_prompt)
#                     analyzed_result = analysis.text if analysis.text else result
                    
#                     return f"🔍 Résultat de recherche pour: {query}\n\n📊 {analyzed_result}"
                
#                 return f"🔍 Résultat de recherche pour: {query}\n\n📊 {result}"
            
#         except Exception as e:
#             logger.error(f"❌ Erreur recherche: {e}")
#             return f"❌ Erreur lors de la recherche: {e}"
    
#     async def _handle_conditional_email(self, info: Dict[str, str], original_request: str) -> str:
#         """Gère un email conditionnel"""
#         try:
#             condition = info['CONDITION'] or original_request
#             logger.info(f"🤖 Email conditionnel: {condition}")
            
#             # Effectue la recherche pour vérifier la condition
#             search_result = self.search_web(condition)
            
#             # Demande à Gemini de décider si la condition est remplie
#             decision_prompt = f"""
# Analyse ce résultat et décide si la condition suivante est remplie:

# CONDITION: {condition}
# RÉSULTAT RECHERCHE: {search_result}

# Réponds UNIQUEMENT par:
# - OUI si la condition est clairement remplie
# - NON si la condition n'est pas remplie
# - INCERTAIN s'il n'y a pas assez d'informations

# Puis explique brièvement ta décision.
# """
            
#             decision_response = self.gemini_model.generate_content(decision_prompt)
#             decision_text = decision_response.text if decision_response.text else "INCERTAIN"
            
#             should_send = decision_text.upper().startswith("OUI")
            
#             if should_send:
#                 # Génère et envoie l'email
#                 current_date = self._get_current_date_formatted()
                
#                 email_prompt = f"""
# Rédige un email professionnel au CEO informant de cette situation:

# INFORMATIONS:
# - CONDITION VÉRIFIÉE: {condition}
# - RÉSULTAT: {search_result}
# - ANALYSE: {decision_text}
# - Date actuelle: {current_date}
# - Destinataire: {self.ceo_name}

# IMPORTANT: Respecte EXACTEMENT ce format:

# SUJET: Information urgente - {condition[:50]}

# CORPS:
# {current_date}

# Cher Monsieur {self.ceo_name},

# [Corps du message expliquant la situation et ses implications]

# Cordialement,
# [Nom de l'expéditeur]
# """
                
#                 email_response = self.gemini_model.generate_content(email_prompt)
#                 email_text = email_response.text if email_response.text else ""
                
#                 subject, body = self._parse_email_content(email_text, f"Information urgente - {condition}")
                
#                 success = await self.send_email(subject, body)
                
#                 if success:
#                     return f"✅ Condition remplie! Email envoyé au CEO.\n\n🧠 Analyse: {decision_text}\n📧 Sujet: {subject}"
#                 else:
#                     return f"✅ Condition remplie mais erreur d'envoi.\n🧠 Analyse: {decision_text}"
#             else:
#                 return f"❌ Condition non remplie. Aucun email envoyé.\n\n🧠 Analyse: {decision_text}"
                
#         except Exception as e:
#             logger.error(f"❌ Erreur email conditionnel: {e}")
#             return f"❌ Erreur lors du traitement de l'email conditionnel: {e}"
    
#     async def _handle_simple_email(self, info: Dict[str, str], original_request: str) -> str:
#         """Gère un email simple"""
#         try:
#             logger.info("✉️ Email simple")
            
#             # Génère l'email basé sur la demande
#             current_date = self._get_current_date_formatted()
            
#             email_prompt = f"""
# Rédige un email professionnel basé sur cette demande:

# INFORMATIONS:
# - DEMANDE: "{original_request}"
# - SUJET SUGGÉRÉ: {info['SUBJECT']}
# - Date actuelle: {current_date}
# - Destinataire: {self.ceo_name}

# IMPORTANT: Respecte EXACTEMENT ce format:

# SUJET: {info['SUBJECT'] or 'Email professionnel'}

# CORPS:
# {current_date}

# Cher Monsieur {self.ceo_name},

# [Corps du message professionnel adapté au contexte]

# Cordialement,
# [Nom de l'expéditeur]
# """
            
#             email_response = self.gemini_model.generate_content(email_prompt)
#             email_text = email_response.text if email_response.text else ""
            
#             subject, body = self._parse_email_content(email_text, "Email professionnel")
            
#             success = await self.send_email(subject, body)
            
#             if success:
#                 return f"✅ Email envoyé au CEO avec succès!\n\n📧 Sujet: {subject}\n📄 Contenu: {body[:200]}..."
#             else:
#                 return "❌ Erreur lors de l'envoi de l'email"
                
#         except Exception as e:
#             logger.error(f"❌ Erreur email simple: {e}")
#             return f"❌ Erreur lors de l'envoi de l'email: {e}"
    
#     async def _handle_other_request(self, info: Dict[str, str], original_request: str) -> str:
#         """Gère les autres types de demandes"""
#         try:
#             # Utilise Gemini pour répondre
#             response_prompt = f"""
# Réponds à cette demande d'un employé de manière utile et professionnelle:

# DEMANDE: "{original_request}"

# Si c'est une question, réponds directement.
# Si ça nécessite une action spécifique, explique comment procéder.
# """
            
#             response = self.gemini_model.generate_content(response_prompt)
#             return response.text if response.text else "Je ne suis pas sûr de comprendre votre demande. Pouvez-vous la reformuler ?"
            
#         except Exception as e:
#             logger.error(f"❌ Erreur autre demande: {e}")
#             return f"❌ Erreur lors du traitement de votre demande: {e}"
    
#     def _parse_email_content(self, email_text: str, default_subject: str) -> tuple:
#         """Parse le contenu email généré par Gemini"""
#         lines = email_text.split('\n')
#         subject = default_subject
#         body = ""
#         subject_found = False
#         body_found = False
        
#         for i, line in enumerate(lines):
#             line = line.strip()
            
#             # Cherche le sujet
#             if line.startswith("SUJET:") and not subject_found:
#                 subject = line.replace("SUJET:", "").strip()
#                 subject_found = True
#                 continue
            
#             # Cherche le corps
#             if line.startswith("CORPS:") and not body_found:
#                 # Prend tout ce qui suit "CORPS:" sur les lignes suivantes
#                 body_lines = []
#                 for j in range(i + 1, len(lines)):
#                     body_line = lines[j].strip()
#                     # Ignore les lignes vides au début
#                     if not body_line and not body_lines:
#                         continue
#                     # Arrête si on trouve "OBJET:" dans le corps (erreur de Gemini)
#                     if body_line.startswith("OBJET:"):
#                         continue
#                     body_lines.append(lines[j])  # Garde l'indentation originale
                
#                 body = '\n'.join(body_lines).strip()
#                 body_found = True
#                 break
        
#         # Si pas de structure SUJET:/CORPS: détectée, essaie de parser différemment
#         if not subject_found and not body_found:
#             # Cherche "OBJET:" au lieu de "SUJET:"
#             for i, line in enumerate(lines):
#                 if line.strip().startswith("OBJET:"):
#                     subject = line.replace("OBJET:", "").strip()
#                     # Le reste est le corps
#                     body = '\n'.join(lines[i+1:]).strip()
#                     break
            
#             # Si toujours rien, utilise tout comme corps
#             if not subject.strip() or subject == default_subject:
#                 body = email_text.strip()
#                 # Nettoie le corps des références d'objet
#                 body_lines = []
#                 for line in body.split('\n'):
#                     if not line.strip().startswith("OBJET:") and not line.strip().startswith("SUJET:"):
#                         body_lines.append(line)
#                 body = '\n'.join(body_lines).strip()
        
#         return subject, body
    
#     async def get_leave_status(self, employee_id: int = None) -> str:
#         """Récupère le statut des demandes de congé d'un employé"""
#         try:
#             if not employee_id:
#                 employee_id = int(os.getenv("DEFAULT_EMPLOYEE_ID", "2"))
            
#             pending_requests = self.db.get_pending_requests_by_employee(employee_id)
            
#             if not pending_requests:
#                 return "📋 Aucune demande de congé en attente"
            
#             result = f"📋 Demandes en attente pour l'employé #{employee_id}:\n\n"
            
#             for req in pending_requests:
#                 result += f"🆔 Demande #{req.leave_id}\n"
#                 result += f"📅 Date: {req.start_date}\n"
#                 result += f"📝 Type: {req.type}\n"
#                 result += f"⏳ Statut: {req.status}\n"
#                 result += f"🕐 Créée: {req.created_at}\n"
#                 result += "-" * 30 + "\n"
            
#             return result
            
#         except Exception as e:
#             logger.error(f"❌ Erreur récupération statut: {e}")
#             return f"❌ Erreur lors de la récupération du statut: {e}"
    
#     async def disconnect(self):
#         """Ferme proprement la connexion MCP et DB"""
#         try:
#             if self._session_context:
#                 await self._session_context.__aexit__(None, None, None)
#             if self._connection:
#                 await self._connection.__aexit__(None, None, None)
#             if self.db:
#                 self.db.close()
#             self.connected = False
#             logger.info("🔌 Connexions MCP et DB fermées proprement")
#         except Exception as e:
#             logger.warning(f"⚠️ Erreur lors de la fermeture: {e}")

# async def main():
#     """Interface principale par prompt"""
#     print("🤖 AGENT GMAIL INTELLIGENT AVEC BASE DE DONNÉES")
#     print("=" * 60)
#     print("Tapez vos demandes en langage naturel:")
#     print("• 'Je veux m'absenter demain car il pleut'")
#     print("• 'Vérifie s'il y a des grèves cette semaine'")
#     print("• 'Envoie un email si le météo est mauvais'")
#     print("• 'Quelle est la météo aujourd'hui?'")
#     print("• 'Statut de mes demandes' - voir les demandes en attente")
#     print("• Tapez 'quit' pour quitter")
#     print("=" * 60)
    
#     agent = SmartGmailAgent()
    
#     try:
#         # Connexion au serveur MCP
#         await agent.connect_to_mcp_server("mcp_gmail_server.py")
#         print(f"✅ Agent connecté!")
#         print(f"📧 Emails envoyés à: {agent.ceo_email}")
#         print(f"👤 CEO identifié: {agent.ceo_name}")
#         print(f"📅 Date système: {agent._get_current_date_formatted()}")
#         print(f"🗂️ Base de données: {agent.db.config['host']}/{agent.db.config['database']}")
#         print("-" * 60)
        
#         # Boucle interactive
#         while True:
#             try:
#                 user_input = input("\n💬 Votre demande: ").strip()
                
#                 if user_input.lower() in ['quit', 'exit', 'q', 'quitter']:
#                     print("👋 Au revoir !")
#                     break
                
#                 if user_input.lower() in ['statut', 'status', 'mes demandes']:
#                     print("🤖 Récupération du statut...")
#                     response = await agent.get_leave_status()
#                     print(f"\n📝 Statut:\n{response}")
#                     continue
                
#                 if not user_input:
#                     continue
                
#                 print("🤖 Traitement en cours...")
#                 response = await agent.process_user_request(user_input)
#                 print(f"\n📝 Réponse:\n{response}")
                
#             except KeyboardInterrupt:
#                 print("\n👋 Au revoir !")
#                 break
#             except Exception as e:
#                 print(f"❌ Erreur: {e}")
        
#     except Exception as e:
#         logger.error(f"❌ Erreur fatale: {e}")
#         print(f"❌ Impossible de démarrer l'agent: {e}")
#         print("🔧 Vérifiez:")
#         print("   - mcp_gmail_server.py existe")
#         print("   - Configuration .env complète")
#         print("   - Base de données accessible")
#         print("   - Dépendances installées")
#     finally:
#         if agent.connected:
#             await agent.disconnect()

# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except KeyboardInterrupt:
#         print("\n👋 Programme arrêté")
#     except Exception as e:
#         logger.error(f"❌ Erreur de démarrage: {e}")
#         print(f"❌ Erreur: {e}")














import asyncio
import json
import os
import logging
import requests
import re
from typing import Dict, Any, List
from dataclasses import dataclass
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Charge les variables d'environnement
load_dotenv('.env')

# Import MCP
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class EmailMessage:
    """Structure pour représenter un email"""
    id: str
    subject: str
    sender: str
    body: str
    date: str

@dataclass
class WeatherCondition:
    """Structure pour représenter une condition météorologique"""
    parameter: str  # 'temperature', 'humidity', 'wind_speed'
    operator: str   # '>', '<', '>=', '<=', '='
    value: float
    unit: str      # '°C', '%', 'm/s'

class SmartGmailAgent:
    """Agent Gmail Intelligent avec Interface par Prompt"""
    
    def __init__(self):
        self.session: ClientSession = None
        self.connected = False
        self.gemini_model = None
        self._connection = None
        self._session_context = None
        
        # Email du CEO (fixe)
        self.ceo_email = "nassim.younes@ensi-uma.tn"
        
        # Extraction automatique du nom du CEO depuis l'email
        self.ceo_name = self._extract_ceo_name_from_email(self.ceo_email)
        
        # Configuration des APIs
        self.setup_gemini()
        self.setup_search_api()
    
    def _extract_ceo_name_from_email(self, email: str) -> str:
        """Extrait le nom et prénom du CEO à partir de son adresse email"""
        try:
            # Extrait la partie avant le @
            username = email.split('@')[0]
            
            # Sépare par points ou tirets
            parts = username.replace('.', ' ').replace('-', ' ').replace('_', ' ').split()
            
            # Capitalise chaque partie (prénom et nom)
            formatted_parts = [part.capitalize() for part in parts if part]
            
            if len(formatted_parts) >= 2:
                return f"{formatted_parts[0]} {formatted_parts[1]}"
            elif len(formatted_parts) == 1:
                return formatted_parts[0].capitalize()
            else:
                return "Monsieur le CEO"
                
        except Exception as e:
            logger.warning(f"⚠️ Erreur extraction nom CEO: {e}")
            return "Monsieur le CEO"
    
    def _get_current_date_formatted(self) -> str:
        """Retourne la date actuelle formatée en français"""
        try:
            now = datetime.now()
            
            # Noms des mois en français
            mois_fr = [
                "", "janvier", "février", "mars", "avril", "mai", "juin",
                "juillet", "août", "septembre", "octobre", "novembre", "décembre"
            ]
            
            # Noms des jours en français
            jours_fr = [
                "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"
            ]
            
            jour_semaine = jours_fr[now.weekday()]
            jour = now.day
            mois = mois_fr[now.month]
            annee = now.year
            
            return f"{jour_semaine} {jour} {mois} {annee}"
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur formatage date: {e}")
            return datetime.now().strftime("%d/%m/%Y")
    
    def _parse_date_from_text(self, text: str) -> str:
        """Parse une date depuis du texte en français"""
        try:
            now = datetime.now()
            text_lower = text.lower()
            
            # Jours relatifs
            if "aujourd'hui" in text_lower:
                return now.strftime("%d/%m/%Y")
            elif "demain" in text_lower:
                tomorrow = now + timedelta(days=1)
                return tomorrow.strftime("%d/%m/%Y")
            elif "après-demain" in text_lower or "apres-demain" in text_lower:
                day_after = now + timedelta(days=2)
                return day_after.strftime("%d/%m/%Y")
            
            # Jours de la semaine
            jours_semaine = {
                'lundi': 0, 'mardi': 1, 'mercredi': 2, 'jeudi': 3,
                'vendredi': 4, 'samedi': 5, 'dimanche': 6
            }
            
            for jour_nom, jour_num in jours_semaine.items():
                if jour_nom in text_lower:
                    # Trouve le prochain occurrence de ce jour
                    jours_jusqu_jour = (jour_num - now.weekday()) % 7
                    if jours_jusqu_jour == 0:  # Si c'est aujourd'hui, prend la semaine prochaine
                        jours_jusqu_jour = 7
                    target_date = now + timedelta(days=jours_jusqu_jour)
                    return target_date.strftime("%d/%m/%Y")
            
            # Patterns de date DD/MM ou DD/MM/YYYY
            date_patterns = [
                r'(\d{1,2})/(\d{1,2})/(\d{4})',
                r'(\d{1,2})/(\d{1,2})',
                r'(\d{1,2})-(\d{1,2})-(\d{4})',
                r'(\d{1,2})-(\d{1,2})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    if len(match.groups()) == 3:
                        day, month, year = match.groups()
                        return f"{day.zfill(2)}/{month.zfill(2)}/{year}"
                    else:
                        day, month = match.groups()
                        return f"{day.zfill(2)}/{month.zfill(2)}/{now.year}"
            
            return "Non spécifiée"
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur parsing date: {e}")
            return "Non spécifiée"
    
    def setup_gemini(self):
        """Configure le client Gemini"""
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                
                models_to_try = [
                    'gemini-2.5-flash',
                    'gemini-1.5-flash',
                    'gemini-pro'
                ]
                
                self.gemini_model = None
                for model_name in models_to_try:
                    try:
                        self.gemini_model = genai.GenerativeModel(model_name)
                        test_response = self.gemini_model.generate_content("Hello")
                        if test_response.text:
                            logger.info(f"✅ Client Gemini configuré avec le modèle: {model_name}")
                            break
                    except Exception as e:
                        logger.debug(f"Modèle {model_name} non disponible: {e}")
                        continue
                        
            except ImportError:
                logger.warning("⚠️ Module google-generativeai non installé")
            except Exception as e:
                logger.error(f"❌ Erreur configuration Gemini: {e}")
        else:
            logger.warning("⚠️ Clé GEMINI_API_KEY non trouvée dans .env")
    
    def setup_search_api(self):
        """Configure les APIs de recherche et météo"""
        # Configuration OpenWeather API
        self.openweather_api_key = os.getenv("OPENWEATHER_API_KEY")
        if self.openweather_api_key:
            self.weather_enabled = True
            logger.info("✅ API OpenWeather configurée")
        else:
            self.weather_enabled = False
            logger.warning("⚠️ Clé OPENWEATHER_API_KEY non trouvée dans .env")
        
        # Recherche web simple (DuckDuckGo gratuit)
        self.search_enabled = True
        logger.info("✅ Recherche web configurée")
    
    async def connect_to_mcp_server(self, server_script: str = "mcp_gmail_server.py"):
        """Se connecte au serveur MCP Gmail"""
        try:
            logger.info("🚀 Connexion au serveur MCP Gmail...")
            
            server_params = StdioServerParameters(
                command="python",
                args=[server_script],
                env=None
            )
            
            self._connection = stdio_client(server_params)
            read, write = await self._connection.__aenter__()
            
            self._session_context = ClientSession(read, write)
            self.session = await self._session_context.__aenter__()
            
            self.connected = True
            logger.info("✅ Connecté au serveur MCP Gmail")
            
            await self.session.initialize()
            return self.session
                    
        except Exception as e:
            logger.error(f"❌ Erreur de connexion MCP: {e}")
            self.connected = False
            raise
    
    def search_web(self, query: str) -> str:
        """Effectue une recherche web simple avec DuckDuckGo"""
        try:
            url = f"https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            abstract = data.get('Abstract', '')
            answer = data.get('Answer', '')
            
            if answer:
                return f"Réponse directe: {answer}"
            elif abstract:
                return f"Information trouvée: {abstract}"
            else:
                return f"Recherche effectuée pour: {query} - Consultez les sources d'actualités locales"
                
        except Exception as e:
            logger.error(f"❌ Erreur de recherche web: {e}")
            return f"Impossible d'effectuer la recherche pour: {query}"

    def get_weather_from_openweather(self, city: str = "Tunis", target_date: str = None) -> Dict[str, Any]:
        """Récupère les données météo depuis OpenWeatherMap API"""
        if not self.weather_enabled or not self.openweather_api_key:
            return {"error": "API OpenWeather non configurée"}
        
        try:
            # URL pour les données météo actuelles
            current_url = f"https://api.openweathermap.org/data/2.5/weather"
            
            # URL pour les prévisions
            forecast_url = f"https://api.openweathermap.org/data/2.5/forecast"
            
            params = {
                'q': f"{city},TN",  # TN pour Tunisie
                'appid': self.openweather_api_key,
                'units': 'metric',  # Celsius
                'lang': 'fr'  # Français
            }
            
            # Récupère la météo actuelle
            current_response = requests.get(current_url, params=params, timeout=10)
            
            if current_response.status_code == 200:
                current_data = current_response.json()
                
                # Récupère aussi les prévisions
                forecast_response = requests.get(forecast_url, params=params, timeout=10)
                forecast_data = forecast_response.json() if forecast_response.status_code == 200 else None
                
                return {
                    "current": current_data,
                    "forecast": forecast_data,
                    "success": True
                }
            else:
                logger.error(f"Erreur OpenWeather API: {current_response.status_code}")
                return {
                    "error": f"Erreur API météo (Code: {current_response.status_code})",
                    "success": False
                }
                
        except requests.exceptions.Timeout:
            logger.error("Timeout OpenWeather API")
            return {"error": "Délai d'attente dépassé pour la météo", "success": False}
        except Exception as e:
            logger.error(f"Erreur OpenWeather: {e}")
            return {"error": f"Erreur météo: {str(e)}", "success": False}
    
    def _find_weather_for_date(self, forecast_data: dict, target_date: str) -> dict:
        """Trouve les données météo pour une date spécifique dans les prévisions"""
        if not forecast_data or "list" not in forecast_data:
            return None
            
        try:
            # Parse la date cible
            if target_date == "Non spécifiée":
                return None
                
            target_dt = datetime.strptime(target_date, "%d/%m/%Y")
            
            # Cherche dans les prévisions
            for item in forecast_data["list"]:
                forecast_dt = datetime.fromtimestamp(item["dt"])
                
                # Si c'est le même jour
                if forecast_dt.date() == target_dt.date():
                    return item
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur recherche météo date: {e}")
            return None
    
    def _extract_weather_conditions(self, text: str) -> List[WeatherCondition]:
        """Extrait les conditions météorologiques depuis le texte"""
        conditions = []
        text_lower = text.lower()
        
        try:
            # Patterns pour température
            temp_patterns = [
                r'temp[eé]rature\s*([><=]+)\s*(\d+)(?:\s*degr[eé])?',
                r'temp[eé]rature\s*(d[eé]passe|sup[eé]rieur[e]?\s*[aà]|plus\s*de|au[-\s]dessus\s*de)\s*(\d+)',
                r'temp[eé]rature\s*(inf[eé]rieur[e]?\s*[aà]|moins\s*de|en[-\s]dessous\s*de)\s*(\d+)',
                r'(\d+)\s*degr[eé]s?\s*(ou\s*plus|maximum|mini|au[-\s]moins)',
                r'plus\s*de\s*(\d+)\s*degr[eé]',
                r'moins\s*de\s*(\d+)\s*degr[eé]',
                r's\'il\s*fait\s*(plus|moins)\s*de\s*(\d+)'
            ]
            
            for pattern in temp_patterns:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    groups = match.groups()
                    
                    if len(groups) >= 2:
                        operator_text = groups[0] if not groups[0].isdigit() else groups[1]
                        value_text = groups[1] if not groups[0].isdigit() else groups[0]
                        
                        try:
                            value = float(value_text)
                            
                            # Détermine l'opérateur
                            if any(word in operator_text for word in ['dépasse', 'supérieur', 'plus', 'dessus', 'maximum']):
                                operator = '>'
                            elif any(word in operator_text for word in ['inférieur', 'moins', 'dessous', 'mini']):
                                operator = '<'
                            elif '>' in operator_text:
                                operator = '>'
                            elif '<' in operator_text:
                                operator = '<'
                            elif '=' in operator_text:
                                operator = '='
                            else:
                                operator = '>'  # Par défaut
                            
                            conditions.append(WeatherCondition('temperature', operator, value, '°C'))
                            
                        except ValueError:
                            continue
            
            # Patterns pour humidité
            humidity_patterns = [
                r'humidit[eé]\s*([><=]+)\s*(\d+)',
                r'humidit[eé]\s*(sup[eé]rieur[e]?\s*[aà]|plus\s*de)\s*(\d+)',
                r'plus\s*de\s*(\d+)\s*%\s*d\'humidit[eé]'
            ]
            
            for pattern in humidity_patterns:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    groups = match.groups()
                    if len(groups) >= 2:
                        try:
                            value = float(groups[-1])
                            operator = '>' if 'plus' in groups[0] or '>' in groups[0] else '<'
                            conditions.append(WeatherCondition('humidity', operator, value, '%'))
                        except ValueError:
                            continue
            
            # Patterns pour vent
            wind_patterns = [
                r'vent\s*([><=]+)\s*(\d+)',
                r'vent\s*(fort|faible|sup[eé]rieur\s*[aà])\s*(\d+)?'
            ]
            
            for pattern in wind_patterns:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    groups = match.groups()
                    if len(groups) >= 2:
                        try:
                            value = float(groups[-1]) if groups[-1] and groups[-1].isdigit() else 10.0
                            operator = '>' if 'fort' in groups[0] or '>' in groups[0] else '<'
                            conditions.append(WeatherCondition('wind_speed', operator, value, 'm/s'))
                        except ValueError:
                            continue
            
        except Exception as e:
            logger.error(f"Erreur extraction conditions météo: {e}")
        
        return conditions
    
    def _check_weather_conditions(self, weather_data: dict, conditions: List[WeatherCondition]) -> Dict[str, Any]:
        """Vérifie si les conditions météorologiques sont remplies"""
        if not weather_data.get("success", False) or not conditions:
            return {"conditions_met": False, "details": "Pas de conditions à vérifier"}
        
        results = []
        all_conditions_met = True
        
        try:
            # Utilise les données actuelles par défaut
            data_to_check = weather_data["current"]
            
            for condition in conditions:
                if condition.parameter == 'temperature':
                    actual_value = data_to_check["main"]["temp"]
                elif condition.parameter == 'humidity':
                    actual_value = data_to_check["main"]["humidity"]
                elif condition.parameter == 'wind_speed':
                    actual_value = data_to_check["wind"]["speed"]
                else:
                    continue
                
                # Vérifie la condition
                condition_met = False
                if condition.operator == '>':
                    condition_met = actual_value > condition.value
                elif condition.operator == '<':
                    condition_met = actual_value < condition.value
                elif condition.operator == '>=':
                    condition_met = actual_value >= condition.value
                elif condition.operator == '<=':
                    condition_met = actual_value <= condition.value
                elif condition.operator == '=':
                    condition_met = abs(actual_value - condition.value) < 1.0  # Tolérance de 1
                
                results.append({
                    'parameter': condition.parameter,
                    'expected': f"{condition.operator} {condition.value}{condition.unit}",
                    'actual': f"{actual_value}{condition.unit}",
                    'met': condition_met
                })
                
                if not condition_met:
                    all_conditions_met = False
            
            return {
                "conditions_met": all_conditions_met,
                "details": results,
                "summary": f"{'✅ Toutes les conditions sont remplies' if all_conditions_met else '❌ Certaines conditions ne sont pas remplies'}"
            }
            
        except Exception as e:
            logger.error(f"Erreur vérification conditions: {e}")
            return {"conditions_met": False, "details": f"Erreur: {e}"}
    
    async def get_weather_info(self, city: str = "Tunis", target_date: str = None) -> str:
        """Récupère et formate les informations météo"""
        weather_data = self.get_weather_from_openweather(city, target_date)
        
        if not weather_data.get("success", False):
            return f"❌ {weather_data.get('error', 'Erreur inconnue')}"
        
        try:
            current = weather_data["current"]
            forecast = weather_data.get("forecast")
            
            # Si une date spécifique est demandée, cherche dans les prévisions
            weather_to_show = current
            date_info = "Actuellement"
            
            if target_date and target_date != "Non spécifiée":
                forecast_item = self._find_weather_for_date(forecast, target_date)
                if forecast_item:
                    weather_to_show = {
                        "main": forecast_item["main"],
                        "weather": forecast_item["weather"],
                        "wind": forecast_item["wind"],
                        "name": current["name"]
                    }
                    date_info = f"Prévision pour {target_date}"
            
            # Formate les données
            temp = weather_to_show["main"]["temp"]
            feels_like = weather_to_show["main"]["feels_like"]
            humidity = weather_to_show["main"]["humidity"]
            description = weather_to_show["weather"][0]["description"]
            wind_speed = weather_to_show["wind"]["speed"]
            
            result = f"""📍 {current["name"]}, Tunisie
📅 {date_info}
🌡️ Température: {temp}°C (ressenti {feels_like}°C)
☁️ Conditions: {description.title()}
💨 Vent: {wind_speed} m/s
💧 Humidité: {humidity}%"""
            
            return result
            
        except KeyError as e:
            logger.error(f"Erreur parsing météo: {e}")
            return f"❌ Erreur lors de l'analyse des données météo: {e}"
    
    async def send_email(self, subject: str, body: str) -> bool:
        """Envoie un email au CEO"""
        if not self.connected or not self.session:
            raise Exception("Pas connecté au serveur MCP")
            
        try:
            logger.info(f"✉️ Envoi d'email au CEO: {self.ceo_email}")
            
            result = await self.session.call_tool(
                "gmail_send_message",
                arguments={
                    "to": self.ceo_email,
                    "subject": subject,
                    "body": body
                }
            )
            
            logger.info(f"✅ Email envoyé au CEO")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'envoi: {e}")
            return False
    
    async def process_user_request(self, user_input: str) -> str:
        """Traite la demande de l'utilisateur et décide quoi faire"""
        if not self.gemini_model:
            return "❌ Client Gemini non configuré. Impossible de traiter la demande."
        
        try:
            # Analyse avancée de l'intention avec Gemini
            analysis_prompt = f"""
Analyse cette demande d'employé et identifie précisément le type d'action:

DEMANDE: "{user_input}"

Types possibles:
1. WEATHER_CONDITIONAL_EMAIL - Demande météo avec condition pour envoyer un email (ex: "si température > 25°C, envoie email")
2. WEATHER_QUERY - Simple demande d'information météo
3. ABSENCE_REQUEST - Demande d'absence
4. SEARCH_REQUEST - Demande de recherche d'information
5. EMAIL_SIMPLE - Email simple sans condition
6. AUTRE - Autre type

Extrait aussi:
- EMPLOYEE_NAME: nom de l'employé si mentionné
- DATE: date mentionnée (aujourd'hui, demain, vendredi, etc.)
- LOCATION: ville/lieu si mentionné
- CONDITIONS: conditions météorologiques (température > X, etc.)
- REASON: raison d'absence si applicable
- EMAIL_REASON: raison pour l'email si applicable

Format OBLIGATOIRE:
TYPE: [TYPE_IDENTIFIE]
EMPLOYEE_NAME: [nom ou "Non spécifié"]
DATE: [date extraite ou "Non spécifiée"]
LOCATION: [lieu ou "Tunis"]
CONDITIONS: [conditions météo ou "Aucune"]
REASON: [raison si applicable ou ""]
EMAIL_REASON: [raison email ou ""]
SUBJECT: [sujet email suggéré ou ""]
"""
            
            analysis = self.gemini_model.generate_content(analysis_prompt)
            analysis_text = analysis.text if analysis.text else ""
            
            # Parse la réponse
            parsed_info = self._parse_analysis(analysis_text)
            
            # Parse la date depuis le texte original
            parsed_date = self._parse_date_from_text(user_input)
            if parsed_date != "Non spécifiée":
                parsed_info['DATE'] = parsed_date
            
            logger.info(f"📊 Analyse: Type={parsed_info['TYPE']}, Date={parsed_info['DATE']}")
            
            # Exécute l'action selon le type identifié
            if parsed_info['TYPE'] == 'WEATHER_CONDITIONAL_EMAIL':
                return await self._handle_weather_conditional_email(parsed_info, user_input)
            elif parsed_info['TYPE'] == 'WEATHER_QUERY':
                return await self._handle_weather_query(parsed_info, user_input)
            elif parsed_info['TYPE'] == 'ABSENCE_REQUEST':
                return await self._handle_absence_request(parsed_info, user_input)
            elif parsed_info['TYPE'] == 'SEARCH_REQUEST':
                return await self._handle_search_request(parsed_info, user_input)
            elif parsed_info['TYPE'] == 'EMAIL_SIMPLE':
                return await self._handle_simple_email(parsed_info, user_input)
            else:
                return await self._handle_other_request(parsed_info, user_input)
                
        except Exception as e:
            logger.error(f"❌ Erreur traitement demande: {e}")
            return f"❌ Erreur lors du traitement de votre demande: {e}"
    
    async def _handle_weather_conditional_email(self, info: Dict[str, str], original_request: str) -> str:
        """Gère une demande météo avec condition d'email"""
        try:
            logger.info("🌤️📧 Traitement demande météo conditionnelle")
            
            location = info.get('LOCATION', 'Tunis')
            target_date = info.get('DATE', 'Non spécifiée')
            employee_name = info.get('EMPLOYEE_NAME', 'Employé')
            
            # Récupère les données météo
            weather_data = self.get_weather_from_openweather(location, target_date)
            
            if not weather_data.get("success", False):
                return f"❌ Impossible de récupérer la météo: {weather_data.get('error', 'Erreur inconnue')}"
            
            # Extrait les conditions météorologiques depuis le texte
            conditions = self._extract_weather_conditions(original_request)
            
            if not conditions:
                return "❌ Aucune condition météorologique détectée dans votre demande"
            
            logger.info(f"🔍 Conditions détectées: {len(conditions)}")
            
            # Vérifie les conditions
            condition_check = self._check_weather_conditions(weather_data, conditions)
            
            # Formate les informations météo
            weather_info = await self.get_weather_info(location, target_date)
            
            # Résultat de la vérification
            result_text = f"🌤️ Vérification météo pour {location}"
            if target_date != "Non spécifiée":
                result_text += f" le {target_date}"
            
            result_text += f"\n\n{weather_info}\n\n"
            result_text += f"🔍 Vérification des conditions:\n{condition_check['summary']}\n"
            
            for detail in condition_check.get('details', []):
                status = "✅" if detail['met'] else "❌"
                result_text += f"{status} {detail['parameter'].title()}: {detail['actual']} (condition: {detail['expected']})\n"
            
            # Si les conditions sont remplies, envoie l'email
            if condition_check['conditions_met']:
                current_date = self._get_current_date_formatted()
                
                # Génère l'email
                email_reason = info.get('EMAIL_REASON') or "absence en raison des conditions météorologiques"
                
                email_prompt = f"""
Rédige un email professionnel informant le CEO d'une absence basée sur les conditions météorologiques:

INFORMATIONS:
- Employé: {employee_name}
- Date d'absence: {target_date if target_date != 'Non spécifiée' else 'aujourd\'hui'}
- Raison: {email_reason}
- Conditions météo vérifiées: {condition_check['summary']}
- Détails météo: {weather_info}
- Date actuelle: {current_date}
- Destinataire: {self.ceo_name}

IMPORTANT: Respecte EXACTEMENT ce format:

SUJET: Absence pour conditions météorologiques - {employee_name}

CORPS:
{current_date}

Cher Monsieur {self.ceo_name},

[Corps du message expliquant l'absence due aux conditions météorologiques avec les détails vérifiés]

Cordialement,
{employee_name}
"""
                
                email_response = self.gemini_model.generate_content(email_prompt)
                email_text = email_response.text if email_response.text else ""
                
                # Parse sujet et corps
                subject, body = self._parse_email_content(email_text, f"Absence pour conditions météorologiques - {employee_name}")
                
                # Envoie l'email
                success = await self.send_email(subject, body)
                
                if success:
                    result_text += f"\n✅ CONDITIONS REMPLIES - Email envoyé au CEO!\n📧 Sujet: {subject}"
                else:
                    result_text += f"\n⚠️ CONDITIONS REMPLIES mais erreur d'envoi de l'email"
            else:
                result_text += f"\n❌ CONDITIONS NON REMPLIES - Aucun email envoyé"
            
            return result_text
            
        except Exception as e:
            logger.error(f"❌ Erreur météo conditionnelle: {e}")
            return f"❌ Erreur lors du traitement de la demande météo conditionnelle: {e}"
    
    async def _handle_weather_query(self, info: Dict[str, str], original_request: str) -> str:
        """Gère une simple demande d'information météo"""
        try:
            location = info.get('LOCATION', 'Tunis')
            target_date = info.get('DATE', 'Non spécifiée')
            
            logger.info(f"🌤️ Demande météo pour {location}, date: {target_date}")
            
            weather_info = await self.get_weather_info(location, target_date)
            
            if self.gemini_model:
                analysis_prompt = f"""
Analyse ce résultat météo et fournis une réponse claire et utile:

RECHERCHE: {original_request}
DONNÉES MÉTÉO: {weather_info}
DATE DEMANDÉE: {target_date}

Fournis:
- Résumé des conditions météo
- Prévisions si pour une date future
- Recommandations pratiques si pertinent
- Réponse en français, style conversationnel
"""
                analysis = self.gemini_model.generate_content(analysis_prompt)
                analyzed_result = analysis.text if analysis.text else weather_info
                
                return f"🌤️ Météo demandée:\n\n{analyzed_result}"
            
            return f"🌤️ Météo:\n\n{weather_info}"
            
        except Exception as e:
            logger.error(f"❌ Erreur requête météo: {e}")
            return f"❌ Erreur lors de la récupération de la météo: {e}"
    
    def _parse_analysis(self, analysis_text: str) -> Dict[str, str]:
        """Parse la réponse d'analyse de Gemini"""
        parsed = {
            'TYPE': 'AUTRE',
            'EMPLOYEE_NAME': 'Non spécifié',
            'REASON': '',
            'DATE': 'Non spécifiée',
            'LOCATION': 'Tunis',
            'CONDITIONS': 'Aucune',
            'EMAIL_REASON': '',
            'SUBJECT': '',
            'ACTION_NEEDED': ''
        }
        
        for line in analysis_text.split('\n'):
            for key in parsed.keys():
                if line.startswith(f"{key}:"):
                    parsed[key] = line.replace(f"{key}:", "").strip()
        
        return parsed
    
    async def _handle_absence_request(self, info: Dict[str, str], original_request: str) -> str:
        """Gère une demande d'absence"""
        try:
            logger.info("🏠 Traitement demande d'absence")
            
            # Collecte des informations automatiquement
            employee_name = info['EMPLOYEE_NAME'] if info['EMPLOYEE_NAME'] != 'Non spécifié' else "Employé"
            reason = info['REASON'] or "Raison personnelle"
            date = info['DATE'] if info['DATE'] != 'Non spécifiée' else datetime.now().strftime("%d/%m/%Y")
            location = info.get('LOCATION', 'Tunis')
            
            # Recherche contextuelle automatique selon la raison
            additional_info = ""
            search_queries = []
            
            # Détection automatique du type de recherche nécessaire
            reason_lower = reason.lower()
            if any(word in reason_lower for word in ['météo', 'temps', 'pluie', 'neige', 'orage', 'intempéries']):
                weather_info = await self.get_weather_info(location, date)
                additional_info += f"\n🌤️ Vérification météo: {weather_info}"
            
            if any(word in reason_lower for word in ['grève', 'manifestation', 'perturbation', 'transport']):
                search_queries.append("grèves Tunisie transport aujourd'hui")
                search_queries.append("perturbations transport public Tunis")
            
            if any(word in reason_lower for word in ['catastrophe', 'urgence', 'accident', 'santé']):
                search_queries.append("actualités urgentes Tunisie catastrophes")
            
            if any(word in reason_lower for word in ['covid', 'maladie', 'épidémie', 'virus']):
                search_queries.append("situation sanitaire Tunisie aujourd'hui")
            
            # Effectue les recherches
            for query in search_queries:
                result = self.search_web(query)
                additional_info += f"\n🔍 {query}: {result}"
            
            # Génère l'email avec Gemini
            current_date = self._get_current_date_formatted()
            
            email_prompt = f"""
Rédige un email professionnel de demande d'absence pour:

INFORMATIONS:
- Employé: {employee_name}
- Date d'absence: {date}
- Raison: {reason}
- Demande originale: "{original_request}"
- Recherches effectuées: {additional_info}
- Date actuelle: {current_date}
- Destinataire: {self.ceo_name}

IMPORTANT: Respecte EXACTEMENT ce format:

SUJET: Demande d'absence - {employee_name} - {date}

CORPS:
{current_date}

Cher Monsieur {self.ceo_name},

[Corps du message professionnel avec justification]

Je vous prie d'agréer, Monsieur {self.ceo_name.split()[-1] if len(self.ceo_name.split()) > 1 else self.ceo_name}, l'expression de mes sentiments respectueux.

Cordialement,
{employee_name}
"""
            
            email_response = self.gemini_model.generate_content(email_prompt)
            email_text = email_response.text if email_response.text else ""
            
            # Parse sujet et corps
            subject, body = self._parse_email_content(email_text, f"Demande d'absence - {employee_name}")
            
            # Envoie l'email
            success = await self.send_email(subject, body)
            
            if success:
                return f"✅ Email de demande d'absence envoyé au CEO avec succès!\n\n📧 Sujet: {subject}\n📄 Contenu: {body[:200]}..."
            else:
                return "❌ Erreur lors de l'envoi de l'email de demande d'absence"
                
        except Exception as e:
            logger.error(f"❌ Erreur demande absence: {e}")
            return f"❌ Erreur lors du traitement de la demande d'absence: {e}"
    
    async def _handle_search_request(self, info: Dict[str, str], original_request: str) -> str:
        """Gère une demande de recherche"""
        try:
            query = original_request
            logger.info(f"🔍 Recherche: {query}")
            
            # Effectue la recherche
            result = self.search_web(query)
            
            # Analyse avec Gemini pour une réponse plus claire
            if self.gemini_model:
                analysis_prompt = f"""
Analyse ce résultat de recherche et fournis une réponse claire et utile:

RECHERCHE: {query}
RÉSULTAT: {result}

Fournis:
- Résumé des informations importantes
- Réponse directe à la question
- Implications pratiques s'il y en a
"""
                analysis = self.gemini_model.generate_content(analysis_prompt)
                analyzed_result = analysis.text if analysis.text else result
                
                return f"🔍 Résultat de recherche pour: {query}\n\n📊 {analyzed_result}"
            
            return f"🔍 Résultat de recherche pour: {query}\n\n📊 {result}"
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche: {e}")
            return f"❌ Erreur lors de la recherche: {e}"
    
    async def _handle_simple_email(self, info: Dict[str, str], original_request: str) -> str:
        """Gère un email simple"""
        try:
            logger.info("✉️ Email simple")
            
            employee_name = info['EMPLOYEE_NAME'] if info['EMPLOYEE_NAME'] != 'Non spécifié' else "Employé"
            
            # Génère l'email basé sur la demande
            current_date = self._get_current_date_formatted()
            
            email_prompt = f"""
Rédige un email professionnel basé sur cette demande:

INFORMATIONS:
- DEMANDE: "{original_request}"
- SUJET SUGGÉRÉ: {info['SUBJECT']}
- Date actuelle: {current_date}
- Destinataire: {self.ceo_name}
- Expéditeur: {employee_name}

IMPORTANT: Respecte EXACTEMENT ce format:

SUJET: {info['SUBJECT'] or 'Email professionnel'}

CORPS:
{current_date}

Cher Monsieur {self.ceo_name},

[Corps du message professionnel adapté au contexte]

Cordialement,
{employee_name}
"""
            
            email_response = self.gemini_model.generate_content(email_prompt)
            email_text = email_response.text if email_response.text else ""
            
            subject, body = self._parse_email_content(email_text, "Email professionnel")
            
            success = await self.send_email(subject, body)
            
            if success:
                return f"✅ Email envoyé au CEO avec succès!\n\n📧 Sujet: {subject}\n📄 Contenu: {body[:200]}..."
            else:
                return "❌ Erreur lors de l'envoi de l'email"
                
        except Exception as e:
            logger.error(f"❌ Erreur email simple: {e}")
            return f"❌ Erreur lors de l'envoi de l'email: {e}"
    
    async def _handle_other_request(self, info: Dict[str, str], original_request: str) -> str:
        """Gère les autres types de demandes"""
        try:
            # Utilise Gemini pour répondre
            response_prompt = f"""
Réponds à cette demande d'un employé de manière utile et professionnelle:

DEMANDE: "{original_request}"

Si c'est une question, réponds directement.
Si ça nécessite une action spécifique, explique comment procéder.
"""
            
            response = self.gemini_model.generate_content(response_prompt)
            return response.text if response.text else "Je ne suis pas sûr de comprendre votre demande. Pouvez-vous la reformuler ?"
            
        except Exception as e:
            logger.error(f"❌ Erreur autre demande: {e}")
            return f"❌ Erreur lors du traitement de votre demande: {e}"
    
    def _parse_email_content(self, email_text: str, default_subject: str) -> tuple:
        """Parse le contenu email généré par Gemini"""
        lines = email_text.split('\n')
        subject = default_subject
        body = ""
        subject_found = False
        body_found = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Cherche le sujet
            if line.startswith("SUJET:") and not subject_found:
                subject = line.replace("SUJET:", "").strip()
                subject_found = True
                continue
            
            # Cherche le corps
            if line.startswith("CORPS:") and not body_found:
                # Prend tout ce qui suit "CORPS:" sur les lignes suivantes
                body_lines = []
                for j in range(i + 1, len(lines)):
                    body_line = lines[j].strip()
                    # Ignore les lignes vides au début
                    if not body_line and not body_lines:
                        continue
                    # Arrête si on trouve "OBJET:" dans le corps (erreur de Gemini)
                    if body_line.startswith("OBJET:"):
                        continue
                    body_lines.append(lines[j])  # Garde l'indentation originale
                
                body = '\n'.join(body_lines).strip()
                body_found = True
                break
        
        # Si pas de structure SUJET:/CORPS: détectée, essaie de parser différemment
        if not subject_found and not body_found:
            # Cherche "OBJET:" au lieu de "SUJET:"
            for i, line in enumerate(lines):
                if line.strip().startswith("OBJET:"):
                    subject = line.replace("OBJET:", "").strip()
                    # Le reste est le corps
                    body = '\n'.join(lines[i+1:]).strip()
                    break
            
            # Si toujours rien, utilise tout comme corps
            if not subject.strip() or subject == default_subject:
                body = email_text.strip()
                # Nettoie le corps des références d'objet
                body_lines = []
                for line in body.split('\n'):
                    if not line.strip().startswith("OBJET:") and not line.strip().startswith("SUJET:"):
                        body_lines.append(line)
                body = '\n'.join(body_lines).strip()
        
        return subject, body
    
    async def disconnect(self):
        """Ferme proprement la connexion MCP"""
        try:
            if self._session_context:
                await self._session_context.__aexit__(None, None, None)
            if self._connection:
                await self._connection.__aexit__(None, None, None)
            self.connected = False
            logger.info("🔌 Connexion MCP fermée proprement")
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors de la fermeture: {e}")

async def main():
    """Interface principale par prompt"""
    print("🤖 AGENT GMAIL INTELLIGENT - VERSION AMÉLIORÉE")
    print("=" * 60)
    print("Tapez vos demandes en langage naturel:")
    print("• 'Quelle est la météo vendredi en Tunisie et si la température dépasse 25 degrés envoie un mail au CEO'")
    print("• 'Je veux m'absenter demain car il pleut'")
    print("• 'Vérifie s'il y a des grèves cette semaine'")
    print("• 'Quelle est la météo aujourd'hui?'")
    print("• Tapez 'quit' pour quitter")
    print("=" * 60)
    
    agent = SmartGmailAgent()
    
    try:
        # Connexion au serveur MCP
        await agent.connect_to_mcp_server("mcp_gmail_server.py")
        print(f"✅ Agent connecté! Emails envoyés à: {agent.ceo_email}")
        print(f"👤 CEO identifié: {agent.ceo_name}")
        print(f"📅 Date système: {agent._get_current_date_formatted()}")
        print("-" * 60)
        
        # Boucle interactive
        while True:
            try:
                user_input = input("\n💬 Votre demande: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q', 'quitter']:
                    print("👋 Au revoir !")
                    break
                
                if not user_input:
                    continue
                
                print("🤖 Traitement en cours...")
                response = await agent.process_user_request(user_input)
                print(f"\n📝 Réponse:\n{response}")
                
            except KeyboardInterrupt:
                print("\n👋 Au revoir !")
                break
            except Exception as e:
                print(f"❌ Erreur: {e}")
        
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        print(f"❌ Impossible de démarrer l'agent: {e}")
        print("🔧 Vérifiez que mcp_gmail_server.py existe et que les dépendances sont installées")
    finally:
        if agent.connected:
            await agent.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Programme arrêté")
    except Exception as e:
        logger.error(f"❌ Erreur de démarrage: {e}")
        print(f"❌ Erreur: {e}")