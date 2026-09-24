# Convierte referencias «l. N» / «l. N-M» (líneas del archivo de trabajo) en secciones del ensayo
# (§1…§4 c) o apostillas (ap. 1…10), que los estudiantes pueden ubicar en la edición de El Cuenco de Plata.
import re, sys, os, glob, json
CORTES = [(16,'§1'),(86,'§2'),(149,'§2 a'),(209,'§2 b'),(315,'§2 c'),(406,'§3'),(528,'§3 a'),(604,'§3 b'),
          (773,'§4'),(775,'§4 a'),(839,'§4 b'),(885,'§4 c'),(903,'ap. 1'),(1054,'ap. 2'),(1190,'ap. 3'),
          (1252,'ap. 4'),(1428,'ap. 5'),(1487,'ap. 6'),(1628,'ap. 7'),(1673,'ap. 8'),(1731,'ap. 9'),(1837,'ap. 10')]
def seccion(n):
    s = '§1'
    for ini, et in CORTES:
        if n >= ini: s = et
    return s
PAT = re.compile(r'(?<![A-Za-zÁÉÍÓÚáéíóúñÑ])ll?\.\s?(\d{1,4})(?:\s?[-–]\s?(\d{1,4}))?')
def conv(txt):
    def r(m):
        a = int(m.group(1)); b = int(m.group(2)) if m.group(2) else a
        sa, sb = seccion(a), seccion(b)
        return sa if sa == sb else f'{sa}–{sb.replace("§", "") if sa.startswith("§") and sb.startswith("§") else sb}'
    out = PAT.sub(r, txt)
    out = re.sub(r'(§\d(?: [a-c])?|ap\. \d+)(\s*[·,]\s*\1)+', r'\1', out)  # duplicados seguidos
    return out
if __name__ == '__main__':
    docs = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs')
    archivos = glob.glob(docs + '/3d/escenas/*.json') + glob.glob(docs + '/svg/*.svg')
    for f in archivos:
        s = open(f, encoding='utf-8').read(); t = conv(s)
        if t != s:
            open(f, 'w', encoding='utf-8').write(t)
            print('convertido', os.path.basename(f), len(PAT.findall(s)), 'refs')
