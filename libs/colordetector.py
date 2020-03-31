import subprocess
import re
# path = '/Users/jandevera/Documents/cmyk_A4.pdf'

RE_FLOAT = re.compile("[01].[0-9]+")
CMYK_NCOLORS = 4

def parseCMYK(pdf_file):
  gs_inkcov = subprocess.Popen(["gs", "-o", "-", "-sDEVICE=inkcov", pdf_file], stdout=subprocess.PIPE)
  for raw_line in iter(gs_inkcov.stdout.readline, b''):
    line = raw_line.decode('utf8').rstrip()
    fields = line.split()
    if (len(fields) >= CMYK_NCOLORS and all(RE_FLOAT.match(fields[i]) for i in range(CMYK_NCOLORS))):
      cmyk = tuple(float(value) for value in fields[0:CMYK_NCOLORS])
      yield cmyk

def is_color(c, m, y, k):
  return c > 0 or m > 0 or y > 0

def count_page_types(pdf_file):
  nc = []
  for n, page in enumerate(parseCMYK(pdf_file), 1):
    if is_color(*page):
      nc.append(n)
  return nc



if __name__ == '__main__':
  nc = count_page_types(path)
  print (nc)