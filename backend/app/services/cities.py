CITIES = [
    "Antwerp", "Ghent", "Brussels", "Charleroi", "Liège", "Bruges", "Leuven", "Namur", "Mons", "Aalst",
    "Mechelen", "Kortrijk", "Hasselt", "Ostend", "Sint-Niklaas", "Roeselare", "Tournai", "Genk", "Seraing", "Verviers",
    "Mouscron", "Dendermonde", "Beringen", "Turnhout", "Heist-op-den-Berg", "Lokeren", "Vilvoorde", "La Louvière", "Anderlecht", "Schaerbeek",
    "Ixelles", "Uccle", "Evere", "Etterbeek", "Forest", "Jette", "Molenbeek-Saint-Jean", "Saint-Gilles", "Woluwe-Saint-Lambert", "Woluwe-Saint-Pierre",
    "Waterloo", "Wavre", "Nivelles", "Ottignies-Louvain-la-Neuve", "Arlon", "Marche-en-Famenne", "Dinant", "Herentals", "Lier", "Knokke-Heist",
]

# Relatieve “basislast” (MWh per uur) per stad: groter = hoger.
# Dit is bewust synthetisch; consistentie is belangrijker dan exactheid.
BASE_LOAD = {
    "Brussels": 5200,
    "Antwerp": 4600,
    "Ghent": 3400,
    "Liège": 3000,
    "Charleroi": 2800,
}

DEFAULT_BASE = 1200  # voor kleinere steden
