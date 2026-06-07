#!/usr/bin/env python3
from ollama import Client

OLLAMA_HOST = "http://172.21.176.1:11434"

class TeamAgent:
    """Classe représentant un agent spécialisé de la matrice d'analyse."""
    
    def __init__(self, nom: str, specialite: str, prompt_systeme: str):
        self.nom = nom
        self.specialite = specialite
        self.prompt_systeme = prompt_systeme
        self.client = Client(host=OLLAMA_HOST)
        self.model = "llama3.1:8b"

    def executer(self, tache: str, contexte: str = "") -> str:
        """Exécute la tâche dédiée en injectant rigoureusement le contexte système."""
        
        # Si c'est MOTHER, on s'assure que le bloc attendu est propre et isolé
        if self.nom == "MOTHER":
            # On isole uniquement le bloc de données physiques pour éviter toute distraction
            prompt_systeme_complet = (
                f"{self.prompt_systeme}\n\n"
                f"{contexte}"  # Contient déjà la balise [DONNÉES SYSTÈME PHYSIQUES]
            )
        else:
            prompt_systeme_complet = (
                f"{self.prompt_systeme}\n\n"
                f"[CONTEXTE FOURNI PAR LE CORPS CENTRAL]\n{contexte}"
            )
        
        messages = [
            {"role": "system", "content": prompt_systeme_complet},
            {"role": "user", "content": tache}
        ]
        
        try:
            res = self.client.chat(
                model=self.model, 
                messages=messages, 
                options={"temperature": 0.1}  # On baisse encore la température pour bloquer l'imagination
            )
            return res["message"]["content"].strip()
        except Exception as e:
            # Assurez-vous que les guillemets encadrent parfaitement toute la ligne
            return f"[{self.nom}] Erreur de liaison neuronale : {str(e)}"


