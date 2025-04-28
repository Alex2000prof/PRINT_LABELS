import json
from PyQt5.QtWidgets import QWidget, QGraphicsView, QGraphicsScene, QToolBar, QAction, QVBoxLayout, QDialog, QMessageBox
from PyQt5.QtGui import QFont, QPen, QPixmap, QPainter
from PyQt5.QtCore import Qt, QRectF
import qrcode
import barcode

TEMPLATE_CONFIG = 'label_template.json'
MM_TO_PX = 3.78
DEFAULT_QR_SIZE = (30 * MM_TO_PX, 30 * MM_TO_PX)
DEFAULT_BC_SIZE = (60 * MM_TO_PX, 15 * MM_TO_PX)
PLACEHOLDER = {'text': 'ART123456', 'qr': 'QR123456789', 'bar': '1234567890123'}

class TemplateEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Настройка шаблона этикетки (40×80 мм)')
        self.scene = QGraphicsScene(self)
        w_px, h_px = 40 * MM_TO_PX, 80 * MM_TO_PX
        self.scene.setSceneRect(0, 0, w_px, h_px)
        pen = QPen(Qt.black); pen.setWidthF(1.0)
        self.scene.addRect(0, 0, w_px, h_px, pen)

        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

        self.init_ui()
        self.load_template()

    def init_ui(self):
        toolbar = QToolBar()
        for name, slot in [
            ('Добавить текст', self.add_text),
            ('Добавить QR', self.add_qr),
            ('Добавить штрихкод', self.add_bar),
            ('Сохранить', self.save_template),
            ('Просмотр', self.preview),
        ]:
            act = QAction(name, self)
            act.triggered.connect(slot)
            toolbar.addAction(act)

        layout = QVBoxLayout(self)
        layout.addWidget(toolbar)
        layout.addWidget(self.view)

    def add_text(self):
        item = self.scene.addText(PLACEHOLDER['text'], QFont('Arial', 12))
        item.setDefaultTextColor(Qt.black)
        item.setFlags(item.ItemIsMovable | item.ItemIsSelectable)

    def add_qr(self):
        w, h = DEFAULT_QR_SIZE
        rect = self.scene.addRect(10*MM_TO_PX, 10*MM_TO_PX, w, h, QPen(Qt.DotLine))
        rect.setData(0, 'qr')
        rect.setFlags(rect.ItemIsMovable | rect.ItemIsSelectable)

    def add_bar(self):
        w, h = DEFAULT_BC_SIZE
        rect = self.scene.addRect(10*MM_TO_PX, 40*MM_TO_PX, w, h, QPen(Qt.DotLine))
        rect.setData(0, 'bar')
        rect.setFlags(rect.ItemIsMovable | rect.ItemIsSelectable)

    def save_template(self):
        items = []
        for it in self.scene.items():
            kind = it.data(0) or 'text'
            if kind == 'text':
                items.append({
                    'type': 'text',
                    'x': it.pos().x(),
                    'y': it.pos().y(),
                    'text': it.toPlainText()
                })
            else:
                r = it.rect()
                items.append({
                    'type': kind,
                    'x': r.x(), 'y': r.y(),
                    'w': r.width(), 'h': r.height()
                })
        with open(TEMPLATE_CONFIG, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)

    def load_template(self):
        self.scene.clear()
        # Нарисовать только рамку вручную, без повторного вызова __init__
        w_px, h_px = 40 * MM_TO_PX, 80 * MM_TO_PX
        self.scene.setSceneRect(0, 0, w_px, h_px)
        self.scene.addRect(0, 0, w_px, h_px, QPen(Qt.black))
        
        try:
            items = json.load(open(TEMPLATE_CONFIG, encoding='utf-8'))
        except Exception:
            return

        for d in items:
            if d['type'] == 'text':
                txt = self.scene.addText(d['text'], QFont('Arial', 12))
                txt.setDefaultTextColor(Qt.black)
                txt.setPos(d['x'], d['y'])
                txt.setFlags(txt.ItemIsMovable | txt.ItemIsSelectable)
            elif d['type'] in ('qr','bar'):
                pen = QPen(Qt.DotLine)
                rect = self.scene.addRect(d['x'], d['y'], d['w'], d['h'], pen)
                rect.setData(0, d['type'])
                rect.setFlags(rect.ItemIsMovable | rect.ItemIsSelectable)

    def preview(self):
        dlg = QDialog(self)
        dlg.setWindowTitle('Preview Этикетки')
        lay = QVBoxLayout(dlg)
        view = QGraphicsView(); lay.addWidget(view)
        scene = QGraphicsScene(); view.setScene(scene)
        try:
            items = json.load(open(TEMPLATE_CONFIG, encoding='utf-8'))
        except FileNotFoundError:
            QMessageBox.warning(self, 'Ошибка', 'Нет сохранённого шаблона')
            return
        for d in items:
            if d['type']=='text':
                t = scene.addText(d['text'], QFont('Arial', 12))
                t.setPos(d['x'], d['y'])
            elif d['type']=='qr':
                img = qrcode.make(PLACEHOLDER['qr']).resize((int(d['w']),int(d['h'])))
                img.save('tmp_qr.png')
                scene.addPixmap(QPixmap('tmp_qr.png')).setPos(d['x'], d['y'])
            elif d['type']=='bar':
                code = barcode.get('code128', PLACEHOLDER['bar'], writer=barcode.writer.ImageWriter())
                fn = code.save('tmp_bar')
                pix = QPixmap(fn+'.png').scaled(int(d['w']),int(d['h']), Qt.KeepAspectRatio)
                scene.addPixmap(pix).setPos(d['x'], d['y'])
        dlg.resize(200,300)
        dlg.exec_()
