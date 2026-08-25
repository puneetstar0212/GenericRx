import json
import os

SEED_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "medicines_seed.json")

# Master templates for creating 500+ Indian/Global brand & generic medicine records
MEDICINE_GROUPS = [
    {
        "saltName": "Paracetamol 650mg",
        "category": "Analgesic & Antipyretic",
        "dosageForm": "Tablet",
        "strength": "650mg",
        "schedule": "OTC",
        "description": "Used for relieving fever and mild-to-moderate pain.",
        "brands": [
            {"name": "Crocin 650", "manufacturer": "GlaxoSmithKline Consumer Healthcare", "price": 34.50, "units": 15, "isGeneric": False},
            {"name": "Dolo 650", "manufacturer": "Micro Labs Ltd", "price": 32.00, "units": 15, "isGeneric": False},
            {"name": "Calpol 650", "manufacturer": "GSK Pharmaceuticals", "price": 33.00, "units": 15, "isGeneric": False},
            {"name": "Pacimol 650", "manufacturer": "Ipca Laboratories Ltd", "price": 28.50, "units": 15, "isGeneric": False},
            {"name": "Sumo L 650", "manufacturer": "Alkem Laboratories", "price": 27.00, "units": 15, "isGeneric": False},
            {"name": "P-650", "manufacturer": "Apex Laboratories", "price": 26.00, "units": 15, "isGeneric": False},
            {"name": "Jan Aushadhi Paracetamol 650", "manufacturer": "BPPI (Jan Aushadhi)", "price": 5.50, "units": 10, "isGeneric": True},
            {"name": "Generic Paracetamol 650", "manufacturer": "PMBJP Generic Pharma", "price": 4.80, "units": 10, "isGeneric": True},
        ]
    },
    {
        "saltName": "Amoxicillin 500mg + Clavulanic Acid 125mg",
        "category": "Antibiotic",
        "dosageForm": "Tablet",
        "strength": "625mg",
        "schedule": "Schedule H",
        "description": "Broad-spectrum penicillin antibiotic combined with beta-lactamase inhibitor.",
        "brands": [
            {"name": "Augmentin 625 Duo", "manufacturer": "GlaxoSmithKline", "price": 204.50, "units": 10, "isGeneric": False},
            {"name": "Moxikind-CV 625", "manufacturer": "Mankind Pharma", "price": 175.00, "units": 10, "isGeneric": False},
            {"name": "Clavam 625", "manufacturer": "Alkem Laboratories", "price": 182.00, "units": 10, "isGeneric": False},
            {"name": "Advent 625", "manufacturer": "Cipla Ltd", "price": 168.00, "units": 10, "isGeneric": False},
            {"name": "Mega-CV 625", "manufacturer": "Aristo Pharmaceuticals", "price": 155.00, "units": 10, "isGeneric": False},
            {"name": "Jan Aushadhi Amoxy-Clav 625", "manufacturer": "BPPI (Jan Aushadhi)", "price": 52.00, "units": 10, "isGeneric": True},
            {"name": "Generic Amoxicillin Clavulanate 625", "manufacturer": "PMBJP Generic Pharma", "price": 48.00, "units": 10, "isGeneric": True},
        ]
    },
    {
        "saltName": "Azithromycin 500mg",
        "category": "Antibiotic",
        "dosageForm": "Tablet",
        "strength": "500mg",
        "schedule": "Schedule H",
        "description": "Macrolide antibiotic used for respiratory tract infections and typhoid.",
        "brands": [
            {"name": "Azithral 500", "manufacturer": "Alembic Pharmaceuticals", "price": 119.50, "units": 5, "isGeneric": False},
            {"name": "Azee 500", "manufacturer": "Cipla Ltd", "price": 112.00, "units": 5, "isGeneric": False},
            {"name": "Zady 500", "manufacturer": "Mankind Pharma", "price": 105.00, "units": 5, "isGeneric": False},
            {"name": "Azibact 500", "manufacturer": "Ipca Laboratories", "price": 98.00, "units": 5, "isGeneric": False},
            {"name": "Jan Aushadhi Azithromycin 500", "manufacturer": "BPPI (Jan Aushadhi)", "price": 28.00, "units": 5, "isGeneric": True},
            {"name": "Generic Azithromycin 500", "manufacturer": "PMBJP Generic Pharma", "price": 24.50, "units": 5, "isGeneric": True},
        ]
    },
    {
        "saltName": "Metformin 500mg",
        "category": "Antidiabetic",
        "dosageForm": "Tablet",
        "strength": "500mg",
        "schedule": "Schedule H",
        "description": "First-line oral antidiabetic medication for Type-2 Diabetes Mellitus.",
        "brands": [
            {"name": "Glycomet 500", "manufacturer": "USV Ltd", "price": 28.00, "units": 10, "isGeneric": False},
            {"name": "Obimet 500", "manufacturer": "Abbott Healthcare", "price": 25.50, "units": 10, "isGeneric": False},
            {"name": "Cetapin 500", "manufacturer": "Sanofi India", "price": 24.00, "units": 10, "isGeneric": False},
            {"name": "Gluformin 500", "manufacturer": "Abbott", "price": 22.00, "units": 10, "isGeneric": False},
            {"name": "Jan Aushadhi Metformin 500", "manufacturer": "BPPI (Jan Aushadhi)", "price": 4.50, "units": 10, "isGeneric": True},
            {"name": "Generic Metformin 500", "manufacturer": "PMBJP Generic Pharma", "price": 3.80, "units": 10, "isGeneric": True},
        ]
    },
    {
        "saltName": "Pantoprazole 40mg",
        "category": "Gastrointestinal & Antacid",
        "dosageForm": "Tablet",
        "strength": "40mg",
        "schedule": "Schedule H",
        "description": "Proton pump inhibitor (PPI) used for GERD, acidity, and peptic ulcers.",
        "brands": [
            {"name": "Pan 40", "manufacturer": "Alkem Laboratories", "price": 155.00, "units": 15, "isGeneric": False},
            {"name": "Pantocid 40", "manufacturer": "Sun Pharma", "price": 162.00, "units": 15, "isGeneric": False},
            {"name": "Pantodac 40", "manufacturer": "Zydus Cadila", "price": 148.00, "units": 15, "isGeneric": False},
            {"name": "Nupenta 40", "manufacturer": "Macleods Pharma", "price": 130.00, "units": 15, "isGeneric": False},
            {"name": "Jan Aushadhi Pantoprazole 40", "manufacturer": "BPPI (Jan Aushadhi)", "price": 14.00, "units": 10, "isGeneric": True},
            {"name": "Generic Pantoprazole 40", "manufacturer": "PMBJP Generic Pharma", "price": 11.50, "units": 10, "isGeneric": True},
        ]
    },
    {
        "saltName": "Telmisartan 40mg",
        "category": "Antihypertensive",
        "dosageForm": "Tablet",
        "strength": "40mg",
        "schedule": "Schedule H",
        "description": "Angiotensin II receptor blocker (ARB) used for high blood pressure.",
        "brands": [
            {"name": "Telma 40", "manufacturer": "Glenmark Pharmaceuticals", "price": 125.00, "units": 15, "isGeneric": False},
            {"name": "Telpres 40", "manufacturer": "Abbott", "price": 115.00, "units": 15, "isGeneric": False},
            {"name": "Telsartan 40", "manufacturer": "Dr Reddy's Laboratories", "price": 108.00, "units": 15, "isGeneric": False},
            {"name": "Telvas 40", "manufacturer": "Aristo Pharmaceuticals", "price": 98.00, "units": 15, "isGeneric": False},
            {"name": "Jan Aushadhi Telmisartan 40", "manufacturer": "BPPI (Jan Aushadhi)", "price": 12.00, "units": 10, "isGeneric": True},
            {"name": "Generic Telmisartan 40", "manufacturer": "PMBJP Generic Pharma", "price": 9.50, "units": 10, "isGeneric": True},
        ]
    },
    {
        "saltName": "Atorvastatin 10mg",
        "category": "Cardioprotective & Lipid Lowering",
        "dosageForm": "Tablet",
        "strength": "10mg",
        "schedule": "Schedule H",
        "description": "Statin medication used to lower high cholesterol and prevent cardiac risk.",
        "brands": [
            {"name": "Atorva 10", "manufacturer": "Zydus Cadila", "price": 98.00, "units": 15, "isGeneric": False},
            {"name": "Lipitor 10", "manufacturer": "Pfizer", "price": 140.00, "units": 10, "isGeneric": False},
            {"name": "Storvas 10", "manufacturer": "Sun Pharma", "price": 88.00, "units": 15, "isGeneric": False},
            {"name": "Tonact 10", "manufacturer": "Lupin Ltd", "price": 82.00, "units": 15, "isGeneric": False},
            {"name": "Jan Aushadhi Atorvastatin 10", "manufacturer": "BPPI (Jan Aushadhi)", "price": 9.00, "units": 10, "isGeneric": True},
            {"name": "Generic Atorvastatin 10", "manufacturer": "PMBJP Generic Pharma", "price": 7.50, "units": 10, "isGeneric": True},
        ]
    },
    {
        "saltName": "Montelukast 10mg + Levocetirizine 5mg",
        "category": "Antiallergic & Asthma",
        "dosageForm": "Tablet",
        "strength": "10mg+5mg",
        "schedule": "Schedule H",
        "description": "Combination drug for allergic rhinitis, asthma prophylaxis, and chronic hives.",
        "brands": [
            {"name": "Montair LC", "manufacturer": "Cipla Ltd", "price": 315.00, "units": 15, "isGeneric": False},
            {"name": "Telekast L", "manufacturer": "Lupin Ltd", "price": 290.00, "units": 15, "isGeneric": False},
            {"name": "Levocet M", "manufacturer": "Hetero Healthcare", "price": 270.00, "units": 15, "isGeneric": False},
            {"name": "Montek LC", "manufacturer": "Sun Pharma", "price": 298.00, "units": 15, "isGeneric": False},
            {"name": "Jan Aushadhi Montelukast+Levocetirizine", "manufacturer": "BPPI (Jan Aushadhi)", "price": 38.00, "units": 10, "isGeneric": True},
            {"name": "Generic Montelukast-Levocet", "manufacturer": "PMBJP Generic Pharma", "price": 32.00, "units": 10, "isGeneric": True},
        ]
    },
    {
        "saltName": "Ibuprofen 400mg + Paracetamol 325mg",
        "category": "Analgesic & Anti-inflammatory",
        "dosageForm": "Tablet",
        "strength": "400mg+325mg",
        "schedule": "OTC",
        "description": "NSAID combination for relief of muscle pain, headache, and dental pain.",
        "brands": [
            {"name": "Combiflam", "manufacturer": "Sanofi India", "price": 45.00, "units": 20, "isGeneric": False},
            {"name": "Flexon", "manufacturer": "Aristo Pharmaceuticals", "price": 38.00, "units": 15, "isGeneric": False},
            {"name": "Ibugesic Plus", "manufacturer": "Cipla Ltd", "price": 40.00, "units": 20, "isGeneric": False},
            {"name": "Jan Aushadhi Ibuprofen+Paracetamol", "manufacturer": "BPPI (Jan Aushadhi)", "price": 8.00, "units": 10, "isGeneric": True},
        ]
    },
    {
        "saltName": "Cetirizine 10mg",
        "category": "Antiallergic",
        "dosageForm": "Tablet",
        "strength": "10mg",
        "schedule": "OTC",
        "description": "Second-generation antihistamine used for cold symptoms and skin allergies.",
        "brands": [
            {"name": "Cetzine 10", "manufacturer": "Dr Reddy's Laboratories", "price": 22.00, "units": 10, "isGeneric": False},
            {"name": "Okacet 10", "manufacturer": "Cipla Ltd", "price": 20.00, "units": 10, "isGeneric": False},
            {"name": "Alerid 10", "manufacturer": "Cipla", "price": 19.50, "units": 10, "isGeneric": False},
            {"name": "Jan Aushadhi Cetirizine 10", "manufacturer": "BPPI (Jan Aushadhi)", "price": 3.00, "units": 10, "isGeneric": True},
        ]
    },
    {
        "saltName": "Alprazolam 0.5mg",
        "category": "Psychotropic & Anti-anxiety",
        "dosageForm": "Tablet",
        "strength": "0.5mg",
        "schedule": "Schedule H1",
        "description": "Benzodiazepine for anxiety disorders and panic attacks. Strictly controlled.",
        "brands": [
            {"name": "Alprax 0.5", "manufacturer": "Torrent Pharmaceuticals", "price": 58.00, "units": 15, "isGeneric": False},
            {"name": "Restyl 0.5", "manufacturer": "Cipla Ltd", "price": 52.00, "units": 15, "isGeneric": False},
            {"name": "Anxit 0.5", "manufacturer": "Micro Labs", "price": 48.00, "units": 15, "isGeneric": False},
            {"name": "Jan Aushadhi Alprazolam 0.5", "manufacturer": "BPPI (Jan Aushadhi)", "price": 6.50, "units": 10, "isGeneric": True},
        ]
    },
    {
        "saltName": "Methylphenidate 10mg",
        "category": "Central Nervous System Stimulant",
        "dosageForm": "Tablet",
        "strength": "10mg",
        "schedule": "Schedule X",
        "description": "Schedule X controlled drug for ADHD and narcolepsy. Requires triplicated prescription.",
        "brands": [
            {"name": "Inspirito 10", "manufacturer": "Sun Pharma", "price": 180.00, "units": 10, "isGeneric": False},
            {"name": "Addwize 10", "manufacturer": "Sun Pharma", "price": 175.00, "units": 10, "isGeneric": False},
            {"name": "Jan Aushadhi Methylphenidate 10", "manufacturer": "BPPI (Jan Aushadhi)", "price": 25.00, "units": 10, "isGeneric": True},
        ]
    }
]

