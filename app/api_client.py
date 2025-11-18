"""
Client API pour Hyxi Cloud
Gère l'authentification et les requêtes vers l'API de télémétrie
Basé sur la documentation officielle Hyxi Cloud
"""
import hashlib
import hmac
import base64
import time
import random
import string
import requests
from typing import Dict, Any, Optional


class HyxiAPIClient:
    """Client pour interagir avec l'API Hyxi Cloud"""

    def __init__(self, access_key: str, secret_key: str, base_url: str, debug: bool = False):
        """
        Initialise le client API

        Args:
            access_key: Clé d'accès (AK)
            secret_key: Clé secrète (SK)
            base_url: URL de base de l'API
            debug: Active le mode debug (affiche toutes les requêtes/réponses)
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.base_url = base_url.rstrip('/')
        self.token = None
        self.token_expires_at = 0
        self.debug = debug

    def _debug_log(self, message: str, data: Any = None):
        """Log debug si le mode debug est activé"""
        if self.debug:
            print(f"[DEBUG] {message}")
            if data is not None:
                import json
                if isinstance(data, (dict, list)):
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                else:
                    print(data)

    @staticmethod
    def _sha512_hex(s: str) -> str:
        """Calcule le hash SHA-512 d'une chaîne et retourne en hexadécimal"""
        return hashlib.sha512(s.encode('utf-8')).hexdigest()

    def _hmac_sha512_base64(self, data: str) -> str:
        """Calcule le HMAC-SHA512 et retourne en base64"""
        h = hmac.new(
            self.secret_key.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha512
        )
        return base64.b64encode(h.digest()).decode('utf-8')

    @staticmethod
    def _random_nonce(length: int = 8) -> str:
        """Génère un nonce aléatoire"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    @staticmethod
    def _now_ts() -> str:
        """Retourne le timestamp actuel en millisecondes"""
        return str(int(time.time() * 1000))

    def _generate_signature(self, method: str, uri: str, content: str, token: str = '') -> tuple:
        """
        Génère la signature pour l'authentification

        Args:
            method: Méthode HTTP (GET, POST, etc.)
            uri: URI de l'endpoint (ex: /api/plant/v1/page)
            content: Contenu à signer (paramètres spécifiques)
            token: Token d'authentification (vide pour l'obtention du token)

        Returns:
            Tuple (timestamp, nonce, signature)
        """
        timestamp = self._now_ts()
        nonce = self._random_nonce()

        # Hash du contenu
        content_sha = self._sha512_hex(content)

        # Construction de la chaîne à signer
        string_to_sign = f"{uri}\n{method}\n{content_sha}\n"

        # Chaîne finale pour la signature
        sign_string = f"{self.access_key}{token}{timestamp}{nonce}{string_to_sign}"

        # Génération de la signature HMAC-SHA512
        signature = self._hmac_sha512_base64(sign_string)

        if self.debug:
            self._debug_log("=== Génération de signature ===")
            self._debug_log(f"Method: {method}")
            self._debug_log(f"URI: {uri}")
            self._debug_log(f"Content: {content}")
            self._debug_log(f"Content SHA-512: {content_sha}")
            self._debug_log(f"Token: {token[:20]}..." if token else "Token: (empty)")
            self._debug_log(f"Timestamp: {timestamp}")
            self._debug_log(f"Nonce: {nonce}")
            self._debug_log(f"Signature: {signature[:50]}...")

        return timestamp, nonce, signature

    def obtain_token(self) -> str:
        """
        Obtient un token d'authentification depuis l'API

        Returns:
            Token d'accès

        Raises:
            Exception: Si l'obtention du token échoue
        """
        uri = '/api/authorization/v1/token'
        method = 'POST'
        content = 'grantType:1'

        timestamp, nonce, signature = self._generate_signature(method, uri, content)

        headers = {
            'Content-Type': 'application/json',
            'AccessKey': self.access_key,
            'Timestamp': timestamp,
            'Nonce': nonce,
            'Sign': signature,
            'Sign-headers': 'grantType',
        }

        body = {'grantType': 1}

        if self.debug:
            self._debug_log("=== Obtention du token ===")
            self._debug_log(f"URL: {self.base_url}{uri}")
            self._debug_log("Headers:", headers)
            self._debug_log("Body:", body)

        try:
            response = requests.post(
                f"{self.base_url}{uri}",
                headers=headers,
                json=body,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if self.debug:
                self._debug_log(f"Status Code: {response.status_code}")
                self._debug_log("Response:", data)

            # L'API retourne code: '0' (string) pour succès et success: True
            if (data.get('code') in [0, '0'] or data.get('success') is True) and 'data' in data:
                access_token = data['data'].get('access_token')
                expires_in = data['data'].get('expires_in', data['data'].get('expiresIn', 3600))

                if access_token:
                    self.token = f"Bearer {access_token}"
                    # expires_in peut être une string, convertir en int
                    if isinstance(expires_in, str):
                        expires_in = int(expires_in)
                    self.token_expires_at = time.time() + expires_in
                    return self.token

            raise Exception(f"Erreur lors de l'obtention du token: {data}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Erreur de connexion: {str(e)}")

    def ensure_token(self):
        """Vérifie et renouvelle le token si nécessaire"""
        if not self.token or time.time() >= self.token_expires_at - 60:
            self.obtain_token()

    def _make_authenticated_request(self, method: str, uri: str,
                                   content: str = '',
                                   body: Optional[Dict] = None,
                                   params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Effectue une requête authentifiée vers l'API

        Args:
            method: Méthode HTTP
            uri: URI de l'endpoint
            content: Contenu pour la signature (vide pour GET)
            body: Body JSON pour POST
            params: Paramètres pour GET

        Returns:
            Réponse JSON de l'API
        """
        try:
            # S'assurer d'avoir un token valide
            self.ensure_token()

            # Générer la signature
            timestamp, nonce, signature = self._generate_signature(
                method, uri, content, self.token
            )

            # Construire les headers
            headers = {
                'Content-Type': 'application/json; charset=utf-8',
                'AccessKey': self.access_key,
                'Timestamp': timestamp,
                'Nonce': nonce,
                'Sign': signature,
                'Authorization': self.token,
            }

            url = f"{self.base_url}{uri}"

            if self.debug:
                self._debug_log(f"=== Requête {method} ===")
                self._debug_log(f"URL: {url}")
                self._debug_log("Headers:", headers)
                if params:
                    self._debug_log("Params:", params)
                if body:
                    self._debug_log("Body:", body)

            # Effectuer la requête
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=body, timeout=30)
            else:
                raise ValueError(f"Méthode HTTP non supportée: {method}")

            response.raise_for_status()
            result = response.json()

            if self.debug:
                self._debug_log(f"Status Code: {response.status_code}")
                self._debug_log("Response:", result)

            return result

        except requests.exceptions.RequestException as e:
            error_message = str(e)
            status_code = None

            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                try:
                    error_data = e.response.json()
                    error_message = error_data.get('message', error_message)
                except:
                    pass

            return {
                'error': True,
                'message': error_message,
                'status_code': status_code
            }

    # === Endpoints API Hyxi Cloud ===

    def test_connection(self) -> Dict[str, Any]:
        """
        Test la connexion à l'API en obtenant un token

        Returns:
            Résultat du test
        """
        try:
            self.obtain_token()
            return {
                'success': True,
                'message': 'Connexion réussie',
                'token_obtained': True
            }
        except Exception as e:
            return {
                'error': True,
                'message': str(e),
                'token_obtained': False
            }

    def get_plant_list(self, page_size: int = 10, current_page: int = 1) -> Dict[str, Any]:
        """
        Récupère la liste des plants (installations)

        Args:
            page_size: Nombre d'éléments par page
            current_page: Numéro de la page

        Returns:
            Liste des plants
        """
        uri = '/api/plant/v1/page'
        params = {
            'pageSize': page_size,
            'currentPage': current_page
        }
        return self._make_authenticated_request('GET', uri, content='', params=params)

    def get_plant_info(self, plant_id: str) -> Dict[str, Any]:
        """
        Récupère les informations détaillées d'un plant

        Args:
            plant_id: ID du plant

        Returns:
            Informations du plant
        """
        uri = '/api/plant/v1/info'
        params = {'plantId': plant_id}
        return self._make_authenticated_request('GET', uri, content='', params=params)

    def get_plant_power_statistics(self, plant_id: str, start_time: str) -> Dict[str, Any]:
        """
        Récupère les statistiques de production d'un plant pour un jour donné

        Args:
            plant_id: ID du plant
            start_time: Date de début au format 'YYYY-MM-DD'

        Returns:
            Statistiques de production (données toutes les 5 min)
        """
        uri = '/api/plant/v1/queryPlantPowerStatistics'
        body = {
            'plantId': plant_id,
            'startTime': start_time
        }
        return self._make_authenticated_request('POST', uri, content='', body=body)

    def get_plant_power_generation(self, plant_id: str) -> Dict[str, Any]:
        """
        Obtient les informations de production d'énergie du plant spécifié
        Inclut: production journalière, mensuelle, annuelle et totale

        Args:
            plant_id: ID du plant

        Returns:
            Informations de production d'énergie agrégées
        """
        uri = '/api/plant/v1/queryPowerGeneration'
        body = {'plantId': plant_id}
        return self._make_authenticated_request('POST', uri, content='', body=body)

    def get_plant_yield_statistics(self, plant_id: str, time_type: int, start_time: str) -> Dict[str, Any]:
        """
        Interroge les statistiques de production d'énergie du plant par période
        
        Args:
            plant_id: ID du plant
            time_type: Type de période
                       1 = Jour (startTime format: yyyy-MM-dd)
                       2 = Mois (startTime format: yyyy-MM)
                       3 = Année (startTime format: yyyy)
            start_time: Date de début selon le format du time_type

        Returns:
            Statistiques de production d'énergie par jour/mois/année
        """
        uri = '/api/plant/v1/queryPlantYieldStatistics'  # Correction orthographique: Yield
        
        # Convertir start_time en entier pour time_type=3 (année)
        if time_type == 3:
            start_time_value = int(start_time) if isinstance(start_time, str) else start_time
        else:
            start_time_value = start_time
            
        body = {
            'plantId': plant_id,
            'timeType': time_type,
            'startTime': start_time_value
        }
        return self._make_authenticated_request('POST', uri, content='', body=body)

    def get_plant_weather(self, plant_id: str) -> Dict[str, Any]:
        """
        Récupère les informations météo incluant lever/coucher du soleil
        
        Args:
            plant_id: ID du plant

        Returns:
            Données météo avec sunrise/sunset pour chaque jour
        """
        uri = '/api/plant/v1/weather'
        body = {'plantId': plant_id}
        return self._make_authenticated_request('POST', uri, content='', body=body)
