import os
import tempfile
import qrcode
from barcode import Code128
from barcode.writer import ImageWriter
from PyQt5 import QtCore
from PyQt5.QtCore import QRect, QSizeF, Qt, QPoint
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QComboBox,
    QDialog, QSpinBox, QStyledItemDelegate, QAbstractItemView, QCheckBox,
    QLineEdit
)
from PyQt5.QtGui import QPainter, QFont, QCursor, QPixmap, QImage, QPen
from PyQt5.QtPrintSupport import QPrinter, QPrinterInfo, QPrintDialog
import logging

from db import connect_to_db as get_connection
from task_dialog import TaskDialog
import resources.resources_rc as rc
from datetime import datetime
# Инициализируем Qt-ресурсы (картинки, SVG и т.п.)
rc.qInitResources()

logging.basicConfig(
    filename=os.path.join(os.getcwd(), "label_printer.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)

LABEL_W_MM = 58
LABEL_H_MM = 40

class PrintWidget(QWidget):
    def __init__(self, task_id, store_id, user_id, user_full_name):
        super().__init__()

        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
           "SELECT 1 FROM DITE_FabricTask WHERE ID = ? AND Fabric = ?",
           (task_id, store_id)
        )
        if cur.fetchone() is None:
           QMessageBox.critical(None, "Доступ запрещён",
                                f"У вас нет доступа к ТЗ #{task_id}.")
           conn.close()
           return
        conn.close()

        
        self.task_id = task_id
        self.store_id = store_id
        self.user_id = user_id
        self.user_full_name = user_full_name
        self.table_data = []  # список кортежей (ID_articul, articul, h_loc, h_rus, size, count)

        logging.info(f"Init PrintWidget: task_id={task_id}, store_id={store_id}, user_id={user_id}, user_full_name={user_full_name}")

        # Верхний блок: заголовок и PDF-флажок
        outer = QVBoxLayout(self)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск артикула…")
        self.search.textChanged.connect(self.filter_table)
        outer.addWidget(self.search)

        self.lbl_tz = QLabel(f"ТЗ: {self.task_id}")
        self.lbl_tz.setFont(QFont("Arial", 84, QFont.Bold))
        self.lbl_tz.setAlignment(Qt.AlignCenter)
        outer.addWidget(self.lbl_tz)

        # Основной макет: таблица слева, кнопки справа
        main_layout = QHBoxLayout()
        outer.addLayout(main_layout)

        # Левый блок: выбор принтера + таблица
        left = QVBoxLayout()
        main_layout.addLayout(left, stretch=4)

        lbl_printer = QLabel("Принтер:")
        lbl_printer.setFont(QFont("Arial", 14))
        left.addWidget(lbl_printer)

        self.printer_combo = QComboBox()
        self.printer_combo.setFont(QFont("Arial", 12))
        for pi in QPrinterInfo.availablePrinters():
            self.printer_combo.addItem(pi.printerName())
        default = QPrinterInfo.defaultPrinter().printerName()
        if default and self.printer_combo.findText(default) >= 0:
            self.printer_combo.setCurrentText(default)
        left.addWidget(self.printer_combo)

        self.table = QTableWidget(0, 4)
        self.table.setFont(QFont("Arial", 14))
        self.table.setHorizontalHeaderLabels(["Артикул", "Рост", "Размер", "Кол-во"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setSelectionMode(self.table.MultiSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(48)

        class SpinBoxDelegate(QStyledItemDelegate):
            def createEditor(self, parent, option, index):
                if index.column() == 3:
                    spin = QSpinBox(parent)
                    spin.setRange(0, 9999)
                    spin.setFont(QFont("Arial", 14))
                    return spin
                return super().createEditor(parent, option, index)
            def setEditorData(self, editor, index):
                if index.column() == 3:
                    editor.setValue(int(index.model().data(index, Qt.EditRole)))
                else:
                    super().setEditorData(editor, index)
            def setModelData(self, editor, model, index):
                if index.column() == 3:
                    model.setData(index, editor.value(), Qt.EditRole)
                else:
                    super().setModelData(editor, model, index)

        self.table.setItemDelegateForColumn(3, SpinBoxDelegate(self.table))
        left.addWidget(self.table)

    

        # Правый блок: кнопки
        right = QVBoxLayout()
        main_layout.addLayout(right, stretch=1)
        right.setAlignment(Qt.AlignTop)

        buttons = [
            ("🔲 Выделить всё", self.table.selectAll),
            ("❌ Снять выделение", self.table.clearSelection),
            ("🖨️ Печать", self.print_selected),
            ("🔄 Обновить", self.load_data),
            ("⚙️ Сменить ТЗ", self.change_task),
        ]
        for text, slot in buttons:
            btn = QPushButton(text)
            btn.setFont(QFont("Arial", 12))
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.clicked.connect(slot)
            right.addWidget(btn)

        self.load_data()
        logging.info("PrintWidget initialized")


    def filter_table(self, text):
        text = text.strip().lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)  # колонка «Артикул»
            if item is None:
                self.table.setRowHidden(row, False)
            else:
                match = text in item.text().lower()
                self.table.setRowHidden(row, not match)    


    def change_task(self):
        dlg = TaskDialog(self.store_id)
        if dlg.exec_() == QDialog.Accepted and hasattr(dlg, 'selected'):
            self.task_id = dlg.selected
            self.lbl_tz.setText(f"ТЗ: {self.task_id}")
            self.load_data()

    def load_data(self):
        self.table.setRowCount(0)
        self.table_data.clear()

        query = f"""
            SELECT art.ID AS ID_Articul,
                   art.Articul AS Articul,
                   h.Heights AS HeightLocal,
                   h.HeightsRus AS HeightRus,
                   s.[36], s.[38], s.[40], s.[42], s.[44],
                   s.[46], s.[48], s.[50], s.[52], s.[54],
                   s.[56], s.[58], s.[60], s.[62], s.[64],
                   s.[66], s.[68], s.[70], s.[72]
            FROM DITE_FabricTask_ArticulsSizes s
            JOIN DITE_FabricTask_Articuls a
              ON a.ID=s.ID_Articuls AND a.ID_FabricTask={self.task_id}
            JOIN DITE_Articuls art
              ON art.Articul=a.Articul
            JOIN DITE_Articuls_Types typ
              ON typ.Gender=art.Gender AND typ.Type=art.Types
            JOIN DITE_Articuls_Types_Heights h
              ON h.ID_Types=typ.ID AND h.HeightsRus=s.HeightsRus
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        conn.close()

        for row in rows:
            id_art, articul, h_loc, h_rus = row[0], row[1], row[2], row[3]
            for idx, size in enumerate(cols[4:], start=4):
                cnt = row[idx]
                try:
                    cnt = int(cnt or 0)
                except ValueError:
                    continue
                if cnt > 0:
                    self.table_data.append((id_art, articul, h_loc, h_rus, size, cnt))
                    r = self.table.rowCount()
                    self.table.insertRow(r)
                    self.table.setItem(r, 0, QTableWidgetItem(articul))
                    self.table.setItem(r, 1, QTableWidgetItem(str(h_rus)))
                    self.table.setItem(r, 2, QTableWidgetItem(size))
                    self.table.setItem(r, 3, QTableWidgetItem(str(cnt)))
                    for c in range(3):
                        self.table.item(r, c).setFlags(self.table.item(r, c).flags() & ~Qt.ItemIsEditable)

    def _print_many(self, id_art, articul, h_loc, h_rus, size):
        """
        Генерирует штрих-код и QR-код, возвращает шесть параметров:
        пути файлов bar_file, qr_file, а также строки barcode_str и qr_str.
        """
        ts = datetime.now().strftime("%Y%m%d-%H%M%S%f")

        barcode_str = f"{articul}-{h_loc}_{size}"
        qr_str = f"{self.user_id}-{ts}"

        # штрих-код без подписи
        bar_base = os.path.join(tempfile.gettempdir(), f"bar_{ts}")
        writer = ImageWriter()
        opts = {
            'module_width': 0.8,
            'module_height': 30.0,
            'quiet_zone': 1.0,
            'font_size': 0,
            'text_distance': 0,
            'write_text': False
        }
        Code128(barcode_str, writer=writer).save(bar_base, opts)
        bar_file = bar_base + ".png"

        # QR-код
        qr_file = os.path.join(tempfile.gettempdir(), f"qr_{ts}.png")
        qrcode.make(qr_str).save(qr_file)

        return bar_file, qr_file, barcode_str, qr_str

    def print_selected(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одну строку.")
            return
        total = 0
        for idx in sel:
            row = idx.row()
            try:
                cnt = int(self.table.item(row, 3).text())
            except:
                cnt = 0
            total += cnt

        reply = QMessageBox.question(
            self,
            "Подтвердите печать",
            f"Будет напечатано {total} этикеток. Продолжить?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        # Настраиваем принтер (или PDF)
        # 1) Настраиваем принтер (или PDF) — делаем один раз
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPrinterName(self.printer_combo.currentText())
        printer.setOutputFormat(QPrinter.NativeFormat)
        printer.setPaperSize(QSizeF(LABEL_W_MM, LABEL_H_MM), QPrinter.Millimeter)
        printer.setFullPage(True)

        dpi_x = printer.logicalDpiX()
        px_per_mm = dpi_x / 25.4 


        # 2) Если это native-печать, показываем диалог один раз
        # dlg = QPrintDialog(printer, self)
        # if dlg.exec_() != QDialog.Accepted:
        #     return

        # 3) Создаём painter один раз и начинаем рисовать
        painter = QPainter()
        if not painter.begin(printer):
            QMessageBox.warning(self, "Ошибка", "Не удалось начать печать.")
            return

        # Для каждой выбранной строки и каждого count печатаем отдельный ярлык
        for idx in sel:
            id_art, articul, h_loc, h_rus, size, cnt = self.table_data[idx.row()]
            cnt = int(self.table.item(idx.row(), 3).text())
            for _ in range(cnt):
                # Генерируем bar/QR и возвращаем пути и строки
                bar_file, qr_file, barcode_str, qr_str = self._print_many(
                    id_art, articul, h_loc, h_rus, size
                )

                # --- рисуем ярлык в QPixmap 480×480 px ---
                # --- рисуем ярлык в QPixmap 480×480 px ---
                # --- динамически рассчитываем размер pixmap в пикселях ---
                # --- плотный layout блоков, по центру ---
                pix_w = int(LABEL_W_MM * px_per_mm)
                pix_h = int(LABEL_H_MM * px_per_mm)

                pix = QPixmap(pix_w, pix_h)
                pix.fill(Qt.white)
                p = QPainter(pix)

                # 1) рамка
                p.setPen(QPen(Qt.black, 2))
                p.drawRect(1, 1, pix_w-2, pix_h-2)

                y = 1

                # 2) артикул (крупный)
                font = QFont("Arial")
                font.setPixelSize(int(pix_h * 0.24))
                font.setBold(True)
                p.setFont(font)
                h1 = p.fontMetrics().height()
                p.drawText(QRect(0, y, pix_w, h1), Qt.AlignHCenter, articul)
                y += h1 + 1

                # 3) рост/размер
                font.setPixelSize(int(pix_h * 0.18))
                p.setFont(font)
                h2 = p.fontMetrics().height()
                p.drawText(QRect(0, y, pix_w, h2), Qt.AlignHCenter, f"{h_rus}/{size}")
                y += h2 + 2

                # 4) QR – 30% ширины
                qr_size = int(pix_w * 0.15)
                qr_img = QImage(qr_file)
                if not qr_img.isNull():
                    qr_img = qr_img.scaled(qr_size, qr_size,
                                        Qt.KeepAspectRatio,
                                        Qt.SmoothTransformation)
                    p.drawImage(QPoint((pix_w - qr_size)//2, y), qr_img)
                    y += qr_size + 6

                # 5) Штрих-код – 80% ширины, прямо под QR
                bar_w = int(pix_w * 0.94)
                bar_h = int(pix_h * 0.22)

                # вычисляем отступ в пикселях
                bottom_margin_mm = 2
                bottom_margin_px = int(bottom_margin_mm * px_per_mm)

                # загружаем и масштабируем изображение
                bar_img = QImage(bar_file)
                if not bar_img.isNull():
                    bar_img = bar_img.scaled(bar_w, bar_h,
                                            Qt.KeepAspectRatio,
                                            Qt.SmoothTransformation)

                    # реальная ширина после масштабирования
                    real_w = bar_img.width()

                    # X-координата для центрирования
                    x_bar = (pix_w - real_w) // 2

                    # Y-координата — от низа pixmap:
                    y_bar = pix_h - bar_img.height() - bottom_margin_px

                    p.drawImage(QPoint(x_bar, y_bar), bar_img)

                p.end()


                
                # Настраиваем native-печать через диалог



                



                # --- выводим готовый pixmap в принтер/PDF ---
                painter.drawPixmap(0, 0, pix)
                printer.newPage()

                # --- логируем в базу каждой этикетки ---
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute(
                        """
                        INSERT INTO DITE_Articuls_LabelsPrint
                        (ID_Articul, Articul, HS, Barcode, QrCode, PrintIDSurname, ID_FabricTask)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (id_art, articul, f"{h_loc}_{size}", barcode_str, qr_str,
                         self.user_id, self.task_id)
                    )
                    conn.commit()
                except Exception:
                    logging.exception("Ошибка записи лога печати ярлыка")
                finally:
                    try: conn.close()
                    except: pass

        painter.end()


BasicPrintWidget = PrintWidget









