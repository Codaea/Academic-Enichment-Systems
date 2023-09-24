from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4



c = canvas.Canvas("hello.pdf", pagesize=A4)


from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))


# title draw
c.setFont('Arial', 30) # increase font size to 30
c.drawString(105, 800, "Academic Enrichment Request")

# name and teacher draw

c.setFont('Arial', 12) 
c.drawString(50, 750, "{{Name}}, You Have Been Requested By {{Teacher}}. Please go to class {{Class}} at {{Room}}.")
c.drawString(50, 730, "Proirity Level {{Priority}}")


# main body draw





c.showPage()
c.save()