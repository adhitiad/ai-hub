import networkx as nx


class InsiderHunter:
    def __init__(self):
        self.graph = nx.Graph()

    def build_dummy_graph(self):
        """
        Simulasi membangun data relasi.
        Di production, data ini diambil dari DB (Collection: ownerships/directors).
        """
        # Node: Orang / Perusahaan
        # Edge: Hubungan (Direktur, Pemilik, Afiliasi)

        # Kasus: Pak Budi adalah Direktur PT A dan Komisaris PT B
        self.graph.add_edge("Pak Budi", "PT_AGRO_SEJAHTERA", relation="Director")
        self.graph.add_edge("Pak Budi", "PT_BUMI_MAKMUR", relation="Commissioner")

        # Kasus: PT C dimiliki oleh Group D
        self.graph.add_edge("PT_CEMENT_INDO", "GROUP_D_HOLDING", relation="Subsidiary")
        self.graph.add_edge("PT_D_DIGITAL", "GROUP_D_HOLDING", relation="Subsidiary")

    def find_related_stocks(self, stock_symbol: str) -> list:
        """
        Jika saham A bergerak, cari saham apa lagi yang satu 'circle'.
        """
        # Map Stock Symbol ke Nama PT (Simplified)
        company_map = {
            "AGRO": "PT_AGRO_SEJAHTERA",
            "BUMI": "PT_BUMI_MAKMUR",
            "SMGR": "PT_CEMENT_INDO",
        }

        company_name = company_map.get(stock_symbol)
        if not company_name or company_name not in self.graph:
            return []

        related_companies = []

        # 1. Cari Tetangga (Siapa direkturnya/pemiliknya?)
        neighbors = list(self.graph.neighbors(company_name))

        # 2. Cari Tetangga dari Tetangga (Perusahaan lain yang direkturnya sama)
        for entity in neighbors:
            second_degree = list(self.graph.neighbors(entity))
            for comp in second_degree:
                if comp != company_name:  # Jangan masukkan diri sendiri
                    relation_type = self.graph.get_edge_data(entity, comp)["relation"]
                    related_companies.append(
                        {
                            "entity": entity,  # Penghubung (Misal: Pak Budi)
                            "related_company": comp,
                            "role": relation_type,
                        }
                    )

        return related_companies


# --- CONTOH ---
# hunter = InsiderHunter()
# hunter.build_dummy_graph()
# print(hunter.find_related_stocks("AGRO"))
# Output: [{'entity': 'Pak Budi', 'related_company': 'PT_BUMI_MAKMUR', 'role': 'Commissioner'}]
# Artinya: AGRO gerak, cek BUMI juga, karena satu pengurus!# Artinya: AGRO gerak, cek BUMI juga, karena satu pengurus!
