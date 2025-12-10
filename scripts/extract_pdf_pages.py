import csv
from pypdf import PdfReader, PdfWriter

input_pdf = "parsing/danik/danik.pdf"
csv_file = "parsing/danik/pages.csv"
output_pdf = "enfermedad_danik.pdf"

# Read page numbers from CSV
pages = []
with open(csv_file) as f:
    reader = csv.reader(f)
    for row in reader:
        for item in row:
            if item.strip().isdigit():
                pages.append(int(item.strip()))

# Create output
reader = PdfReader(input_pdf)
writer = PdfWriter()

for p in pages:
    writer.add_page(reader.pages[p - 1])  # p-1 because pages are zero-indexed

with open(output_pdf, "wb") as f:
    writer.write(f)

print("Done.")
