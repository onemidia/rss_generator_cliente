import os
from flask import Flask, render_template, request, redirect, url_for, send_file, make_response
from werkzeug.utils import secure_filename
from datetime import datetime
import xml.etree.ElementTree as ET

app = Flask(__name__)

# Configurações
UPLOAD_FOLDER = 'uploads'
FEED_FOLDER = 'feeds'
ALLOWED_EXTENSIONS = {'txt'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['FEED_FOLDER'] = FEED_FOLDER

# Garante que as pastas existem
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
                preco_formatado = preco.replace('.', ',')  # Substitui ponto por vírgula

                item = ET.SubElement(channel, "item")
                ET.SubElement(item, "title").text = produto
                ET.SubElement(item, "link").text = f"https://seusite.com/produtos/{codigo}"
                ET.SubElement(item, "description").text = f"R$ {preco_formatado}/{unidade}"
                ET.SubElement(item, "pubDate").text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
                ET.SubElement(item, "guid").text = codigo

    # Salvar XML com indentação correta
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(arquivo_xml, encoding="utf-8", xml_declaration=True)
    
    print(f"Feed RSS gerado para {cliente} em: {arquivo_xml}")

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files or 'cliente' not in request.form:
            return redirect(request.url)

        file = request.files['file']
        cliente = request.form['cliente'].strip().lower()

        if file.filename == '' or not cliente:
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{cliente}.txt")
            file.save(file_path)

            # Gera o feed RSS
            txt_para_rss(cliente, file_path)

            return f'Arquivo recebido e feed RSS atualizado! Acesse em: /feed/{cliente}.xml'

    return render_template('index.html')

@app.route('/feed/<cliente>.xml')
def serve_feed(cliente):
    """Retorna o feed XML de um cliente com cache controlado"""
    arquivo_xml = os.path.join(app.config['FEED_FOLDER'], f"{cliente}.xml")
    if os.path.exists(arquivo_xml):
        response = make_response(send_file(arquivo_xml, mimetype='application/rss+xml'))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return "Feed não encontrado!", 404

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=10000)