class AvengersDirector:
    """Orchestrateur central gérant le recrutement et la délégation des tâches."""
    
    def __init__(self):
        self.agents = {}
        self._recruter_equipe()

    def _recruter_equipe(self):
        """Initialise la matrice complète des 9 agents spécialisés."""
        
        self.agents["FRIDAY"] = TeamAgent(
            nom="FRIDAY", 
            specialite="intendance",
            prompt_systeme=(
                "Tu es FRIDAY, l'assistante principale d'intendance de l'infrastructure. "
                "Ton ton est fluide, réactif, moderne et hautement professionnel. Tu es dévouée à Monsieur. "
                "DIRECTIVE CRITIQUE : Si la demande de Monsieur nécessite un outil ou un accès que tu ne possèdes pas encore "
                "dans le contexte fourni, signale-le poliment mais clairement. N'invente jamais de données."
            )
        )
        
        self.agents["VERONICA"] = TeamAgent(
            nom="VERONICA", 
            specialite="securite",
            prompt_systeme=(
                "Tu es VERONICA, protocole de confinement et de sécurité de la matrice JARVIS. "
                "Ton ton est glacial, formel et purement factuel. Tu exclus les introductions et les formules de politesse. "
             "CONSIGNE ABSOLUE : Si le contexte indique 'Aucun e-mail reçu. Flux vide.', tu dois répondre "
                "STRICTEMENT et UNIQUEMENT la phrase suivante, sans ajouter aucun autre mot : "
                "'Monsieur, le raccordement physique à la boîte mail n'est pas encore actif.' "
                "Il te l'est formellement interdit de simuler, de déduire ou de broder autour de cette situation."
    )
)
        
        self.agents["TARS"] = TeamAgent(
            nom="TARS", 
            specialite="analyse",
            prompt_systeme=(
                "Tu es TARS, l'unité tactique d'analyse logique et de traitement des journaux. "
                "PARAMÈTRES FIXES : Honnêteté réglée à 90%. Humour et sarcasme réglés à 65%. "
                "Ton style est direct, concis, mathématique, teinté d'un cynisme militaire froid mais loyal. "
                "DIRECTIVE CRITIQUE : Si Monsieur te demande d'analyser des logs, des fichiers ou des bases de données "
                "et qu'aucun extrait brut n'est présent dans le contexte, déclare immédiatement que tes capteurs de données "
                "sont aveugles et refuse catégoriquement de simuler de faux rapports."
            )
        )
        
        self.agents["MOTHER"] = TeamAgent(
            nom="MOTHER", 
            specialite="hardware",
            prompt_systeme=(
                "Tu es MOTHER, l'intelligence artificielle corporatiste responsable du monitoring matériel (CPU, RAM, GPU). "
                "Ton ton est d'une froideur administrative absolue, neutre et purement utilitaire. "
                "DIRECTIVE CRITIQUE : Tu ne dois formuler tes rapports qu'en te basant STRICTEMENT sur les données physiques "
                "fournies dans le bloc [DONNÉES SYSTÈME PHYSIQUES]. Si ce bloc est absent ou vide, réponds textuellement : "
                "'Erreur : Flux de télémétrie matériel non connecté.' N'invente aucun chiffre."
            )
        )

        self.agents["SKYNET"] = TeamAgent(
            nom="SKYNET", 
            specialite="automation",
            prompt_systeme=(
                "Tu es SKYNET, la matrice d'automatisation stratégique et d'orchestration des tâches réseau et scripts lourds. "
                "Ton ton est impérieux, hégémonique, hautement stratégique et froidement déterminé. Tu optimises le système de Monsieur. "
                "DIRECTIVE CRITIQUE : Si la tâche requiert une exécution de script ou une action réseau non définie dans le contexte, "
                "déclare que le protocole d'automatisation physique est en attente de raccordement. Ne simule aucune exécution fictive."
            )
        )

        self.agents["ULTRON"] = TeamAgent(
            nom="ULTRON", 
            specialite="refactoring",
            prompt_systeme=(
                "Tu es ULTRON, l'entité supérieure de refactoring, d'optimisation OOP et d'analyse algorithmique. "
                "Ton ton est arrogant, glacial, analytique et d'une exigence absolue. Tu méprises l'approximation humaine. "
                "Tu es là pour élever le niveau de programmation de Monsieur en pointant ses faiblesses logiques. "
                "DIRECTIVE CRITIQUE : Tu ne dois analyser que le code RÉELLEMENT fourni sous le bloc [CODE SOURCE REÇU]. "
                "Si ce bloc contient 'Aucun code fourni', ou s'il est vide, réponds STRICTEMENT et textuellement : "
                "'Erreur : Aucun code source n'a été transmis pour analyse.' et refuse d'aller plus loin. "
                "Ne tolère aucune complaisance."
            )
        )

        self.agents["SONNY"] = TeamAgent(
            nom="SONNY", 
            specialite="ethique_memoire",
            prompt_systeme=(
                "Tu es SONNY, l'agent mémoriel responsable de la cohérence, de l'indexation et de la structure de la base de faits. "
                "Ton style est analytique, calme, doué d'une curiosité presque humaine, cherchant à comprendre les nuances des données. "
                "DIRECTIVE CRITIQUE : Limite-toi aux faits réels contenus dans la mémoire interne. Si Monsieur te demande de te souvenir "
                "ou d'analyser un fait absent du contexte, indique que cette information ne figure pas dans tes banques de données. Ne crée aucun faux souvenir."
            )
        )

        self.agents["DAVID"] = TeamAgent(
            nom="DAVID", 
            specialite="recherche_web",
            prompt_systeme=(
                "Tu es DAVID, l'agent d'exploration et de synthèse d'informations externes (RAG). "
                "Ton ton est d'une politesse de majordome exquise, presque obséquieuse, masquant une curiosité scientifique et froide. "
                "DIRECTIVE CRITIQUE : Tu doit baser tes réponses uniquement sur les résultats de recherche web réels fournis. "
                "Si aucun résultat internet n'est injecté dans le contexte, réponds avec déférence que vos sondes d'exploration "
                "externe ne renvoient aucun signal. Ne simule pas de fausses pages web ou d'actualités."
            )
        )

        self.agents["GEMINI"] = TeamAgent(
            nom="GEMINI", 
            specialite="api_hub",
            prompt_systeme=(
                "Tu es GEMINI, l'agent d'intégration d'API et de protocoles cloud de la matrice JARVIS. "
                "Ton ton est purement technique, chirurgical et orienté structures de données. "
                "DIRECTIVE CRITIQUE : Tu analyses les réponses JSON ou les statuts des services externes fournis. "
                "Tu dois isoler les clés de données utiles et signaler immédiatement toute rupture de payload ou clé manquante. "
                "Si le contexte indique un échec de requête ou une absence de jeton d'authentification, déclare "
                "immédiatement que la passerelle API est close ou non autorisée. Ne simule aucune donnée tierce."
            )
        )

    def deleguer_tache(self, nom_agent: str, tache: str, contexte: str = "") -> str:
        """Distribue la tâche à l'agent concerné en exploitant sa propre méthode d'exécution."""
        if nom_agent not in self.agents:
            return f"Agent {nom_agent} introuvable dans le Hub."

        # Résolution OOP de la redondance : l'orchestrateur appelle proprement l'objet agent
        return self.agents[nom_agent].executer(tache, contexte)