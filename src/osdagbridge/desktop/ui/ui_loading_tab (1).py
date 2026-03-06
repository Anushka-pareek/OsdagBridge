

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QComboBox, QCheckBox,
    QPushButton, QScrollArea, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QDialog,
    QDialogButtonBox, QMessageBox, QSizePolicy, QSpacerItem,
    QAbstractItemView
)


# ─────────────────────────────────────────────────────────────────────────────
#  Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

TITLE_STYLE = (
    "QGroupBox { font-weight: bold; font-size: 9pt; "
    "border: 1px solid #888; border-radius: 4px; margin-top: 8px; "
    "padding-top: 6px; } "
    "QGroupBox::title { subcontrol-origin: margin; left: 8px; "
    "padding: 0 4px 0 4px; }"
)
NOTE_STYLE = "color: #555; font-size: 8pt; font-style: italic;"
WARN_STYLE = "color: #b00; font-size: 8pt;"

STEEL_GRADES = [
    "E 250A", "E 250BR", "E 250B0", "E 275A", "E 300A",
    "E 350A", "E 350BR", "E 410A", "E 450A", "E 550A", "E 600A", "E 650A",
]

IRC6_VEHICLES = [
    "Class A",
    "Class 70R Wheeled",
    "Class 70R Tracked",
    "Class AA Wheeled",
    "Class AA Tracked",
    "Class SV",
    "Fatigue Truck",
]

LOAD_CASES = ["Dead Load (DL)", "Dead Load for Surfacing (DW)",
              "Super-Imposed Dead Load (SIDL)", "Live Load (LL)",
              "Earthquake Load (EL)", "Wind Load (WL)",
              "Temperature Load (TL)", "Custom"]

LOAD_TYPES = ["Point", "Line", "Area"]


def _make_label(text, parent=None, style=None):
    lbl = QLabel(text, parent)
    if style:
        lbl.setStyleSheet(style)
    return lbl


def _make_combo(items, parent=None, fixed_width=None):
    cb = QComboBox(parent)
    cb.addItems(items)
    cb.setStyleSheet("QComboBox { combobox-popup: 0; }")
    cb.setMaxVisibleItems(8)
    if fixed_width:
        cb.setFixedWidth(fixed_width)
    return cb


def _make_line(placeholder="", parent=None, validator=None, fixed_width=None):
    le = QLineEdit(parent)
    le.setPlaceholderText(placeholder)
    if validator:
        le.setValidator(validator)
    if fixed_width:
        le.setFixedWidth(fixed_width)
    return le


def _make_group(title):
    gb = QGroupBox(title)
    gb.setStyleSheet(TITLE_STYLE)
    return gb


def _hr():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    line.setStyleSheet("color: #bbb;")
    return line


# ─────────────────────────────────────────────────────────────────────────────
#  Custom Vehicle Dialog
# ─────────────────────────────────────────────────────────────────────────────

class CustomVehicleDialog(QDialog):
    """Dialog to Add / Edit a custom IRC vehicle."""

    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Live Load Custom Vehicle Add/Edit")
        self.setMinimumWidth(520)
        self._rows = []          # list of [load_kN, spacing_m]
        self._build_ui()
        if data:
            self._populate(data)

    def _build_ui(self):
        main = QVBoxLayout(self)

        # Vehicle name
        row0 = QHBoxLayout()
        row0.addWidget(QLabel("Vehicle Name:"))
        self.le_name = _make_line("e.g. Class B Special")
        row0.addWidget(self.le_name)
        main.addLayout(row0)

        # Axle table
        main.addWidget(QLabel("Axle Loads:"))
        self.tbl = QTableWidget(0, 3)
        self.tbl.setHorizontalHeaderLabels(["No.", "Load (kN)", "Spacing to next (m)"])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.setFixedHeight(160)
        main.addWidget(self.tbl)

        btn_row = QHBoxLayout()
        self.btn_add_axle    = QPushButton("Add Axle")
        self.btn_mod_axle    = QPushButton("Modify")
        self.btn_del_axle    = QPushButton("Delete")
        for b in (self.btn_add_axle, self.btn_mod_axle, self.btn_del_axle):
            btn_row.addWidget(b)
        btn_row.addStretch()
        main.addLayout(btn_row)

        self.btn_add_axle.clicked.connect(self._add_axle_row)
        self.btn_mod_axle.clicked.connect(self._mod_axle_row)
        self.btn_del_axle.clicked.connect(self._del_axle_row)

        # Additional parameters
        params_gb = _make_group("Vehicle Parameters")
        pg = QGridLayout(params_gb)

        dbl = QtGui.QDoubleValidator(0, 1e6, 3)

        self.le_nose_tail   = _make_line("30", validator=dbl)
        self.le_wheel_w     = _make_line("500", validator=dbl)
        self.le_clear_edge  = _make_line("150", validator=dbl)
        self.le_clear_cross = _make_line("1200", validator=dbl)
        self.le_wheel_sp    = _make_line("1.8", validator=dbl)
        self.le_impact      = _make_line("0.25", validator=dbl)

        for i, (lbl, widget, hint) in enumerate([
            ("Min. Nose-to-Tail Distance (m)",      self.le_nose_tail,   "Default: 30"),
            ("Width of Wheel, w (mm)",              self.le_wheel_w,     "Default: 500"),
            ("Min. Clearance – Carriageway Edge (mm)", self.le_clear_edge,"Default: 150"),
            ("Min. Clearance – Crossing Vehicles (mm)", self.le_clear_cross,"Default: 1200"),
            ("Wheel Spacing – Transverse (m)",      self.le_wheel_sp,    "Default: 1.8"),
            ("Impact Factor",                       self.le_impact,      "Default: 0.25"),
        ]):
            pg.addWidget(QLabel(lbl), i, 0)
            pg.addWidget(widget, i, 1)
            pg.addWidget(_make_label(hint, style=NOTE_STYLE), i, 2)

        main.addWidget(params_gb)

        # OK / Cancel
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._validate_and_accept)
        btns.rejected.connect(self.reject)
        main.addWidget(btns)

    # ── axle table helpers ────────────────────────────────────────────────────
    def _add_axle_row(self):
        r = self.tbl.rowCount()
        self.tbl.insertRow(r)
        self.tbl.setItem(r, 0, QTableWidgetItem(str(r + 1)))
        self.tbl.setItem(r, 1, QTableWidgetItem(""))
        spacing_item = QTableWidgetItem("0")
        self.tbl.setItem(r, 2, spacing_item)
        # update row numbers
        for i in range(self.tbl.rowCount()):
            self.tbl.item(i, 0).setText(str(i + 1))
            self.tbl.item(i, 0).setFlags(Qt.ItemIsEnabled)

    def _mod_axle_row(self):
        row = self.tbl.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warning", "Select a row to modify.")

    def _del_axle_row(self):
        row = self.tbl.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warning", "Select a row to delete.")
            return
        self.tbl.removeRow(row)
        for i in range(self.tbl.rowCount()):
            self.tbl.item(i, 0).setText(str(i + 1))

    # ── populate / collect ────────────────────────────────────────────────────
    def _populate(self, data):
        self.le_name.setText(data.get("name", ""))
        for axle in data.get("axles", []):
            r = self.tbl.rowCount()
            self.tbl.insertRow(r)
            self.tbl.setItem(r, 0, QTableWidgetItem(str(r + 1)))
            self.tbl.setItem(r, 1, QTableWidgetItem(str(axle[0])))
            self.tbl.setItem(r, 2, QTableWidgetItem(str(axle[1])))
        for le, key in [
            (self.le_nose_tail,   "nose_tail"),
            (self.le_wheel_w,     "wheel_w"),
            (self.le_clear_edge,  "clear_edge"),
            (self.le_clear_cross, "clear_cross"),
            (self.le_wheel_sp,    "wheel_sp"),
            (self.le_impact,      "impact"),
        ]:
            if key in data:
                le.setText(str(data[key]))

    def get_data(self):
        axles = []
        for r in range(self.tbl.rowCount()):
            load = self.tbl.item(r, 1).text() if self.tbl.item(r, 1) else ""
            sp   = self.tbl.item(r, 2).text() if self.tbl.item(r, 2) else "0"
            axles.append((load, sp))
        return {
            "name":        self.le_name.text(),
            "axles":       axles,
            "nose_tail":   self.le_nose_tail.text(),
            "wheel_w":     self.le_wheel_w.text(),
            "clear_edge":  self.le_clear_edge.text(),
            "clear_cross": self.le_clear_cross.text(),
            "wheel_sp":    self.le_wheel_sp.text(),
            "impact":      self.le_impact.text(),
        }

    def _validate_and_accept(self):
        if not self.le_name.text().strip():
            QMessageBox.warning(self, "Validation", "Vehicle Name is required.")
            return
        if self.tbl.rowCount() == 0:
            QMessageBox.warning(self, "Validation", "At least one axle load is required.")
            return
        self.accept()


