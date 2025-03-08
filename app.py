import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime
import xml.etree.ElementTree as ET

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
FEED_FOLDER = 'feeds'  # Pasta onde os feeds serão armazenados
ALLOWED_EXTENSIONS = {'txt'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['FEED_FOLDER'] = FEED_FOLDER

# Criar as pastas se não existirem
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FEED_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def txt_para_rss(cliente, arquivo_txt):
    """Gera um feed RSS a partir de um arquivo TXT para um cliente específico"""
    arquivo_xml = os.path.join(app.config['FEED_FOLDER'], f"{cliente}.xml")

    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")

    ET.SubElement(channel, "title").text = f"Feed de {cliente}"
    ET.SubElement(channel, "link").text = f"https://rss-generator.onrender.com/feed/{cliente}.xml"
    ET.SubElement(channel, "description").text = f"Lista de produtos de {cliente}"
    ET.SubElement(channel, "pubDate").text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

    with open(arquivo_txt, "r") as f:
        for linha in f:
            dados = linha.strip().split(";")
            if len(dados) >= 4:
                codigo, produto, preco, unidade = dados[:4]

                item = ET.SubElement(channel, "item")
                ET.SubElement(item, "title").text = produto
                ET.SubElement(item, "link").text = f"https://seusite.com/produtos/{codigo}"
                ET.SubElement(item, "description").text = f"{produto} - R${preco}/{unidade}"
                ET.SubElement(item, "pubDate").text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
                ET.SubElement(item, "guid").text = codigo

    tree = ET.ElementTree(root)
    tree.write(arquivo_xml, encoding="utf-8", xml_declaration=True)
    print(f"Feed RSS gerado para {cliente} em: {arquivo_xml}")

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        cliente = request.form.get('cliente')  # Obtém o nome do cliente do formulário
        if not cliente:
            return "Erro: Informe um nome de cliente!", 400

        if 'file' not in request.files:
            return "Erro: Nenhum arquivo enviado!", 400

        file = request.files['file']
        if file.filename == '':
            return "Erro: Arquivo sem nome!", 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{cliente}.txt")
            file.save(file_path)

            txt_para_rss(cliente, file_path)
            return f"Arquivo recebido e feed RSS gerado! Acesse: <a href='/feed/{cliente}.xml'>Seu Feed</a>"

    return render_template('index.html')

@app.route('/feed/<cliente>.xml')
def serve_feed(cliente):
    """Rota para servir o feed XML do cliente"""
    file_path = os.path.join(app.config['FEED_FOLDER'], f"{cliente}.xml")
    if os.path.exists(file_path):
        return send_from_directory(app.config['FEED_FOLDER'], f"{cliente}.xml")
    else:
        return "Feed não encontrado!", 404

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=10000)