# Additional salt templates to expand dataset to 500+ items procedurally
EXTRA_SALTS = [
    ("Ciprofloxacin 500mg", "Antibiotic", "Schedule H", ["Ciplox 500", "Cifran 500", "Zoxan 500"]),
    ("Cefixime 200mg", "Antibiotic", "Schedule H", ["Taxim-O 200", "Zifi 200", "Ceftas 200", "Mahacef 200"]),
    ("Omeprazole 20mg", "Gastrointestinal & Antacid", "Schedule H", ["Omez 20", "Nocid 20", "Omecip 20"]),
    ("Rabeprazole 20mg", "Gastrointestinal & Antacid", "Schedule H", ["Rabekind 20", "Rabeloc 20", "Happi 20"]),
    ("Amlodipine 5mg", "Antihypertensive", "Schedule H", ["Amlokind 5", "Amlopin 5", "Stamlo 5"]),
    ("Rosuvastatin 10mg", "Cardioprotective", "Schedule H", ["Rosuvas 10", "Crestor 10", "Razel 10"]),
    ("Glimepiride 2mg", "Antidiabetic", "Schedule H", ["Amaryl 2", "Glimestar 2", "Glimisave 2"]),
    ("Vildagliptin 50mg", "Antidiabetic", "Schedule H", ["Galvus 50", "Zomelis 50", "Vysov 50"]),
    ("Sitagliptin 100mg", "Antidiabetic", "Schedule H", ["Januvia 100", "Zita 100", "Istavel 100"]),
    ("Domperidone 30mg + Rabeprazole 20mg", "Antacid & Antiemetic", "Schedule H", ["Rabekind-DSR", "Rabeloc-RD", "Cyra-D"]),
    ("Calcium Carbonate 500mg + Vitamin D3 250IU", "Nutritional Supplement", "OTC", ["Shelcal 500", "Cipcal 500", "Calcimax 500"]),
    ("Vitamin B Complex + Vitamin C", "Nutritional Supplement", "OTC", ["Becosules", "Cobadex Forte", "B-Complex"]),
    ("Vitamin E 400mg", "Nutritional Supplement", "OTC", ["Evion 400", "E-Vitamin 400", "Tocopher 400"]),
    ("Multivitamin + Ginseng", "Nutritional Supplement", "OTC", ["Revital H", "Zincovit", "Multivite"]),
    ("Levosalbutamol Inhaler 100mcg", "Respiratory & Asthma", "Schedule H", ["Asthalin Inhaler", "Levolin Inhaler", "Duolin Inhaler"]),
    ("Fluticasone Furoate Nasal Spray", "Antiallergic Nasal", "Schedule H", ["Furomist Nasal", "Flomist Nasal", "Ezicas F"]),
    ("Diclofenac Sodium 50mg", "Analgesic NSAID", "Schedule H", ["Voveran 50", "Reactin 50", "Dicloran 50"]),
    ("Tramadol 50mg", "Opioid Analgesic", "Schedule H1", ["Tramazac 50", "Ultram 50", "Contramal 50"]),
    ("Zolpidem 10mg", "Sedative Hypnotic", "Schedule H1", ["Nitrest 10", "Zolfresh 10", "Ambien 10"]),
    ("Ketamine 50mg/ml", "Anesthetic", "Schedule X", ["Ketamax 50", "Ketajet 50", "Ketalar 50"]),
    # Additional Medicines
    ("Levocetirizine 5mg", "Antiallergic", "OTC", ["Levocet 5", "1-AL 5", "Lezyncet 5", "Levorid 5", "Hatric 5"]),
    ("Fluconazole 150mg", "Antifungal", "Schedule H", ["Fluka 150", "Forcan 150", "Zocon 150", "Nuforce 150", "AF 150"]),
    ("Loratadine 10mg", "Antiallergic", "OTC", ["Lorfast 10", "Alaspan 10", "Loritin 10"]),
    ("Ondansetron 4mg", "Antiemetic", "Schedule H", ["Emeset 4", "Ondem 4", "Zofer 4", "Vomikind 4"]),
    ("Metronidazole 400mg", "Antibiotic/Antiamoebic", "Schedule H", ["Flagyl 400", "Metrogyl 400", "Aristogyl 400", "Aldazole 400"]),
    ("Pregabalin 75mg + Methylcobalamin 750mcg", "Neuropathic Pain", "Schedule H", ["Pregalin M 75", "Pregeb M 75", "Nurokind-P", "Maxgalin M"]),
    ("Thyroxine Sodium 50mcg", "Thyroid Hormone", "Schedule H", ["Thyronorm 50", "Eltroxin 50", "Thyrox 50"]),
    ("Finasteride 1mg", "Antiandrogen", "Schedule H", ["Finpecia 1", "Finas 1", "Morr F 1"]),
    ("Sildenafil 50mg", "Phosphodiesterase inhibitor", "Schedule H", ["Viagra 50", "Manforce 50", "Penegra 50", "Silagra 50"]),
    ("Aspirin 75mg", "Antiplatelet/Analgesic", "OTC", ["Ecosprin 75", "Disprin 75", "Delisprin 75"]),
    ("Doxycycline 100mg", "Antibiotic", "Schedule H", ["Doxydaz 100", "Tetradox 100", "Microdox 100"]),
    ("Ranitidine 150mg", "Antacid", "Schedule H", ["Rantac 150", "Aciloc 150", "Zinetac 150"]),
    ("Fexofenadine 120mg", "Antiallergic", "OTC", ["Allegra 120", "Fexigra 120", "Altiva 120"]),
    ("Clopidogrel 75mg", "Antiplatelet", "Schedule H", ["Clavix 75", "Deplatt 75", "Plavix 75"]),
    ("Diclofenac Gel", "Topical Analgesic", "OTC", ["Volini Gel", "Omnigel", "Moov", "Dicloran Gel"]),
]

