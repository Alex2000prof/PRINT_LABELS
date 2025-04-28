# template_viewer.py
import json
from PyQt5.QtWidgets import QWidget, QGraphicsView, QGraphicsScene, QVBoxLayout
from PyQt5.QtGui import QPixmap, QFont, QPainter
from PyQt5.QtCore import Qt
import qrcode, barcode
from template_editor import TEMPLATE_CONFIG, DEFAULT_QR_SIZE, DEFAULT_BC_SIZE, PLACEHOLDER
import os

class TemplateViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Просмотр шаблона этикетки')
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        layout = QVBoxLayout(self)
        layout.addWidget(self.view)
        self.load()

    def load(self):
        self.scene.clear()

        # Создаём файл, если он отсутствует
        if not os.path.exists(TEMPLATE_CONFIG):
            with open(TEMPLATE_CONFIG, 'w', encoding='utf-8') as f:
                json.dump([], f)

        try:
            with open(TEMPLATE_CONFIG, encoding='utf-8') as f:
                items = json.load(f)
        except json.JSONDecodeError:
            # Если файл повреждён — перезаписываем пустым
            items = []
            with open(TEMPLATE_CONFIG, 'w', encoding='utf-8') as f:
                json.dump(items, f)

        for d in items:
            x, y = d['x'], d['y']
            if d['type'] == 'text':
                t = self.scene.addText(d.get('text', PLACEHOLDER['text']), QFont('Arial', 12))
                t.setDefaultTextColor(Qt.black)
                t.setPos(x, y)
            elif d['type'] == 'qr':
                w, h = d.get('w', DEFAULT_QR_SIZE[0]), d.get('h', DEFAULT_QR_SIZE[1])
                img = qrcode.make(PLACEHOLDER['qr']).resize((int(w), int(h)))
                img.save('tmp_qr.png')
                pix = QPixmap('tmp_qr.png')
                self.scene.addPixmap(pix).setPos(x, y)
            elif d['type'] == 'bar':
                w, h = d.get('w', DEFAULT_BC_SIZE[0]), d.get('h', DEFAULT_BC_SIZE[1])
                code = barcode.get('code128', PLACEHOLDER['bar'], writer=barcode.writer.ImageWriter())
                fn = code.save('tmp_bar')
                pix = QPixmap(fn + '.png').scaled(int(w), int(h), Qt.KeepAspectRatio)
                self.scene.addPixmap(pix).setPos(x, y)