# ─────────────────────────────────────────────────────────────────────────────
#  Custom Load Dialog
# ─────────────────────────────────────────────────────────────────────────────

class CustomLoadDialog(QDialog):
    """Dialog to Add / Edit a single custom load entry."""

    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Custom Load Input – Add/Edit")
        self.setMinimumWidth(420)
        self._build_ui()
        if data:
            self._populate(data)

    def _build_ui(self):
        g = QGridLayout(self)
        dbl = QtGui.QDoubleValidator(-1e9, 1e9, 3)

        g.addWidget(QLabel("Load Case:"), 0, 0)
        self.cb_case = _make_combo(LOAD_CASES)
        self.le_custom_case = _make_line("Custom load case name")
        self.le_custom_case.setVisible(False)
        self.cb_case.currentTextChanged.connect(
            lambda t: self.le_custom_case.setVisible(t == "Custom"))
        g.addWidget(self.cb_case, 0, 1)
        g.addWidget(self.le_custom_case, 0, 2)

        g.addWidget(QLabel("Load Type:"), 1, 0)
        self.cb_type = _make_combo(LOAD_TYPES)
        self.cb_type.currentTextChanged.connect(self._on_type_change)
        g.addWidget(self.cb_type, 1, 1)

        # distance from left edge
        g.addWidget(QLabel("Distance from Left Edge (m):"), 2, 0)
        dist_w = QWidget()
        dist_lay = QHBoxLayout(dist_w)
        dist_lay.setContentsMargins(0, 0, 0, 0)
        self.le_dist_start = _make_line("Start", validator=dbl)
        self.le_dist_end   = _make_line("End",   validator=dbl)
        self.lbl_dist_end  = QLabel("to")
        dist_lay.addWidget(self.le_dist_start)
        dist_lay.addWidget(self.lbl_dist_end)
        dist_lay.addWidget(self.le_dist_end)
        g.addWidget(dist_w, 2, 1, 1, 2)

        # distance from CL of bearing
        g.addWidget(QLabel("Distance from CL of Bearing (m):"), 3, 0)
        bear_w = QWidget()
        bear_lay = QHBoxLayout(bear_w)
        bear_lay.setContentsMargins(0, 0, 0, 0)
        self.le_bear_start = _make_line("Start", validator=dbl)
        self.le_bear_end   = _make_line("End",   validator=dbl)
        self.lbl_bear_end  = QLabel("to")
        bear_lay.addWidget(self.le_bear_start)
        bear_lay.addWidget(self.lbl_bear_end)
        bear_lay.addWidget(self.le_bear_end)
        g.addWidget(bear_w, 3, 1, 1, 2)

        self._on_type_change("Point")

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        g.addWidget(btns, 4, 0, 1, 3)

    def _on_type_change(self, t):
        is_point = (t == "Point")
        self.le_dist_end.setVisible(not is_point)
        self.lbl_dist_end.setVisible(not is_point)
        self.le_bear_end.setVisible(not is_point)
        self.lbl_bear_end.setVisible(not is_point)

    def _populate(self, data):
        idx = self.cb_case.findText(data.get("case", ""))
        if idx >= 0:
            self.cb_case.setCurrentIndex(idx)
        idx2 = self.cb_type.findText(data.get("type", "Point"))
        if idx2 >= 0:
            self.cb_type.setCurrentIndex(idx2)
        self.le_dist_start.setText(data.get("dist_start", ""))
        self.le_dist_end.setText(data.get("dist_end", ""))
        self.le_bear_start.setText(data.get("bear_start", ""))
        self.le_bear_end.setText(data.get("bear_end", ""))

    def get_data(self):
        return {
            "case":       self.cb_case.currentText(),
            "type":       self.cb_type.currentText(),
            "dist_start": self.le_dist_start.text(),
            "dist_end":   self.le_dist_end.text(),
            "bear_start": self.le_bear_start.text(),
            "bear_end":   self.le_bear_end.text(),
        }


# ─────────────────────────────────────────────────────────────────────────────
#  Load Combination Dialog
# ─────────────────────────────────────────────────────────────────────────────

