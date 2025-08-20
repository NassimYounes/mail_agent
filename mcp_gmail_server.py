import asyncio
import json
import os
import base64
import logging
from typing import Any, Dict, List
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent

# Import Google APIs
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Scopes Gmail
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

class GmailMCPServer:
    """Serveur MCP pour Gmail (Version Corrigée)"""
    
    def __init__(self):
        self.gmail_service = None
        self.server = Server("gmail-mcp-server")
        self._setup_tools()
    
    def _setup_tools(self):
        """Configure les outils MCP disponibles (Version Corrigée)"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """Retourne la liste des outils disponibles"""
            tools = [
                Tool(
                    name="gmail_list_messages",
                    description="Liste les messages Gmail récents",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "max_results": {"type": "integer", "default": 10}
                        }
                    }
                ),
                Tool(
                    name="gmail_send_message",
                    description="Envoie un email via Gmail",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "to": {"type": "string"},
                            "subject": {"type": "string"},
                            "body": {"type": "string"}
                        },
                        "required": ["to", "subject", "body"]
                    }
                ),
                Tool(
                    name="gmail_search_messages",
                    description="Recherche des messages Gmail",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "max_results": {"type": "integer", "default": 10}
                        },
                        "required": ["query"]
                    }
                )
            ]
            logger.info(f"Outils configurés: {[tool.name for tool in tools]}")
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Gère les appels d'outils (Version Corrigée)"""
            try:
                logger.info(f"Appel d'outil: {name} avec arguments: {arguments}")
                
                if name == "gmail_list_messages":
                    return await self._list_messages(arguments.get("max_results", 10))
                elif name == "gmail_send_message":
                    return await self._send_message(
                        arguments["to"], 
                        arguments["subject"], 
                        arguments["body"]
                    )
                elif name == "gmail_search_messages":
                    return await self._search_messages(
                        arguments["query"], 
                        arguments.get("max_results", 10)
                    )
                else:
                    raise ValueError(f"Outil inconnu: {name}")
            except Exception as e:
                logger.error(f"Erreur dans handle_call_tool: {str(e)}")
                return [TextContent(type="text", text=f"Erreur: {str(e)}")]
    
    async def _authenticate_gmail(self):
        """Authentifie avec Gmail API """
        creds = None
        
        
        # Token sauvegardé
        if os.path.exists('token.json'):
            try:
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
                logger.info("Credentials chargés depuis token.json")
            except Exception as e:
                logger.error(f"Erreur de lecture token.json: {e}")
        
        # Si pas de credentials valides, demande l'autorisation
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Credentials rafraîchis")
                except Exception as e:
                    logger.error(f"Erreur de rafraîchissement: {e}")
                    creds = None
            
            if not creds:
                try:
                    if not os.path.exists('credentials.json'):
                        raise FileNotFoundError("Fichier credentials.json introuvable")
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                    logger.info("Nouvelle authentification réussie")
                except Exception as e:
                    logger.error(f"Erreur d'authentification: {e}")
                    raise
            
            # Sauvegarde les credentials
            try:
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
                logger.info("Nouveau token sauvegardé")
            except Exception as e:
                logger.error(f"Erreur sauvegarde token: {e}")
        
        try:
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            logger.info("Service Gmail initialisé avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur initialisation service Gmail: {e}")
            raise
    
    async def _list_messages(self, max_results: int) -> List[TextContent]:
        """Liste les messages Gmail (Version Corrigée)"""
        try:
            if not self.gmail_service:
                await self._authenticate_gmail()
            
            results = self.gmail_service.users().messages().list(
                userId='me', maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            logger.info(f"{len(messages)} messages trouvés")
            
            email_contents = []
            for message in messages:
                msg = self.gmail_service.users().messages().get(
                    userId='me', id=message['id'], format='full'
                ).execute()
                
                headers = msg['payload'].get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Pas de sujet')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Expéditeur inconnu')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Date inconnue')
                
                body = self._extract_message_body(msg['payload'])
                
                email_data = {
                    'id': message['id'],
                    'subject': subject,
                    'from': sender,
                    'date': date,
                    'body': body[:500] + '...' if len(body) > 500 else body
                }
                
                email_contents.append(TextContent(
                    type="text",
                    text=json.dumps(email_data, ensure_ascii=False)
                ))
            
            return email_contents
            
        except Exception as e:
            logger.error(f"Erreur dans _list_messages: {e}")
            return [TextContent(type="text", text=f"Erreur: {str(e)}")]
    
    async def _send_message(self, to: str, subject: str, body: str) -> List[TextContent]:
        """Envoie un message Gmail (Version Corrigée)"""
        try:
            if not self.gmail_service:
                await self._authenticate_gmail()
            
            message = f"To: {to}\nSubject: {subject}\n\n{body}"
            raw_message = base64.urlsafe_b64encode(message.encode('utf-8')).decode('utf-8')
            
            send_result = self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Message envoyé avec ID: {send_result['id']}")
            return [TextContent(
                type="text", 
                text=json.dumps({
                    "status": "success",
                    "message_id": send_result['id']
                })
            )]
            
        except Exception as e:
            logger.error(f"Erreur dans _send_message: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "error": str(e)
                })
            )]
    
    async def _search_messages(self, query: str, max_results: int) -> List[TextContent]:
        """Recherche des messages Gmail (Version Corrigée)"""
        try:
            if not self.gmail_service:
                await self._authenticate_gmail()
            
            results = self.gmail_service.users().messages().list(
                userId='me', q=query, maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            logger.info(f"{len(messages)} messages trouvés pour la requête '{query}'")
            
            email_contents = []
            for message in messages:
                msg = self.gmail_service.users().messages().get(
                    userId='me', id=message['id'], format='full'
                ).execute()
                
                headers = msg['payload'].get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Pas de sujet')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Expéditeur inconnu')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Date inconnue')
                
                body = self._extract_message_body(msg['payload'])
                
                email_data = {
                    'id': message['id'],
                    'subject': subject,
                    'from': sender,
                    'date': date,
                    'body': body[:500] + '...' if len(body) > 500 else body,
                    'query': query
                }
                
                email_contents.append(TextContent(
                    type="text",
                    text=json.dumps(email_data, ensure_ascii=False)
                ))
            
            return email_contents
            
        except Exception as e:
            logger.error(f"Erreur dans _search_messages: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "error": str(e),
                    "query": query
                })
            )]
    
    def _extract_message_body(self, payload):
        """Extrait le corps du message (Version Corrigée)"""
        try:
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            
            return "Aucun contenu texte trouvé"
        except Exception as e:
            logger.error(f"Erreur extraction corps message: {e}")
            return f"Erreur d'extraction: {str(e)}"
    
    async def run(self):
        """Lance le serveur MCP (Version Corrigée)"""
        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="gmail-mcp-server",
                        server_version="1.0.1",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={}
                        )
                    )
                )
        except Exception as e:
            logger.error(f"Erreur dans run(): {e}")
            raise

async def main():
    """Fonction principale (Version Corrigée)"""
    try:
        logger.info("Démarrage du serveur MCP Gmail...")
        server = GmailMCPServer()
        await server.run()
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
    finally:
        logger.info("Serveur arrêté")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Serveur arrêté par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur de démarrage: {e}")