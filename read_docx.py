import zipfile
import xml.etree.ElementTree as ET
import sys
import os

def read_docx(path):
    try:
        if not os.path.exists(path):
            return f"Error: File not found {path}"
        with zipfile.ZipFile(path, 'r') as docx:
            xml_content = docx.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            paragraphs = tree.findall('.//w:p', namespaces)
            text = []
            for p in paragraphs:
                texts = p.findall('.//w:t', namespaces)
                if texts:
                    text.append(''.join(t.text for t in texts))
            return '\n'.join(text)
    except Exception as e:
        return f"Error reading {path}: {str(e)}"

out1 = read_docx(r"c:\Users\User\-SIMDCCONR01\📘 DOCUMENTAÇÃO TÉCNICA DO SISTEMA para automação de laudos periciais.docx")
out2 = read_docx(r"c:\Users\User\-SIMDCCONR01\DOCUMENTO COMPLEMENTAR PARA OUTPUTS.docx")

with open(r"c:\Users\User\-SIMDCCONR01\docx_output.txt", "w", encoding="utf-8") as f:
    f.write("=== DOC 1 ===\n")
    f.write(out1)
    f.write("\n=== DOC 2 ===\n")
    f.write(out2)
