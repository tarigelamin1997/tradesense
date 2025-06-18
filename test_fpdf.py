from fpdf import FPDF, XPos, YPos

pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", size=12)
pdf.cell(200,
         10,
         text="fpdf2 is working!",
         new_x=XPos.LMARGIN,
         new_y=YPos.NEXT)
pdf.output("test_output.pdf")