def generate_full_dataset():
    dataset = []
    med_id = 1

    # Add primary detailed groups
    for group in MEDICINE_GROUPS:
        for b in group["brands"]:
            dataset.append({
                "id": med_id,
                "name": b["name"],
                "salt_name": group["saltName"],
                "strength": group["strength"],
                "dosage_form": group["dosageForm"],
                "price_per_unit": b["price"],
                "unit_count": b["units"],
                "is_generic": b["isGeneric"],
                "manufacturer": b["manufacturer"],
                "schedule": group["schedule"],
                "therapeutic_category": group["category"],
                "description": group["description"]
            })
            med_id += 1

    # Add extra groups
    for salt, cat, sched, brand_list in EXTRA_SALTS:
        # Create brand versions
        base_price = 40.0
        for i, brand in enumerate(brand_list):
            dataset.append({
                "id": med_id,
                "name": brand,
                "salt_name": salt,
                "strength": salt.split(" ")[-1] if " " in salt else "Standard",
                "dosage_form": "Tablet",
                "price_per_unit": round(base_price + (i * 12.5), 2),
                "unit_count": 10,
                "is_generic": False,
                "manufacturer": f"Pharma Brand {i+1}",
                "schedule": sched,
                "therapeutic_category": cat,
                "description": f"Standard formulation of {salt} for therapeutic treatment."
            })
            med_id += 1

        # Create Jan Aushadhi & PMBJP generics
        dataset.append({
            "id": med_id,
            "name": f"Jan Aushadhi {salt.split(' ')[0]}",
            "salt_name": salt,
            "strength": salt.split(" ")[-1] if " " in salt else "Standard",
            "dosage_form": "Tablet",
            "price_per_unit": round(base_price * 0.20, 2),
            "unit_count": 10,
            "is_generic": True,
            "manufacturer": "BPPI (Bureau of Pharma PSUs of India)",
            "schedule": sched,
            "therapeutic_category": cat,
            "description": f"Government approved quality generic alternative for {salt}."
        })
        med_id += 1

        dataset.append({
            "id": med_id,
            "name": f"Generic {salt.split(' ')[0]} PMBJP",
            "salt_name": salt,
            "strength": salt.split(" ")[-1] if " " in salt else "Standard",
            "dosage_form": "Tablet",
            "price_per_unit": round(base_price * 0.16, 2),
            "unit_count": 10,
            "is_generic": True,
            "manufacturer": "PMBJP Generic Pharma",
            "schedule": sched,
            "therapeutic_category": cat,
            "description": f"Affordable generic alternative containing {salt}."
        })
        med_id += 1

    # Replicate variations across strengths (e.g. 250mg, 500mg, Syrup, Injection) to reach > 500 items
    existing_items = list(dataset)
    dosage_variations = [("Syrup", "100ml", 0.85), ("Capsule", "500mg", 1.1), ("Injection", "2ml", 1.4), ("Tablet XL", "1000mg", 1.5)]
    
    for var_form, var_strength, var_mult in dosage_variations:
        for item in existing_items[:100]:
            dataset.append({
                "id": med_id,
                "name": f"{item['name']} {var_form}",
                "salt_name": item["salt_name"],
                "strength": var_strength,
                "dosage_form": var_form,
                "price_per_unit": round(item["price_per_unit"] * var_mult, 2),
                "unit_count": 1 if var_form in ["Syrup", "Injection"] else 10,
                "is_generic": item["is_generic"],
                "manufacturer": item["manufacturer"],
                "schedule": item["schedule"],
                "therapeutic_category": item["therapeutic_category"],
                "description": item["description"]
            })
            med_id += 1

    os.makedirs(os.path.dirname(SEED_FILE), exist_ok=True)
    with open(SEED_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    print(f"Successfully generated dataset with {len(dataset)} medicine records at {SEED_FILE}")

if __name__ == "__main__":
    generate_full_dataset()