class LoadCombinationDialog(QDialog):
    """Dialog to Add / Edit a load combination."""

    def __init__(self, parent=None, available_cases=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Load Combination – Add/Edit")
        self.setMinimumWidth(460)
        self._cases = available_cases or LOAD_CASES
        self._entries = []          # list of (case, factor)
        self._build_ui()
        if data:
            self._populate(data)

    def _build_ui(self):
        main = QVBoxLayout(self)

        top = QGridLayout()
        top.addWidget(QLabel("Combination Name:"), 0, 0)
        self.le_name = _make_line("e.g. ULS_1")
        top.addWidget(self.le_name, 0, 1, 1, 2)

        top.addWidget(QLabel("Load Case:"), 1, 0)
        self.cb_case = _make_combo(self._cases)
        top.addWidget(self.cb_case, 1, 1)

        top.addWidget(QLabel("Load Factor:"), 2, 0)
        self.le_factor = _make_line("1.0",
            validator=QtGui.QDoubleValidator(0, 10, 3))
        top.addWidget(self.le_factor, 2, 1)

        self.btn_add_entry = QPushButton("Add to Table")
        self.btn_add_entry.clicked.connect(self._add_entry)
        top.addWidget(self.btn_add_entry, 2, 2)

        main.addLayout(top)

        self.tbl = QTableWidget(0, 2)
        self.tbl.setHorizontalHeaderLabels(["Load Case", "Load Factor"])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.setFixedHeight(140)
        main.addWidget(self.tbl)

        btn_row = QHBoxLayout()
        self.btn_edit_entry = QPushButton("Edit Selected")
        self.btn_del_entry  = QPushButton("Delete Selected")
        self.btn_edit_entry.clicked.connect(self._edit_entry)
        self.btn_del_entry.clicked.connect(self._del_entry)
        btn_row.addWidget(self.btn_edit_entry)
        btn_row.addWidget(self.btn_del_entry)
        btn_row.addStretch()
        main.addLayout(btn_row)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._validate_and_accept)
        btns.rejected.connect(self.reject)
        main.addWidget(btns)

    def _add_entry(self):
        case   = self.cb_case.currentText()
        factor = self.le_factor.text() or "1.0"
        r = self.tbl.rowCount()
        self.tbl.insertRow(r)
        self.tbl.setItem(r, 0, QTableWidgetItem(case))
        self.tbl.setItem(r, 1, QTableWidgetItem(factor))

    def _edit_entry(self):
        row = self.tbl.currentRow()
        if row < 0:
            return
        idx = self.cb_case.findText(self.tbl.item(row, 0).text())
        if idx >= 0:
            self.cb_case.setCurrentIndex(idx)
        self.le_factor.setText(self.tbl.item(row, 1).text())
        self.tbl.removeRow(row)

    def _del_entry(self):
        row = self.tbl.currentRow()
        if row >= 0:
            self.tbl.removeRow(row)

    def _populate(self, data):
        self.le_name.setText(data.get("name", ""))
        for case, factor in data.get("entries", []):
            r = self.tbl.rowCount()
            self.tbl.insertRow(r)
            self.tbl.setItem(r, 0, QTableWidgetItem(case))
            self.tbl.setItem(r, 1, QTableWidgetItem(str(factor)))

    def get_data(self):
        entries = []
        for r in range(self.tbl.rowCount()):
            entries.append((
                self.tbl.item(r, 0).text(),
                self.tbl.item(r, 1).text(),
            ))
        return {"name": self.le_name.text(), "entries": entries}

    def _validate_and_accept(self):
        if not self.le_name.text().strip():
            QMessageBox.warning(self, "Validation", "Combination Name is required.")
            return
        if self.tbl.rowCount() == 0:
            QMessageBox.warning(self, "Validation", "Add at least one load case entry.")
            return
        self.accept()


# ─────────────────────────────────────────────────────────────────────────────
#  Main Loading Tab
# ─────────────────────────────────────────────────────────────────────────────

