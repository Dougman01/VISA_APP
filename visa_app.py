import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QLineEdit, QPushButton, QComboBox,
    QMessageBox, QDialog, QTreeWidget, QTreeWidgetItem, QHeaderView,
    QCheckBox, QFileDialog, QSizePolicy
)
from PyQt5.QtCore import QDate, Qt
from datetime import datetime, timedelta
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER


class VisaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Banco de dados VISA - VISA")
        self.setGeometry(100, 100, 1000, 700)

        self.db_name = "visa_bd.db"
        self.conn = None
        self.cursor = None
        self.init_db()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        self.create_main_menu()

    def init_db(self):
        """Inicializa o banco de dados SQLite e cria a tabela 'estabelecimentos' se ela não existir.
        
        A coluna 'motivo' foi adicionada conforme a solicitação.
        """
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS estabelecimentos (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Estabelecimento TEXT NOT NULL,
                    CNPJ_CPF TEXT NOT NULL UNIQUE,
                    Grupo TEXT,
                    CNAE TEXT,
                    Grau_de_risco TEXT,
                    Responsavel TEXT,
                    CPF_Responsavel TEXT,
                    Endereco TEXT,
                    Telefone TEXT,
                    Email TEXT,
                    Projeto_Arquitetonico TEXT,
                    Data_ultima_inspecao TEXT,
                    Reinspecao TEXT,
                    Alvara TEXT,
                    Data_proxima_inspecao TEXT,
                    Situacao TEXT,
                    motivo TEXT
                )
                """
            )
            self.conn.commit()
            print("Banco de dados 'visa_bd.db' e tabela 'estabelecimentos' verificados/criados.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erro no Banco de Dados", f"Erro ao inicializar o banco de dados: {e}")
            self.close()

    def clear_layout(self, layout):
        """Função auxiliar para limpar todos os widgets de um layout."""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def create_main_menu(self):
        """Cria a interface do menu principal com os três botões principais."""
        self.clear_layout(self.main_layout)

        title_label = QLabel("Banco de dados VISA")
        title_label.setObjectName("title_label")
        title_label.setStyleSheet(
            "font-size: 28pt; font-weight: bold; color: #2c3e50; padding: 40px;"
        )
        title_label.setAlignment(Qt.AlignCenter)

        self.main_layout.addWidget(title_label)
        self.main_layout.setAlignment(Qt.AlignCenter)

        btn_cadastro = QPushButton("Cadastro")
        btn_cadastro.clicked.connect(self.open_cadastro_window)
        btn_cadastro.setFixedSize(300, 50)
        self.main_layout.addWidget(btn_cadastro, alignment=Qt.AlignCenter)

        btn_inserir_inspecao = QPushButton("Inserir Inspeção")
        btn_inserir_inspecao.clicked.connect(self.open_inserir_inspecao_window)
        btn_inserir_inspecao.setFixedSize(300, 50)
        self.main_layout.addWidget(btn_inserir_inspecao, alignment=Qt.AlignCenter)

        btn_pesquisar = QPushButton("Pesquisar / Exportar")
        btn_pesquisar.clicked.connect(self.open_pesquisar_window)
        btn_pesquisar.setFixedSize(300, 50)
        self.main_layout.addWidget(btn_pesquisar, alignment=Qt.AlignCenter)

        # Configurações de estilo global para os botões do menu principal
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #e0e0e0;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 10px;
                font-size: 12pt;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #388E3C;
            }
            """
        )

    def calculate_situacao(self, ultima_inspecao_str):
        """
        Calcula a situação do alvará e a data da próxima inspeção.
        A lógica da situação é:
        - VIGENTE: de 90 dias ou mais para a próxima inspeção.
        - REQUER ATENÇÃO: entre 60 e 89 dias para a próxima inspeção.
        - VENCIDO: menos de 60 dias para a próxima inspeção (ou já passou).
        """
        if not ultima_inspecao_str:
            return "Não Informado", ""

        try:
            ultima_inspecao = datetime.strptime(ultima_inspecao_str, "%d/%m/%Y")
            proxima_inspecao_dt = ultima_inspecao + timedelta(days=365)
            today = datetime.now()
            dias_restantes = (proxima_inspecao_dt - today).days

            if dias_restantes >= 90:
                situacao = "VIGENTE"
            elif 60 <= dias_restantes < 90:
                situacao = "REQUER ATENÇÃO"
            else:
                situacao = "VENCIDO"

            return situacao, proxima_inspecao_dt.strftime("%d/%m/%Y")

        except ValueError:
            return "Erro de Formato", ""

    # --- Funções para Cadastro ---
    def open_cadastro_window(self):
        """Abre a janela para cadastrar um novo estabelecimento."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Cadastro de Estabelecimento")
        dialog.setGeometry(200, 200, 700, 700)
        dialog.setModal(True)

        layout = QFormLayout()
        dialog.setLayout(layout)

        labels_info = [
            ("Estabelecimento:", "Estabelecimento"),
            ("CNPJ ou CPF:", "CNPJ_CPF"),
            ("Grupo:", "Grupo"),
            ("CNAE:", "CNAE"),
            ("Grau de risco:", "Grau_de_risco"),
            ("Responsável:", "Responsavel"),
            ("CPF do Responsável:", "CPF_Responsavel"),
            ("Endereço:", "Endereco"),
            ("Telefone:", "Telefone"),
            ("E-mail:", "Email"),
            ("Projeto Arquitetônico:", "Projeto_Arquitetonico"),
        ]

        self.entries = {}
        for label_text_display, entry_key in labels_info:
            if entry_key in ["Grupo", "Grau_de_risco", "Projeto_Arquitetonico"]:
                combo = QComboBox()
                if entry_key == "Grupo":
                    combo.addItems(["ALIMENTOS", "SERVIÇOS DE SAÚDE"])
                elif entry_key == "Grau_de_risco":
                    combo.addItems(["ALTO RISCO", "BAIXO RISCO A", "BAIXO RISCO B"])
                elif entry_key == "Projeto_Arquitetonico":
                    combo.addItems([
                        "APROVADO E EXECUTADO", "APROVADO E NÃO EXECUTADO",
                        "EM ANÁLISE", "NÃO APROVADO", "NÃO SE APLICA"
                    ])
                self.entries[entry_key] = combo
                layout.addRow(QLabel(label_text_display), combo)
            else:
                entry = QLineEdit()
                self.entries[entry_key] = entry
                layout.addRow(QLabel(label_text_display), entry)

        btn_salvar = QPushButton("Salvar Cadastro")
        btn_salvar.clicked.connect(lambda: self.salvar_cadastro(dialog))
        layout.addRow(btn_salvar)

        dialog.exec_()

    def salvar_cadastro(self, window):
        """Salva os dados do novo estabelecimento no banco de dados."""
        estabelecimento = self.entries["Estabelecimento"].text()
        cnpj_cpf = self.entries["CNPJ_CPF"].text()
        grupo = self.entries["Grupo"].currentText()
        cnae = self.entries["CNAE"].text()
        grau_de_risco = self.entries["Grau_de_risco"].currentText()
        responsavel = self.entries["Responsavel"].text()
        cpf_responsavel = self.entries["CPF_Responsavel"].text()
        endereco = self.entries["Endereco"].text()
        telefone = self.entries["Telefone"].text()
        email = self.entries["Email"].text()
        projeto_arquitetonico = self.entries["Projeto_Arquitetonico"].currentText()

        if not estabelecimento or not cnpj_cpf:
            QMessageBox.warning(window, "Campos Obrigatórios", "Estabelecimento e CNPJ/CPF são obrigatórios.")
            return

        if cnae and not re.match(r"^\d{4}-\d/\d{2}$", cnae):
            QMessageBox.warning(window, "Formato CNAE", "O CNAE deve estar no formato xxxx-x/xx (ex: 0000-0/00).")
            return

        try:
            self.cursor.execute(
                """
                INSERT INTO estabelecimentos (
                    Estabelecimento, CNPJ_CPF, Grupo, CNAE, Grau_de_risco,
                    Responsavel, CPF_Responsavel, Endereco, Telefone, Email,
                    Projeto_Arquitetonico, Data_ultima_inspecao, Reinspecao,
                    Alvara, Data_proxima_inspecao, Situacao, motivo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    estabelecimento, cnpj_cpf, grupo, cnae, grau_de_risco,
                    responsavel, cpf_responsavel, endereco, telefone, email,
                    projeto_arquitetonico, "", "", "", "", "", ""
                ),
            )
            self.conn.commit()
            QMessageBox.information(window, "Sucesso", "Estabelecimento salvo com sucesso!")
            window.accept()
        except sqlite3.IntegrityError:
            QMessageBox.warning(window, "Erro de Cadastro", "CNPJ/CPF já cadastrado.")
        except sqlite3.Error as e:
            QMessageBox.critical(window, "Erro ao Salvar", f"Erro ao salvar estabelecimento: {e}")

    # --- Funções para Inserir Inspeção ---
    def open_inserir_inspecao_window(self):
        """Abre a janela para inserir ou atualizar dados de inspeção de um estabelecimento."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Inserir / Atualizar Inspeção")
        dialog.setGeometry(200, 200, 800, 600)
        dialog.setModal(True)

        layout = QVBoxLayout()
        dialog.setLayout(layout)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Pesquisar por CNPJ ou CPF:"))
        self.search_cnpj_cpf_entry = QLineEdit()
        search_layout.addWidget(self.search_cnpj_cpf_entry)
        btn_buscar = QPushButton("Buscar")
        btn_buscar.clicked.connect(lambda: self.load_estabelecimento_for_inspection(dialog))
        search_layout.addWidget(btn_buscar)
        layout.addLayout(search_layout)

        self.inspection_entries = {}
        self.current_establishment_id = None

        form_layout = QFormLayout()
        layout.addLayout(form_layout)

        # Mapeamento de chaves do BD para rótulos e tipos de widget
        # A coluna 'motivo' e suas opções foram adicionadas aqui.
        labels_data = {
            "ID": {"label": "ID:", "type": "readonly_entry"},
            "Estabelecimento": {"label": "Estabelecimento:", "type": "entry"},
            "CNPJ_CPF": {"label": "CNPJ ou CPF:", "type": "entry"},
            "Grupo": {"label": "Grupo:", "type": "combobox", "options": ["ALIMENTOS", "SERVIÇOS DE SAÚDE"]},
            "CNAE": {"label": "CNAE:", "type": "entry"},
            "Grau_de_risco": {"label": "Grau de risco:", "type": "combobox", "options": ["ALTO RISCO", "BAIXO RISCO A", "BAIXO RISCO B"]},
            "Responsavel": {"label": "Responsável:", "type": "entry"},
            "CPF_Responsavel": {"label": "CPF do Responsável:", "type": "entry"},
            "Endereco": {"label": "Endereço:", "type": "entry"},
            "Telefone": {"label": "Telefone:", "type": "entry"},
            "Email": {"label": "E-mail:", "type": "entry"},
            "Projeto_Arquitetonico": {"label": "Projeto Arquitetônico:", "type": "combobox", "options": ["APROVADO E EXECUTADO", "APROVADO E NÃO EXECUTADO", "EM ANÁLISE", "NÃO APROVADO", "NÃO SE APLICA"]},
            "Data_ultima_inspecao": {"label": "Data da última inspeção (DD/MM/AAAA):", "type": "entry"},
            "Reinspecao": {"label": "Reinspeção:", "type": "checkbutton"},
            "Alvara": {"label": "Alvará:", "type": "combobox", "options": ["LIBERADO", "EM ANÁLISE", "DISPENSADO"]},
            "motivo": {"label": "Motivo da última inspeção:", "type": "combobox", "options": ["Liberação de alvará", "Renovação de alvará", "Denúncia", "Surto de TDAH", "Interesse da visa", "A pedido de outros órgãos"]},
            "Data_proxima_inspecao": {"label": "Data da próxima inspeção (calculada):", "type": "readonly_entry"},
            "Situacao": {"label": "Situação (calculada):", "type": "readonly_entry"},
        }

        for key, info in labels_data.items():
            if info["type"] == "combobox":
                combo = QComboBox()
                combo.addItems(info["options"])
                self.inspection_entries[key] = combo
                form_layout.addRow(QLabel(info["label"]), combo)
            elif info["type"] == "checkbutton":
                self.reinspecao_checkbox = QCheckBox("Sim")
                self.inspection_entries[key] = self.reinspecao_checkbox
                form_layout.addRow(QLabel(info["label"]), self.reinspecao_checkbox)
            elif info["type"] == "readonly_entry":
                entry = QLineEdit()
                entry.setReadOnly(True)
                self.inspection_entries[key] = entry
                form_layout.addRow(QLabel(info["label"]), entry)
            else:
                entry = QLineEdit()
                self.inspection_entries[key] = entry
                form_layout.addRow(QLabel(info["label"]), entry)

        btn_salvar_inspecao = QPushButton("Salvar Inspeção")
        btn_salvar_inspecao.clicked.connect(lambda: self.salvar_inspecao(dialog))
        layout.addWidget(btn_salvar_inspecao)

        dialog.exec_()

    def load_estabelecimento_for_inspection(self, parent_window):
        """Carrega os dados de um estabelecimento para a janela de inspeção com base no CNPJ/CPF."""
        cnpj_cpf = self.search_cnpj_cpf_entry.text()

        if not cnpj_cpf:
            QMessageBox.warning(parent_window, "Pesquisa Vazia", "Por favor, digite o CNPJ ou CPF para pesquisar.")
            return

        self.cursor.execute("SELECT * FROM estabelecimentos WHERE CNPJ_CPF=?", (cnpj_cpf,))
        data = self.cursor.fetchone()

        if data:
            self.current_establishment_id = data[0]

            db_columns = [
                "ID", "Estabelecimento", "CNPJ_CPF", "Grupo", "CNAE", "Grau_de_risco",
                "Responsavel", "CPF_Responsavel", "Endereco", "Telefone", "Email",
                "Projeto_Arquitetonico", "Data_ultima_inspecao", "Reinspecao",
                "Alvara", "Data_proxima_inspecao", "Situacao", "motivo"
            ]

            for i, key in enumerate(db_columns):
                value = data[i] if data[i] is not None else ""
                widget = self.inspection_entries.get(key)
                if isinstance(widget, QLineEdit):
                    widget.setText(str(value))
                elif isinstance(widget, QComboBox):
                    widget.setCurrentText(str(value))
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(value == "Sim")
            
            ultima_inspecao_val = self.inspection_entries["Data_ultima_inspecao"].text()
            situacao, proxima_inspecao = self.calculate_situacao(ultima_inspecao_val)

            self.inspection_entries["Data_proxima_inspecao"].setText(proxima_inspecao)
            self.inspection_entries["Situacao"].setText(situacao)

            QMessageBox.information(parent_window, "Sucesso", "Dados do estabelecimento carregados para edição.")
        else:
            QMessageBox.warning(parent_window, "Não Encontrado", "Nenhum estabelecimento encontrado com o CNPJ/CPF informado.")
            self.clear_inspection_fields()

    def clear_inspection_fields(self):
        """Limpa todos os campos da janela de inserção/atualização de inspeção."""
        self.current_establishment_id = None
        self.search_cnpj_cpf_entry.clear()
        
        for key, widget in self.inspection_entries.items():
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(False)

    def salvar_inspecao(self, window):
        """Salva as alterações e os dados de inspeção no banco de dados."""
        if self.current_establishment_id is None:
            QMessageBox.warning(window, "Erro", "Nenhum estabelecimento selecionado para atualização.")
            return

        data_to_save = {}
        for key in self.inspection_entries:
            widget = self.inspection_entries[key]
            if isinstance(widget, QLineEdit):
                data_to_save[key] = widget.text()
            elif isinstance(widget, QComboBox):
                data_to_save[key] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                data_to_save[key] = "Sim" if widget.isChecked() else "Não"

        ultima_inspecao_str = data_to_save.get("Data_ultima_inspecao", "")
        if ultima_inspecao_str:
            try:
                datetime.strptime(ultima_inspecao_str, "%d/%m/%Y")
            except ValueError:
                QMessageBox.warning(window, "Formato de Data Inválido", "Data da última inspeção deve ser DD/MM/AAAA.")
                return

        situacao, proxima_inspecao_str = self.calculate_situacao(ultima_inspecao_str)
        data_to_save["Data_proxima_inspecao"] = proxima_inspecao_str
        data_to_save["Situacao"] = situacao

        try:
            self.cursor.execute(
                """
                UPDATE estabelecimentos SET
                    Estabelecimento=?, CNPJ_CPF=?, Grupo=?, CNAE=?, Grau_de_risco=?,
                    Responsavel=?, CPF_Responsavel=?, Endereco=?, Telefone=?, Email=?,
                    Projeto_Arquitetonico=?, Data_ultima_inspecao=?, Reinspecao=?,
                    Alvara=?, Data_proxima_inspecao=?, Situacao=?, motivo=?
                WHERE ID=?
                """,
                (
                    data_to_save["Estabelecimento"], data_to_save["CNPJ_CPF"],
                    data_to_save["Grupo"], data_to_save["CNAE"],
                    data_to_save["Grau_de_risco"], data_to_save["Responsavel"],
                    data_to_save["CPF_Responsavel"], data_to_save["Endereco"],
                    data_to_save["Telefone"], data_to_save["Email"],
                    data_to_save["Projeto_Arquitetonico"], data_to_save["Data_ultima_inspecao"],
                    data_to_save["Reinspecao"], data_to_save["Alvara"],
                    data_to_save["Data_proxima_inspecao"], data_to_save["Situacao"],
                    data_to_save["motivo"], self.current_establishment_id
                ),
            )
            self.conn.commit()
            QMessageBox.information(window, "Sucesso", "Dados da inspeção salvos/atualizados com sucesso!")
            window.accept()
        except sqlite3.Error as e:
            QMessageBox.critical(window, "Erro ao Salvar", f"Erro ao salvar dados da inspeção: {e}")

    # --- Funções para Pesquisar / Exportar ---
    def open_pesquisar_window(self):
        """Abre a janela de pesquisa e exportação de relatórios."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Pesquisar e Exportar Relatórios")
        dialog.setGeometry(200, 200, 1000, 700)
        dialog.setModal(True)

        main_layout = QVBoxLayout()
        dialog.setLayout(main_layout)

        filter_buttons_frame = QWidget()
        filter_layout = QHBoxLayout()
        filter_buttons_frame.setLayout(filter_layout)

        filter_layout.addWidget(QPushButton("Por Grupo", clicked=self.show_filter_grupo))
        filter_layout.addWidget(QPushButton("Por CNAE", clicked=self.show_filter_cnae))
        filter_layout.addWidget(QPushButton("Por Grau de Risco", clicked=self.show_filter_grau_risco))
        filter_layout.addWidget(QPushButton("Por Reinspeção", clicked=self.show_filter_reinspecao))
        filter_layout.addWidget(QPushButton("Por Situação", clicked=self.show_filter_situacao))
        filter_layout.addWidget(QPushButton("Por Motivo", clicked=self.show_filter_motivo)) # Novo botão
        filter_layout.addWidget(QPushButton("Todos os Estabelecimentos", clicked=self.show_filter_todos))

        main_layout.addWidget(filter_buttons_frame)

        self.filter_options_frame = QWidget()
        self.filter_options_layout = QVBoxLayout()
        self.filter_options_frame.setLayout(self.filter_options_layout)
        main_layout.addWidget(self.filter_options_frame)
        self.filter_options_frame.setVisible(False)

        self.tree_widget = QTreeWidget()
        # O número de colunas foi atualizado para incluir a nova coluna 'motivo'
        self.tree_widget.setColumnCount(18)
        self.tree_widget.setHeaderLabels([
            "ID", "Estabelecimento", "CNPJ_CPF", "Grupo", "CNAE", "Grau_de_risco",
            "Responsavel", "CPF_Responsavel", "Endereco", "Telefone", "Email",
            "Projeto_Arquitetonico", "Data_ultima_inspecao", "Reinspecao",
            "Alvara", "Data_proxima_inspecao", "Situacao", "Motivo" # Nova coluna adicionada
        ])
        self.tree_widget.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tree_widget.setSelectionMode(QTreeWidget.ExtendedSelection)

        main_layout.addWidget(self.tree_widget)

        export_buttons_frame = QWidget()
        export_layout = QHBoxLayout()
        export_buttons_frame.setLayout(export_layout)
        export_layout.addWidget(QPushButton("Exportar para PDF", clicked=self.export_to_pdf))
        export_layout.addWidget(QPushButton("Exportar Tudo para PDF", clicked=lambda: self.export_to_pdf(export_all=True)))
        main_layout.addWidget(export_buttons_frame)

        self.show_filter_todos() # Carrega todos os estabelecimentos por padrão

        dialog.exec_()
        
    def show_filter_todos(self):
        self.clear_layout(self.filter_options_layout)
        self.filter_options_frame.setVisible(False)
        self.load_data_to_tree()

    def show_filter_grupo(self):
        self.clear_layout(self.filter_options_layout)
        self.filter_options_frame.setVisible(True)

        options = ["ALIMENTOS", "SERVIÇOS DE SAÚDE"]
        combo = QComboBox()
        combo.addItems(options)
        
        btn = QPushButton("Filtrar")
        btn.clicked.connect(lambda: self.load_data_to_tree(filter_by="Grupo", filter_value=combo.currentText()))

        layout = QHBoxLayout()
        layout.addWidget(QLabel("Filtrar por Grupo:"))
        layout.addWidget(combo)
        layout.addWidget(btn)

        self.filter_options_layout.addLayout(layout)

    def show_filter_cnae(self):
        self.clear_layout(self.filter_options_layout)
        self.filter_options_frame.setVisible(True)

        entry = QLineEdit()
        btn = QPushButton("Filtrar")
        btn.clicked.connect(lambda: self.load_data_to_tree(filter_by="CNAE", filter_value=entry.text()))

        layout = QHBoxLayout()
        layout.addWidget(QLabel("Filtrar por CNAE:"))
        layout.addWidget(entry)
        layout.addWidget(btn)

        self.filter_options_layout.addLayout(layout)

    def show_filter_grau_risco(self):
        self.clear_layout(self.filter_options_layout)
        self.filter_options_frame.setVisible(True)

        options = ["ALTO RISCO", "BAIXO RISCO A", "BAIXO RISCO B"]
        combo = QComboBox()
        combo.addItems(options)

        btn = QPushButton("Filtrar")
        btn.clicked.connect(lambda: self.load_data_to_tree(filter_by="Grau_de_risco", filter_value=combo.currentText()))

        layout = QHBoxLayout()
        layout.addWidget(QLabel("Filtrar por Grau de Risco:"))
        layout.addWidget(combo)
        layout.addWidget(btn)
        
        self.filter_options_layout.addLayout(layout)
        
    def show_filter_reinspecao(self):
        self.clear_layout(self.filter_options_layout)
        self.filter_options_frame.setVisible(True)

        options = ["Sim", "Não"]
        combo = QComboBox()
        combo.addItems(options)

        btn = QPushButton("Filtrar")
        btn.clicked.connect(lambda: self.load_data_to_tree(filter_by="Reinspecao", filter_value=combo.currentText()))
        
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Filtrar por Reinspeção:"))
        layout.addWidget(combo)
        layout.addWidget(btn)

        self.filter_options_layout.addLayout(layout)
        
    def show_filter_situacao(self):
        self.clear_layout(self.filter_options_layout)
        self.filter_options_frame.setVisible(True)

        options = ["VIGENTE", "REQUER ATENÇÃO", "VENCIDO", "Não Informado"]
        combo = QComboBox()
        combo.addItems(options)

        btn = QPushButton("Filtrar")
        btn.clicked.connect(lambda: self.load_data_to_tree(filter_by="Situacao", filter_value=combo.currentText()))
        
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Filtrar por Situação:"))
        layout.addWidget(combo)
        layout.addWidget(btn)

        self.filter_options_layout.addLayout(layout)

    def show_filter_motivo(self):
        """Cria o widget de filtro para a nova coluna 'motivo'."""
        self.clear_layout(self.filter_options_layout)
        self.filter_options_frame.setVisible(True)

        options = ["Liberação de alvará", "Renovação de alvará", "Denúncia", "Surto de TDAH", "Interesse da visa", "A pedido de outros órgãos"]
        combo = QComboBox()
        combo.addItems(options)

        btn = QPushButton("Filtrar")
        btn.clicked.connect(lambda: self.load_data_to_tree(filter_by="motivo", filter_value=combo.currentText()))
        
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Filtrar por Motivo:"))
        layout.addWidget(combo)
        layout.addWidget(btn)

        self.filter_options_layout.addLayout(layout)
    
    def load_data_to_tree(self, filter_by=None, filter_value=None):
        """Carrega os dados do banco de dados para o QTreeWidget com ou sem filtro."""
        self.tree_widget.clear()
        query = "SELECT * FROM estabelecimentos"
        params = []

        if filter_by and filter_value:
            query += f" WHERE {filter_by} LIKE ?"
            params.append(f"%{filter_value}%")
            
        self.cursor.execute(query, params)
        data = self.cursor.fetchall()

        for row in data:
            item = QTreeWidgetItem([str(col) if col is not None else "" for col in row])
            self.tree_widget.addTopLevelItem(item)

    def export_to_pdf(self, export_all=False):
        """Exporta os dados selecionados ou todos para um arquivo PDF."""
        if export_all:
            self.cursor.execute("SELECT * FROM estabelecimentos")
            data_to_export = self.cursor.fetchall()
        else:
            selected_items = self.tree_widget.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Exportação", "Por favor, selecione as linhas que deseja exportar.")
                return
            data_to_export = [[item.text(i) for i in range(self.tree_widget.columnCount())] for item in selected_items]

        if not data_to_export:
            QMessageBox.information(self, "Exportação", "Não há dados para exportar.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Relatório PDF", "", "PDF Files (*.pdf)")
        if not file_path:
            return

        doc = SimpleDocTemplate(file_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        title = Paragraph(f"Relatório de Estabelecimentos - {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['h1'])
        story.append(title)
        story.append(Paragraph("<br/>", styles['Normal']))

        headers = [self.tree_widget.headerItem().text(i) for i in range(self.tree_widget.columnCount())]
        
        # Cria a tabela de dados
        data = [headers] + data_to_export
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ])
        
        table = Table(data, hAlign=TA_CENTER)
        table.setStyle(table_style)
        
        story.append(table)

        doc.build(story)
        QMessageBox.information(self, "Sucesso", f"Relatório PDF salvo em: {file_path}")

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = VisaApp()
    window.show()
    sys.exit(app.exec_())

