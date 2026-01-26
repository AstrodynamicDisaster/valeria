# Mappings
python scripts/export_190_concepts.py --mapping-from parsing/rentarider/bucket.yml --mapping-out parsing/rentarider/mapping.json
python scripts/export_190_concepts.py --mapping-from parsing/tarantin/bucket.yml --mapping-out parsing/tarantin/mapping.json
python scripts/export_190_concepts.py --mapping-from parsing/tepuy_bazan/bucket.yml --mapping-out parsing/tepuy_bazan/mapping.json
python scripts/export_190_concepts.py --mapping-from parsing/tepuy_burger/bucket.yml --mapping-out parsing/tepuy_burger/mapping.json
python scripts/export_190_concepts.py --mapping-from parsing/umbrella/bucket.yml --mapping-out parsing/umbrella/mapping.json
python scripts/export_190_concepts.py --mapping-from parsing/tepuy_on_road/bucket.yml --mapping-out parsing/tepuy_on_road/mapping.json
python scripts/export_190_concepts.py --mapping-from parsing/alopeke/bucket.yml --mapping-out parsing/alopeke/mapping.json
python scripts/export_190_concepts.py --mapping-from parsing/tremenda/bucket.yml --mapping-out parsing/tremenda/mapping.json
python scripts/export_190_concepts.py --mapping-from parsing/rossitruck/bucket.yml --mapping-out parsing/rossitruck/mapping.json
python scripts/export_190_concepts.py --mapping-from parsing/fleets/bucket.yml --mapping-out parsing/fleets/mapping.json
python scripts/export_190_concepts.py --mapping-from parsing/lapsa/bucket.yml --mapping-out parsing/lapsa/mapping.json

# 190s
python 190.py --cif B09979378 --year 2025 --mapping parsing/rentarider/mapping.json --out parsing/rentarider/txt/rentarider_complementaria.txt --tipo-declaracion C --numero-identificativo 1900000000002 --id-declaracion-anterior 1900000000001
python 190.py --cif B40601734 --year 2025 --mapping parsing/tarantin/mapping.json --out parsing/tarantin/txt/tarantin_complementaria.txt --tipo-declaracion C --numero-identificativo 1900000000002 --id-declaracion-anterior 1900000000001
python 190.py --cif B42633750 --year 2025 --mapping parsing/tepuy_bazan/mapping.json --out parsing/tepuy_bazan/txt/tepuy_bazan_complementaria.txt --tipo-declaracion C --numero-identificativo 1900000000002 --id-declaracion-anterior 1900000000001
python 190.py --cif B42524694 --year 2025 --mapping parsing/tepuy_burger/mapping.json --out parsing/tepuy_burger/txt/tepuy_burger_complementaria.txt --tipo-declaracion C --numero-identificativo 1900000000002 --id-declaracion-anterior 1900000000001
python 190.py --cif B06982748 --year 2025 --mapping parsing/umbrella/mapping.json --out parsing/umbrella/txt/umbrella_complementaria.txt --tipo-declaracion C --numero-identificativo 1900000000002 --id-declaracion-anterior 1900000000001
python 190.py --cif B44781235 --year 2025 --mapping parsing/tepuy_on_road/mapping.json --out parsing/tepuy_on_road/txt/tepuy_on_road_complementaria.txt --tipo-declaracion C --numero-identificativo 1900000000002 --id-declaracion-anterior 1900000000001
python 190.py --cif B87933685 --year 2025 --mapping parsing/alopeke/mapping.json --out parsing/alopeke/txt/alopeke_original.txt --numero-identificativo 1900000000001
python 190.py --cif B66891201 --year 2025 --mapping parsing/tremenda/mapping.json --out parsing/tremenda/txt/tremenda_complementaria.txt --tipo-declaracion C --numero-identificativo 1900000000002 --id-declaracion-anterior 1900000000001
python 190.py --cif B56744949 --year 2025 --mapping parsing/rossitruck/mapping.json --out parsing/rossitruck/txt/rossitruck_complementaria.txt --tipo-declaracion C --numero-identificativo 1900000000002 --id-declaracion-anterior 1900000000001
python 190.py --cif B75604249 --year 2025 --mapping parsing/fleets/mapping.json --out parsing/fleets/txt/fleets_complementaria.txt --tipo-declaracion C --numero-identificativo 1900000000002 --id-declaracion-anterior 1900000000001
python 190.py --cif B19766534 --year 2025 --mapping parsing/lapsa/mapping.json --out parsing/lapsa/txt/lapsa.txt --tipo-declaracion S --numero-identificativo 1900000000003 --id-declaracion-anterior 1900000000001

# Fixing province
python scripts/update_modelo190_ccc.py --input parsing/rentarider/txt/rentarider_original.txt --output parsing/rentarider/txt/rentarider_original.txt
python scripts/update_modelo190_ccc.py --input parsing/tarantin/txt/tarantin_original.txt --output parsing/tarantin/txt/tarantin_original.txt
python scripts/update_modelo190_ccc.py --input parsing/tepuy_bazan/txt/Tepuy_Bazan_original.txt --output parsing/tepuy_bazan/txt/Tepuy_Bazan_original.txt
python scripts/update_modelo190_ccc.py --input parsing/tepuy_burger/txt/Tepuy_Burger_original.txt --output parsing/tepuy_burger/txt/Tepuy_Burger_original.txt
python scripts/update_modelo190_ccc.py --input parsing/umbrella/txt/Umbrella_original.txt --output parsing/umbrella/txt/Umbrella_original.txt
python scripts/update_modelo190_ccc.py --input parsing/tepuy_on_road/txt/Tepuy_On_Road_original.txt --output parsing/tepuy_on_road/txt/Tepuy_On_Road_original.txt
python scripts/update_modelo190_ccc.py --input parsing/tremenda/txt/LaTremenda_original.txt --output parsing/tremenda/txt/LaTremenda_original.txt
python scripts/update_modelo190_ccc.py --input parsing/rossitruck/txt/Rossitruck_original.txt --output parsing/rossitruck/txt/Rossitruck_original.txt
python scripts/update_modelo190_ccc.py --input parsing/fleets/txt/fleets_original.txt --output parsing/fleets/txt/fleets_original.txt

# Special cases
python scripts/update_modelo190_ccc.py --input parsing/tepuy_gocho/txt/Tepuy_Gocho_original.txt --output parsing/tepuy_gocho/txt/Tepuy_Gocho_original.txt
python scripts/update_modelo190_ccc.py --input parsing/pideya/txt/PideYA_original.txt --output parsing/pideya/txt/PideYA_original.txt