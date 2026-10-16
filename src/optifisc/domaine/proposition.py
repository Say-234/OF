"""Articles de loi, réponses de l'assistant et propositions de l'agent (UC09, UC14)."""
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class Article:
    """Un article du CGI ou du LPF (texte public)."""
    source: str                    # « CGI 2026 », « LPF 2024 »
    numero: str                    # « 32 »
    chapitre: str                  # ex. « Impôt sur les sociétés »
    texte: str

    @property
    def reference(self) -> str:
        return f"{self.source} art. {self.numero}"


@dataclass(frozen=True)
class ArticleTrouve:
    article: Article
    pertinence: float              # score de recherche, de 0 à 1 (relatif au meilleur résultat)


@dataclass(frozen=True)
class ReponseAssistant:
    question: str
    articles: tuple[ArticleTrouve, ...]
    reponse: str = ""              # proposition rédigée par l'IA ("" si IA désactivée ou bloquée)
    articles_cites: tuple[str, ...] = ()
    sourcee: bool = False          # au moins un article cité fait partie des articles fournis
    modele: str = ""
    message: str = ""              # explication si l'IA n'a pas été appelée (pare-feu, indisponible…)


@dataclass(frozen=True)
class ProfilPseudonymise:
    """Ce que l'agent a le droit de voir du dossier (doc 01, A.3) : ni nom, ni IFU, ni libellé de compte."""
    secteur: str
    categorie_taux: str
    mois_arrete: int
    chiffre_affaires_millions: int
    resultat_comptable_millions: int
    resultat_fiscal_millions: int
    reintegrations_millions: int
    deductions_millions: int
    au_minimum_de_perception: bool
    ecart_au_seuil_millions: int   # résultat fiscal − seuil de bascule
    excedent_acomptes_millions: int
    dons_marge_millions: int

    def en_texte(self) -> str:
        lignes = [f"{cle} : {valeur}" for cle, valeur in self.__dict__.items()]
        return "\n".join(lignes)


@dataclass(frozen=True)
class Proposition:
    """Une proposition de l'agent. Les montants affichés viennent du moteur (gain), jamais du texte de l'IA."""
    id: str
    type: str                      # « levier » (chiffré par le moteur) ou « piste » (à étudier, sans chiffre)
    titre: str
    article: str                   # numéro de l'article du CGI cité
    justification: str             # texte de l'IA, nombres masqués
    id_levier: str = ""
    parametres: dict = field(default_factory=dict)
    gain: Decimal | None = None    # calculé par le moteur pour un levier
    confiance: Decimal = Decimal("0")
    controles: tuple[str, ...] = ()
    decision: str = ""             # « », « acceptee », « ecartee »
    motif: str = ""
