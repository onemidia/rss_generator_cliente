import os
import logging
from flask import Flask, request, redirect
from werkzeug.utils import secure_filename
from flask import render_template

app = Flask(__name__)

# Configurações do aplicativo
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Função para verificar se o arquivo tem a extensão permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Função para converter o arquivo .txt para o formato RSS
def txt_para_rss(file_path, xml_path, titulo, link, descricao):
    import xml.etree.ElementTree as ET

    # Criando o feed RSS
    rss = ET.Element('rss', version="2.0")
    channel = ET.SubElement(rss, 'channel')

    title = ET.SubElement(channel, 'title')
    title.text = titulo
    link_tag = ET.SubElement(channel, 'link')
    link_tag.text = link
    description = ET.SubElement(channel, 'description')
    description.text = descricao

    # Lendo o conteúdo do arquivo .txt
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Adicionando os itens ao feed
    for line in lines:
        product_name, product_value = line.strip().split('-')
        item = ET.SubElement(channel, 'item')

        item_title = ET.SubElement(item, 'title')
        item_title.text = product_name.strip()

        item_link = ET.SubElement(item, 'link')
        item_link.text = link

        item_description = ET.SubElement(item, 'description')
        item_description.text = f'{product_value.strip().replace(".", ",")}'

    # Salvando o arquivo XML
    tree = ET.ElementTree(rss)
    tree.write(xml_path)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    try:
        if request.method == 'POST':
            if 'file' not in request.files:
                return redirect(request.url)
            file = request.files['file']
            if file.filename == '':
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                # Gerar o feed RSS para o cliente
                cliente_nome = 'caio'  # Este valor pode vir de algum parâmetro ou banco de dados
                xml_path = f'feeds/{cliente_nome}.xml'
                txt_para_rss(file_path, xml_path, 'Carnes Nobres', 'https://seusite.com/feed', 'Lista de Carnes Nobres e seus preços.')

                # Gerar a URL para o feed
                url = f'/feeds/{cliente_nome}.xml'  # Corrigir a URL

                return f'Arquivo recebido e feed RSS atualizado! Acesse em: {url}'
            else:
                return "Arquivo não permitido. Apenas arquivos .txt são aceitos."
    except Exception as e:
        logging.error(f"Erro no upload de arquivo: {str(e)}")
        return "Erro interno no servidor. Tente novamente mais tarde."

# Rota para acessar o feed gerado
@app.route('/feeds/<cliente_nome>.xml')
def serve_feed(cliente_nome):
    xml_path = f'feeds/{cliente_nome}.xml'
    if os.path.exists(xml_path):
        return send_file(xml_path)
    else:
        return "Feed não encontrado."

if __name__ == '__main__':
    app.run(debug=True)