class LoadingTab(QWidget):
    """
    Complete Loading input tab for OsdagBridge.

    Drop this widget directly into the Additional Inputs QTabWidget:
        additional_inputs_tabwidget.addTab(LoadingTab(parent), "Loading")
    """

    # emitted whenever any input changes (so the parent can mark design dirty)
    inputChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # internal state
        self._custom_vehicles   = []   # list of dicts
        self._custom_loads      = []   # list of dicts
        self._load_combinations = []   # list of dicts

        self._build_ui()

    # =========================================================================
    #  Top-level layout: inner tab widget inside a scroll area
    # =========================================================================

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        container = QWidget()
        container_lay = QVBoxLayout(container)
        container_lay.setSpacing(10)

        self.inner_tabs = QTabWidget()
        self.inner_tabs.setTabPosition(QTabWidget.North)

        # ── sub-tabs ────────────────────────────────────────────────────────
        self.inner_tabs.addTab(self._build_permanent_tab(),    "Permanent")
        self.inner_tabs.addTab(self._build_live_load_tab(),    "Live Load")
        self.inner_tabs.addTab(self._build_seismic_tab(),      "Seismic")
        self.inner_tabs.addTab(self._build_wind_tab(),         "Wind")
        self.inner_tabs.addTab(self._build_temperature_tab(),  "Temperature")
        self.inner_tabs.addTab(self._build_custom_load_tab(),  "Custom Load")
        self.inner_tabs.addTab(self._build_load_combo_tab(),   "Load Combination")

        container_lay.addWidget(self.inner_tabs)
        container_lay.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

    # =========================================================================
    #  1. Permanent Load
    # =========================================================================

    def _build_permanent_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(8)
        dbl = QtGui.QDoubleValidator(0, 1e6, 3)

        # ── Dead Load (DL) ───────────────────────────────────────────────────
        gb_dl = _make_group("Dead Load (DL)")
        g = QGridLayout(gb_dl)

        g.addWidget(QLabel("Include Member Self-Weight:"), 0, 0)
        self.cb_self_weight = _make_combo(["Yes", "No"])
        g.addWidget(self.cb_self_weight, 0, 1)

        g.addWidget(QLabel("Self-weight Factor:"), 1, 0)
        self.le_sw_factor = _make_line("1.0", validator=dbl)
        g.addWidget(self.le_sw_factor, 1, 1)
        g.addWidget(_make_label("Default: 1", style=NOTE_STYLE), 1, 2)

        g.addWidget(QLabel("Include Concrete Deck Weight:"), 2, 0)
        self.cb_deck_weight = _make_combo(["Yes", "No"])
        g.addWidget(self.cb_deck_weight, 2, 1)

        lay.addWidget(gb_dl)

        # ── Dead Load for Surfacing (DW) ─────────────────────────────────────
        gb_dw = _make_group("Dead Load for Surfacing (DW)")
        g2 = QGridLayout(gb_dw)
        g2.addWidget(QLabel("Include Load from Wearing Course:"), 0, 0)
        self.cb_wearing_course = _make_combo(["Yes", "No"])
        g2.addWidget(self.cb_wearing_course, 0, 1)
        lay.addWidget(gb_dw)

        # ── Super-Imposed Dead Load (SIDL) ───────────────────────────────────
        gb_sidl = _make_group("Super-Imposed Dead Load (SIDL)")
        g3 = QGridLayout(gb_sidl)

        g3.addWidget(QLabel("Include Load from Crash Barrier:"), 0, 0)
        self.cb_crash_barrier_load = _make_combo(["Yes", "No"])
        g3.addWidget(self.cb_crash_barrier_load, 0, 1)

        g3.addWidget(QLabel("Include Load from Median:"), 1, 0)
        self.cb_median_load = _make_combo(["Yes", "No"])
        g3.addWidget(self.cb_median_load, 1, 1)
        self._lbl_median_note = _make_label(
            "Grayed out if no median in Basic Inputs", style=NOTE_STYLE)
        g3.addWidget(self._lbl_median_note, 1, 2)

        g3.addWidget(QLabel("Include Load from Railing:"), 2, 0)
        self.cb_railing_load = _make_combo(["Yes", "No"])
        g3.addWidget(self.cb_railing_load, 2, 1)
        self._lbl_railing_note = _make_label(
            "Grayed out if footpath = none", style=NOTE_STYLE)
        g3.addWidget(self._lbl_railing_note, 2, 2)

        lay.addWidget(gb_sidl)
        lay.addStretch()
        return w

    # =========================================================================
    #  2. Live Load
    # =========================================================================

    def _build_live_load_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(8)
        dbl = QtGui.QDoubleValidator(0, 1e6, 3)

        # ── IRC 6 Vehicles ───────────────────────────────────────────────────
        gb_irc = _make_group("Vehicles from IRC 6  (select all that apply)")
        irc_lay = QVBoxLayout(gb_irc)
        self.chk_vehicles = {}
        for v in IRC6_VEHICLES:
            chk = QCheckBox(v)
            chk.setChecked(True)
            irc_lay.addWidget(chk)
            self.chk_vehicles[v] = chk
        lay.addWidget(gb_irc)

        # ── Custom Vehicle ───────────────────────────────────────────────────
        gb_cv = _make_group("Custom Vehicle")
        cv_lay = QVBoxLayout(gb_cv)

        cv_btn_row = QHBoxLayout()
        self.btn_cv_add  = QPushButton("Add")
        self.btn_cv_edit = QPushButton("Edit")
        self.btn_cv_del  = QPushButton("Delete")
        for b in (self.btn_cv_add, self.btn_cv_edit, self.btn_cv_del):
            cv_btn_row.addWidget(b)
        cv_btn_row.addStretch()
        cv_lay.addLayout(cv_btn_row)

        self.tbl_cv = QTableWidget(0, 4)
        self.tbl_cv.setHorizontalHeaderLabels(
            ["☑", "Name", "Axles", "Nose-Tail (m)"])
        self.tbl_cv.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_cv.setColumnWidth(0, 28)
        self.tbl_cv.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_cv.setFixedHeight(110)
        cv_lay.addWidget(self.tbl_cv)

        self.btn_cv_add.clicked.connect(self._add_custom_vehicle)
        self.btn_cv_edit.clicked.connect(self._edit_custom_vehicle)
        self.btn_cv_del.clicked.connect(self._del_custom_vehicle)
        lay.addWidget(gb_cv)

        # ── Braking Load ─────────────────────────────────────────────────────
        gb_bk = _make_group("Braking Load from Vehicles")
        bk_lay = QVBoxLayout(gb_bk)
        bk_lay.addWidget(_make_label(
            "Check vehicles to include braking load:", style=NOTE_STYLE))

        self.chk_braking = {}
        for v in IRC6_VEHICLES:
            chk = QCheckBox(v)
            chk.setChecked(True)
            bk_lay.addWidget(chk)
            self.chk_braking[v] = chk

        bk_ecc_row = QHBoxLayout()
        bk_ecc_row.addWidget(QLabel("Eccentricity from Top of Deck (m):"))
        self.le_bk_ecc = _make_line("1.2", validator=dbl)
        bk_ecc_row.addWidget(self.le_bk_ecc)
        bk_ecc_row.addWidget(_make_label("Default: 1.2 m (IRC 6)", style=NOTE_STYLE))
        bk_ecc_row.addStretch()
        bk_lay.addLayout(bk_ecc_row)
        lay.addWidget(gb_bk)

        # ── Footpath Pressure ─────────────────────────────────────────────────
        gb_fp = _make_group("Footpath Pressure")
        fp_lay = QGridLayout(gb_fp)
        fp_lay.addWidget(QLabel("Footpath Pressure (kN/m²):"), 0, 0)
        self.cb_fp_auto = _make_combo(["Automatic (IRC 6 = 500)", "User Defined"])
        self.cb_fp_auto.currentTextChanged.connect(self._on_fp_change)
        fp_lay.addWidget(self.cb_fp_auto, 0, 1)
        self.le_fp_pressure = _make_line("500", validator=dbl)
        self.le_fp_pressure.setEnabled(False)
        fp_lay.addWidget(self.le_fp_pressure, 0, 2)
        fp_lay.addWidget(_make_label(
            "Applicable only if footpath is present", style=NOTE_STYLE), 1, 0, 1, 3)
        lay.addWidget(gb_fp)

        lay.addStretch()
        return w

    def _on_fp_change(self, text):
        self.le_fp_pressure.setEnabled(text == "User Defined")

    # custom vehicle CRUD
    def _add_custom_vehicle(self):
        dlg = CustomVehicleDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            self._custom_vehicles.append(data)
            self._refresh_cv_table()
            self.inputChanged.emit()

    def _edit_custom_vehicle(self):
        row = self.tbl_cv.currentRow()
        if row < 0 or row >= len(self._custom_vehicles):
            QMessageBox.warning(self, "Warning",
                "No vehicles have been added." if not self._custom_vehicles
                else "Select a vehicle to edit.")
            return
        dlg = CustomVehicleDialog(self, data=self._custom_vehicles[row])
        if dlg.exec_() == QDialog.Accepted:
            self._custom_vehicles[row] = dlg.get_data()
            self._refresh_cv_table()
            self.inputChanged.emit()

    def _del_custom_vehicle(self):
        row = self.tbl_cv.currentRow()
        if row < 0 or row >= len(self._custom_vehicles):
            QMessageBox.warning(self, "Warning",
                "No vehicles have been added." if not self._custom_vehicles
                else "Select a vehicle to delete.")
            return
        self._custom_vehicles.pop(row)
        self._refresh_cv_table()
        self.inputChanged.emit()

    def _refresh_cv_table(self):
        self.tbl_cv.setRowCount(0)
        for d in self._custom_vehicles:
            r = self.tbl_cv.rowCount()
            self.tbl_cv.insertRow(r)
            chk_item = QTableWidgetItem()
            chk_item.setCheckState(Qt.Checked)
            chk_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            self.tbl_cv.setItem(r, 0, chk_item)
            self.tbl_cv.setItem(r, 1, QTableWidgetItem(d.get("name", "")))
            self.tbl_cv.setItem(r, 2, QTableWidgetItem(
                str(len(d.get("axles", [])))))
            self.tbl_cv.setItem(r, 3, QTableWidgetItem(d.get("nose_tail", "")))

    # =========================================================================
    #  3. Seismic Load
    # =========================================================================

    def _build_seismic_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(8)
        dbl = QtGui.QDoubleValidator(0, 1e6, 3)

        # ── Inputs ───────────────────────────────────────────────────────────
        gb_in = _make_group("Seismic / Earthquake Load (EL) – Inputs per IRC 6")
        g = QGridLayout(gb_in)

        g.addWidget(QLabel("Seismic Zone:"), 0, 0)
        self.cb_seismic_zone = _make_combo(["II", "III", "IV", "V"])
        g.addWidget(self.cb_seismic_zone, 0, 1)
        g.addWidget(_make_label("Default per Project Location", style=NOTE_STYLE), 0, 2)

        g.addWidget(QLabel("Importance Factor (I):"), 1, 0)
        self.le_importance = _make_line("1.0", validator=dbl)
        g.addWidget(self.le_importance, 1, 1)
        g.addWidget(_make_label("Default: 1.0 (normal bridge)", style=NOTE_STYLE), 1, 2)

        g.addWidget(QLabel("Type of Soil:"), 2, 0)
        self.cb_soil = _make_combo([
            "Type I – Rocky / Hard Soil (N > 30)",
            "Type II – Medium Soil (10 < N ≤ 30)",
            "Type III – Soft Soil (N < 10)",
        ])
        g.addWidget(self.cb_soil, 2, 1, 1, 2)

        g.addWidget(QLabel("Time Period (s):"), 3, 0)
        self.le_time_period = _make_line("(leave blank if unknown)", validator=dbl)
        g.addWidget(self.le_time_period, 3, 1)
        g.addWidget(_make_label("Default: Sa/g = 2.5 if blank (Cl. 218.5.1)", style=NOTE_STYLE), 3, 2)

        g.addWidget(QLabel("Damping (%):"), 4, 0)
        self.le_damping = _make_line("2", validator=dbl)
        g.addWidget(self.le_damping, 4, 1)
        g.addWidget(_make_label("Default: 2%", style=NOTE_STYLE), 4, 2)

        g.addWidget(QLabel("Response Reduction Factor (R):"), 5, 0)
        self.cb_R = _make_combo(["1 – No ductile detailing", "2 – Ductile detailing"])
        g.addWidget(self.cb_R, 5, 1)
        g.addWidget(_make_label("Default: 1", style=NOTE_STYLE), 5, 2)

        g.addWidget(QLabel("Dead Load for Seismic (kN):"), 6, 0)
        self.cb_eq_dl = _make_combo(["Automatic", "Custom"])
        self.cb_eq_dl.currentTextChanged.connect(
            lambda t: self.le_eq_dl.setEnabled(t == "Custom"))
        self.le_eq_dl = _make_line("", validator=dbl)
        self.le_eq_dl.setEnabled(False)
        g.addWidget(self.cb_eq_dl, 6, 1)
        g.addWidget(self.le_eq_dl, 6, 2)

        g.addWidget(QLabel("Live Load for Seismic (kN):"), 7, 0)
        self.cb_eq_ll = _make_combo(["Automatic", "Custom"])
        self.cb_eq_ll.currentTextChanged.connect(
            lambda t: self.le_eq_ll.setEnabled(t == "Custom"))
        self.le_eq_ll = _make_line("", validator=dbl)
        self.le_eq_ll.setEnabled(False)
        g.addWidget(self.cb_eq_ll, 7, 1)
        g.addWidget(self.le_eq_ll, 7, 2)

        lay.addWidget(gb_in)

        # ── IRC 6 Outputs ────────────────────────────────────────────────────
        gb_out = _make_group("IRC 6 Derived Outputs")
        go = QGridLayout(gb_out)

        self._seismic_outputs = {}
        output_labels = [
            ("Zone Factor (Z)",                        "zone_factor"),
            ("Spectral Acceleration Coeff. (Sa/g)",    "sa_g"),
            ("Horizontal Seismic Coeff. (Ah)",         "Ah"),
            ("Vertical Seismic Coeff. (Av)",           "Av"),
        ]
        for i, (lbl, key) in enumerate(output_labels):
            go.addWidget(QLabel(lbl + ":"), i, 0)
            le = QLineEdit()
            le.setReadOnly(True)
            le.setPlaceholderText("Calculated after Design")
            le.setStyleSheet("background:#f5f5f5;")
            go.addWidget(le, i, 1)
            self._seismic_outputs[key] = le

        lay.addWidget(gb_out)
        lay.addStretch()
        return w

    # =========================================================================
    #  4. Wind Load
    # =========================================================================

    def _build_wind_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(8)
        dbl = QtGui.QDoubleValidator(-1e6, 1e6, 3)

        gb_in = _make_group("Wind Load (WL) – Inputs per IRC 6")
        g = QGridLayout(gb_in)

        rows = [
            ("Basic Wind Speed (m/s):",           "le_wind_speed",      "33",   True,  "Default per Project Location (IRC 6 Fig. 10)"),
            ("Average Exposed Height (m):",        "le_wind_height",     "10",   True,  "Default: 10 m"),
        ]
        for i, (lbl, attr, default, editable, note) in enumerate(rows):
            g.addWidget(QLabel(lbl), i, 0)
            le = _make_line(default, validator=dbl)
            le.setText(default)
            le.setEnabled(editable)
            setattr(self, attr, le)
            g.addWidget(le, i, 1)
            g.addWidget(_make_label(note, style=NOTE_STYLE), i, 2)

        r = 2
        g.addWidget(QLabel("Type of Terrain:"), r, 0)
        self.cb_terrain = _make_combo(["Plain Terrain", "Terrain with Obstructions"])
        g.addWidget(self.cb_terrain, r, 1)

        r += 1
        g.addWidget(QLabel("Site Topography:"), r, 0)
        self.cb_topography = _make_combo([
            "Flat", "Hill, Ridge, Escarpment or Cliff"])
        g.addWidget(self.cb_topography, r, 1)

        auto_custom_fields = [
            ("Gust Factor (G):",                  "cb_gust",      "le_gust",      "2"),
            ("Drag Coeff. CD:",                   "cb_CD",        "le_CD",        "Auto"),
            ("Drag Coeff. Live Load CDLL:",        "cb_CDLL",      "le_CDLL",     "1.2"),
            ("Lift Coeff. CL:",                   "cb_CL",        "le_CL",       "0.75"),
            ("Superstructure Area – Elevation (m²):", "cb_ss_elev","le_ss_elev",  ""),
            ("Superstructure Area – Plan (m²):",   "cb_ss_plan",  "le_ss_plan",   ""),
            ("Exposed Frontal Area Live Load (m²):","cb_frontal", "le_frontal",   ""),
            ("Wind Load Eccentricity – Top of Deck (m):", "cb_wl_ecc","le_wl_ecc",""),
            ("Wind on LL Eccentricity – Top of Deck (m):","cb_wll_ecc","le_wll_ecc",""),
        ]
        for i, (lbl, cb_attr, le_attr, default) in enumerate(auto_custom_fields, start=r + 1):
            g.addWidget(QLabel(lbl), i, 0)
            cb = _make_combo(["Automatic", "Custom"])
            le = _make_line(default, validator=dbl)
            le.setEnabled(False)
            cb.currentTextChanged.connect(
                lambda t, _le=le: _le.setEnabled(t == "Custom"))
            setattr(self, cb_attr, cb)
            setattr(self, le_attr, le)
            g.addWidget(cb, i, 1)
            g.addWidget(le, i, 2)

        lay.addWidget(gb_in)

        # ── Outputs ──────────────────────────────────────────────────────────
        gb_out = _make_group("IRC 6 Derived Outputs")
        go = QGridLayout(gb_out)
        self._wind_outputs = {}
        wind_out_labels = [
            ("Hourly Mean Wind Speed (m/s)",       "vz"),
            ("Hourly Wind Pressure (N/m²)",        "pz"),
            ("Transverse Wind Force (N)",           "Ft"),
            ("Longitudinal Wind Force (N)",         "Fl"),
            ("Vertical Wind Force (N)",             "Fv"),
            ("Transverse Wind Force on LL (N)",     "Ft_ll"),
            ("Longitudinal Wind Force on LL (N)",   "Fl_ll"),
        ]
        for i, (lbl, key) in enumerate(wind_out_labels):
            go.addWidget(QLabel(lbl + ":"), i, 0)
            le = QLineEdit()
            le.setReadOnly(True)
            le.setPlaceholderText("Calculated after Design")
            le.setStyleSheet("background:#f5f5f5;")
            go.addWidget(le, i, 1)
            self._wind_outputs[key] = le

        lay.addWidget(gb_out)
        lay.addStretch()
        return w

    # =========================================================================
    #  5. Temperature Load
    # =========================================================================

    def _build_temperature_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(8)
        dbl = QtGui.QDoubleValidator(-100, 100, 3)
        dbl_pos = QtGui.QDoubleValidator(0, 1e6, 6)

        gb_in = _make_group("Temperature Load (TL) – Inputs per IRC 6")
        g = QGridLayout(gb_in)

        g.addWidget(QLabel("Highest Maximum Air Temperature (°C):"), 0, 0)
        self.le_temp_max = _make_line("", validator=dbl)
        g.addWidget(self.le_temp_max, 0, 1)
        g.addWidget(_make_label("Default per Project Location", style=NOTE_STYLE), 0, 2)

        g.addWidget(QLabel("Lowest Minimum Air Temperature (°C):"), 1, 0)
        self.le_temp_min = _make_line("", validator=dbl)
        g.addWidget(self.le_temp_min, 1, 1)
        g.addWidget(_make_label("Default per Project Location", style=NOTE_STYLE), 1, 2)

        g.addWidget(QLabel("Coeff. of Thermal Expansion – Steel (1/°C):"), 2, 0)
        self.le_alpha_steel = _make_line("0.000012", validator=dbl_pos)
        g.addWidget(self.le_alpha_steel, 2, 1)
        g.addWidget(_make_label("Default: 12.0 × 10⁻⁶ (IRC 6)", style=NOTE_STYLE), 2, 2)

        g.addWidget(QLabel("Coeff. of Thermal Expansion – RCC (1/°C):"), 3, 0)
        self.le_alpha_rcc = _make_line("0.000012", validator=dbl_pos)
        g.addWidget(self.le_alpha_rcc, 3, 1)
        g.addWidget(_make_label("Default: 12.0 × 10⁻⁶ (IRC 6)", style=NOTE_STYLE), 3, 2)

        lay.addWidget(gb_in)

        gb_out = _make_group("IRC 6 Derived Outputs")
        go = QGridLayout(gb_out)
        self._temp_outputs = {}
        for i, (lbl, key) in enumerate([
            ("Effective Bridge Temp – Min (°C)",  "t_min"),
            ("Effective Bridge Temp – Max (°C)",  "t_max"),
            ("Temperature Rise for Design (°C)",  "t_rise"),
            ("Temperature Fall for Design (°C)",  "t_fall"),
        ]):
            go.addWidget(QLabel(lbl + ":"), i, 0)
            le = QLineEdit()
            le.setReadOnly(True)
            le.setPlaceholderText("Calculated after Design")
            le.setStyleSheet("background:#f5f5f5;")
            go.addWidget(le, i, 1)
            self._temp_outputs[key] = le

        lay.addWidget(gb_out)
        lay.addStretch()
        return w

    # =========================================================================
    #  6. Custom Load
    # =========================================================================

    def _build_custom_load_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(8)

        # ── Add / Edit input area ─────────────────────────────────────────────
        gb_add = _make_group("Custom Load Input – Add / Edit")
        gb_add_lay = QVBoxLayout(gb_add)
        gb_add_lay.addWidget(_make_label(
            "Fill fields and click Save. Select a row below to Edit or Delete.",
            style=NOTE_STYLE))

        btn_row = QHBoxLayout()
        self.btn_cl_add  = QPushButton("Add Custom Load")
        self.btn_cl_edit = QPushButton("Edit Selected")
        self.btn_cl_del  = QPushButton("Delete Selected")
        for b in (self.btn_cl_add, self.btn_cl_edit, self.btn_cl_del):
            btn_row.addWidget(b)
        btn_row.addStretch()
        gb_add_lay.addLayout(btn_row)
        lay.addWidget(gb_add)

        # ── List ──────────────────────────────────────────────────────────────
        gb_list = _make_group("Custom Load List  (check to include in analysis)")
        list_lay = QVBoxLayout(gb_list)

        self.tbl_cl = QTableWidget(0, 6)
        self.tbl_cl.setHorizontalHeaderLabels(
            ["☑", "Load Case", "Type", "Dist Start (m)", "Dist End (m)", "Bearing Start (m)"])
        self.tbl_cl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_cl.setColumnWidth(0, 30)
        self.tbl_cl.setSelectionBehavior(QAbstractItemView.SelectRows)
        list_lay.addWidget(self.tbl_cl)
        lay.addWidget(gb_list)

        self.btn_cl_add.clicked.connect(self._add_custom_load)
        self.btn_cl_edit.clicked.connect(self._edit_custom_load)
        self.btn_cl_del.clicked.connect(self._del_custom_load)

        lay.addStretch()
        return w

    # custom load CRUD
    def _add_custom_load(self):
        dlg = CustomLoadDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            self._custom_loads.append(dlg.get_data())
            self._refresh_cl_table()
            self.inputChanged.emit()

    def _edit_custom_load(self):
        row = self.tbl_cl.currentRow()
        if row < 0 or row >= len(self._custom_loads):
            QMessageBox.warning(self, "Warning", "Select a load entry to edit.")
            return
        dlg = CustomLoadDialog(self, data=self._custom_loads[row])
        if dlg.exec_() == QDialog.Accepted:
            self._custom_loads[row] = dlg.get_data()
            self._refresh_cl_table()
            self.inputChanged.emit()

    def _del_custom_load(self):
        row = self.tbl_cl.currentRow()
        if row < 0 or row >= len(self._custom_loads):
            QMessageBox.warning(self, "Warning", "Select a load entry to delete.")
            return
        self._custom_loads.pop(row)
        self._refresh_cl_table()
        self.inputChanged.emit()

    def _refresh_cl_table(self):
        self.tbl_cl.setRowCount(0)
        for d in self._custom_loads:
            r = self.tbl_cl.rowCount()
            self.tbl_cl.insertRow(r)
            chk = QTableWidgetItem()
            chk.setCheckState(Qt.Checked)
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            self.tbl_cl.setItem(r, 0, chk)
            self.tbl_cl.setItem(r, 1, QTableWidgetItem(d.get("case", "")))
            self.tbl_cl.setItem(r, 2, QTableWidgetItem(d.get("type", "")))
            self.tbl_cl.setItem(r, 3, QTableWidgetItem(d.get("dist_start", "")))
            self.tbl_cl.setItem(r, 4, QTableWidgetItem(d.get("dist_end", "")))
            self.tbl_cl.setItem(r, 5, QTableWidgetItem(d.get("bear_start", "")))

    # =========================================================================
    #  7. Load Combination
    # =========================================================================

    def _build_load_combo_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(8)

        # auto IRC 6 toggle
        self.chk_auto_irc = QCheckBox(
            "Auto-include all IRC 6 Load Combinations (default: ON)")
        self.chk_auto_irc.setChecked(True)
        self.chk_auto_irc.stateChanged.connect(self._on_auto_irc_toggle)
        lay.addWidget(self.chk_auto_irc)

        gb = _make_group("Load Combination List")
        gb_lay = QVBoxLayout(gb)

        btn_row = QHBoxLayout()
        self.btn_lc_add  = QPushButton("Add")
        self.btn_lc_edit = QPushButton("Edit Selected")
        self.btn_lc_del  = QPushButton("Delete Selected")
        for b in (self.btn_lc_add, self.btn_lc_edit, self.btn_lc_del):
            btn_row.addWidget(b)
        btn_row.addStretch()
        gb_lay.addLayout(btn_row)

        self.tbl_lc = QTableWidget(0, 3)
        self.tbl_lc.setHorizontalHeaderLabels(
            ["Combination Name", "Load Cases", "Source"])
        self.tbl_lc.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_lc.setSelectionBehavior(QAbstractItemView.SelectRows)
        gb_lay.addWidget(self.tbl_lc)
        lay.addWidget(gb)

        self.btn_lc_add.clicked.connect(self._add_load_combo)
        self.btn_lc_edit.clicked.connect(self._edit_load_combo)
        self.btn_lc_del.clicked.connect(self._del_load_combo)

        # populate default IRC 6 combos
        self._populate_irc6_combos()

        lay.addStretch()
        return w

    # ── IRC 6 default combinations ────────────────────────────────────────────
    IRC6_DEFAULT_COMBOS = [
        ("ULS Basic",      [("DL", "1.35"), ("LL", "1.5"), ("WL", "1.5")]),
        ("ULS Seismic",    [("DL", "1.35"), ("EL", "1.5")]),
        ("ULS Temperature",[("DL", "1.35"), ("TL", "1.5")]),
        ("SLS Rare",       [("DL", "1.0"),  ("LL", "1.0"), ("WL", "1.0")]),
        ("SLS Frequent",   [("DL", "1.0"),  ("LL", "0.75")]),
        ("SLS Quasi-perm", [("DL", "1.0"),  ("LL", "0.5")]),
    ]

    def _populate_irc6_combos(self):
        for name, entries in self.IRC6_DEFAULT_COMBOS:
            cases = ", ".join(f"{c}×{f}" for c, f in entries)
            r = self.tbl_lc.rowCount()
            self.tbl_lc.insertRow(r)
            self.tbl_lc.setItem(r, 0, QTableWidgetItem(name))
            self.tbl_lc.setItem(r, 1, QTableWidgetItem(cases))
            src = QTableWidgetItem("IRC 6 Auto")
            src.setForeground(QtGui.QBrush(QtGui.QColor("#555")))
            self.tbl_lc.setItem(r, 2, src)
            self._load_combinations.append({
                "name": name,
                "entries": entries,
                "source": "irc6",
            })

    def _on_auto_irc_toggle(self, state):
        # remove / restore IRC 6 auto rows
        rows_to_remove = [
            r for r in range(self.tbl_lc.rowCount())
            if self.tbl_lc.item(r, 2) and
               self.tbl_lc.item(r, 2).text() == "IRC 6 Auto"
        ]
        for r in reversed(rows_to_remove):
            self.tbl_lc.removeRow(r)
        self._load_combinations = [
            c for c in self._load_combinations if c.get("source") != "irc6"
        ]
        if state == Qt.Checked:
            self._populate_irc6_combos()
        self.inputChanged.emit()

    def _add_load_combo(self):
        dlg = LoadCombinationDialog(self, available_cases=LOAD_CASES)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            data["source"] = "custom"
            self._load_combinations.append(data)
            self._refresh_lc_table_custom()
            self.inputChanged.emit()

    def _edit_load_combo(self):
        row = self.tbl_lc.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warning", "Select a combination to edit.")
            return
        # find matching custom entry
        name = self.tbl_lc.item(row, 0).text() if self.tbl_lc.item(row, 0) else ""
        match = next((i for i, c in enumerate(self._load_combinations)
                      if c["name"] == name and c.get("source") == "custom"), None)
        if match is None:
            QMessageBox.information(self, "Info",
                "IRC 6 auto combinations cannot be edited. Add a custom one instead.")
            return
        dlg = LoadCombinationDialog(self, data=self._load_combinations[match])
        if dlg.exec_() == QDialog.Accepted:
            self._load_combinations[match] = {**dlg.get_data(), "source": "custom"}
            self._refresh_lc_table_custom()
            self.inputChanged.emit()

    def _del_load_combo(self):
        row = self.tbl_lc.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warning", "Select a combination to delete.")
            return
        name = self.tbl_lc.item(row, 0).text() if self.tbl_lc.item(row, 0) else ""
        match = next((i for i, c in enumerate(self._load_combinations)
                      if c["name"] == name and c.get("source") == "custom"), None)
        if match is None:
            QMessageBox.information(self, "Info",
                "IRC 6 auto combinations cannot be deleted here. "
                "Uncheck the auto-include checkbox to remove them all.")
            return
        self._load_combinations.pop(match)
        self.tbl_lc.removeRow(row)
        self.inputChanged.emit()

    def _refresh_lc_table_custom(self):
        # rebuild only custom rows (leave IRC6 auto rows intact)
        # remove existing custom rows
        for r in reversed(range(self.tbl_lc.rowCount())):
            if self.tbl_lc.item(r, 2) and \
               self.tbl_lc.item(r, 2).text() == "Custom":
                self.tbl_lc.removeRow(r)
        for c in self._load_combinations:
            if c.get("source") != "custom":
                continue
            cases = ", ".join(f"{lc}×{f}" for lc, f in c.get("entries", []))
            r = self.tbl_lc.rowCount()
            self.tbl_lc.insertRow(r)
            self.tbl_lc.setItem(r, 0, QTableWidgetItem(c["name"]))
            self.tbl_lc.setItem(r, 1, QTableWidgetItem(cases))
            src = QTableWidgetItem("Custom")
            src.setForeground(QtGui.QBrush(QtGui.QColor("#005a9c")))
            self.tbl_lc.setItem(r, 2, src)

    # =========================================================================
    #  Public API – get / set all inputs as a dict (for save / load .osi)
    # =========================================================================

    def get_loading_data(self) -> dict:
        """Return all loading inputs as a serialisable dict."""
        return {
            # Permanent
            "self_weight":        self.cb_self_weight.currentText(),
            "sw_factor":          self.le_sw_factor.text(),
            "deck_weight":        self.cb_deck_weight.currentText(),
            "wearing_course":     self.cb_wearing_course.currentText(),
            "crash_barrier_load": self.cb_crash_barrier_load.currentText(),
            "median_load":        self.cb_median_load.currentText(),
            "railing_load":       self.cb_railing_load.currentText(),
            # Live
            "irc_vehicles":    {v: chk.isChecked()
                                for v, chk in self.chk_vehicles.items()},
            "custom_vehicles": self._custom_vehicles,
            "braking_vehicles": {v: chk.isChecked()
                                 for v, chk in self.chk_braking.items()},
            "braking_ecc":     self.le_bk_ecc.text(),
            "fp_pressure_mode":self.cb_fp_auto.currentText(),
            "fp_pressure":     self.le_fp_pressure.text(),
            # Seismic
            "seismic_zone":    self.cb_seismic_zone.currentText(),
            "importance":      self.le_importance.text(),
            "soil_type":       self.cb_soil.currentText(),
            "time_period":     self.le_time_period.text(),
            "damping":         self.le_damping.text(),
            "R_factor":        self.cb_R.currentText(),
            "eq_dl_mode":      self.cb_eq_dl.currentText(),
            "eq_dl":           self.le_eq_dl.text(),
            "eq_ll_mode":      self.cb_eq_ll.currentText(),
            "eq_ll":           self.le_eq_ll.text(),
            # Wind
            "wind_speed":      self.le_wind_speed.text(),
            "wind_height":     self.le_wind_height.text(),
            "terrain":         self.cb_terrain.currentText(),
            "topography":      self.cb_topography.currentText(),
            # Temperature
            "temp_max":        self.le_temp_max.text(),
            "temp_min":        self.le_temp_min.text(),
            "alpha_steel":     self.le_alpha_steel.text(),
            "alpha_rcc":       self.le_alpha_rcc.text(),
            # Custom loads
            "custom_loads":    self._custom_loads,
            # Combinations
            "auto_irc6_combos": self.chk_auto_irc.isChecked(),
            "load_combinations": self._load_combinations,
        }

    def set_loading_data(self, data: dict):
        """Restore all loading inputs from a dict (used by load .osi)."""
        def _set_combo(cb, key):
            val = data.get(key)
            if val:
                idx = cb.findText(val)
                if idx >= 0:
                    cb.setCurrentIndex(idx)

        _set_combo(self.cb_self_weight,       "self_weight")
        self.le_sw_factor.setText(data.get("sw_factor", "1.0"))
        _set_combo(self.cb_deck_weight,       "deck_weight")
        _set_combo(self.cb_wearing_course,    "wearing_course")
        _set_combo(self.cb_crash_barrier_load,"crash_barrier_load")
        _set_combo(self.cb_median_load,       "median_load")
        _set_combo(self.cb_railing_load,      "railing_load")

        for v, state in data.get("irc_vehicles", {}).items():
            if v in self.chk_vehicles:
                self.chk_vehicles[v].setChecked(state)

        self._custom_vehicles = data.get("custom_vehicles", [])
        self._refresh_cv_table()

        for v, state in data.get("braking_vehicles", {}).items():
            if v in self.chk_braking:
                self.chk_braking[v].setChecked(state)

        self.le_bk_ecc.setText(data.get("braking_ecc", "1.2"))
        _set_combo(self.cb_fp_auto,       "fp_pressure_mode")
        self.le_fp_pressure.setText(data.get("fp_pressure", "500"))

        _set_combo(self.cb_seismic_zone,  "seismic_zone")
        self.le_importance.setText(data.get("importance", "1.0"))
        _set_combo(self.cb_soil,          "soil_type")
        self.le_time_period.setText(data.get("time_period", ""))
        self.le_damping.setText(data.get("damping", "2"))
        _set_combo(self.cb_R,             "R_factor")
        _set_combo(self.cb_eq_dl,         "eq_dl_mode")
        self.le_eq_dl.setText(data.get("eq_dl", ""))
        _set_combo(self.cb_eq_ll,         "eq_ll_mode")
        self.le_eq_ll.setText(data.get("eq_ll", ""))

        self.le_wind_speed.setText(data.get("wind_speed", "33"))
        self.le_wind_height.setText(data.get("wind_height", "10"))
        _set_combo(self.cb_terrain,       "terrain")
        _set_combo(self.cb_topography,    "topography")

        self.le_temp_max.setText(data.get("temp_max", ""))
        self.le_temp_min.setText(data.get("temp_min", ""))
        self.le_alpha_steel.setText(data.get("alpha_steel", "0.000012"))
        self.le_alpha_rcc.setText(data.get("alpha_rcc", "0.000012"))

        self._custom_loads = data.get("custom_loads", [])
        self._refresh_cl_table()

        self.chk_auto_irc.setChecked(data.get("auto_irc6_combos", True))
        self._load_combinations = data.get("load_combinations", [])
        self._refresh_lc_table_custom()

    def set_output_values(self, seismic: dict = None,
                          wind: dict = None, temperature: dict = None):
        """
        Called by the backend after analysis to populate read-only output fields.
        Pass dicts keyed by the output field identifiers defined above.
        """
        if seismic:
            for key, le in self._seismic_outputs.items():
                if key in seismic:
                    le.setText(str(seismic[key]))
        if wind:
            for key, le in self._wind_outputs.items():
                if key in wind:
                    le.setText(str(wind[key]))
        if temperature:
            for key, le in self._temp_outputs.items():
                if key in temperature:
                    le.setText(str(temperature[key]))

    # =========================================================================
    #  Contextual enable/disable (call from parent when Basic Inputs change)
    # =========================================================================

    def set_median_enabled(self, enabled: bool):
        """Disable median load option when no median is selected in Basic Inputs."""
        self.cb_median_load.setEnabled(enabled)
        self._lbl_median_note.setVisible(not enabled)

    def set_railing_enabled(self, enabled: bool):
        """Disable railing load option when footpath = None."""
        self.cb_railing_load.setEnabled(enabled)
        self._lbl_railing_note.setVisible(not enabled)


# ─────────────────────────────────────────────────────────────────────────────
#  Quick standalone test
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = QWidget()
    win.setWindowTitle("OsdagBridge – Loading Tab (standalone test)")
    win.resize(900, 680)
    layout = QVBoxLayout(win)
    tab = LoadingTab()
    layout.addWidget(tab)
    win.show()
    sys.exit(app.exec_())
