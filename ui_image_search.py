# ui_image_search_singleinput_pro_results_learn_choice.py
# V2.6.0 – Negatieve feedback + penalty in ranking + Undo
# - Knop “Niet correct (negatief)” op geselecteerde match
# - Artikel-penalty via log(1+neg_count)
# - Negatieve keyword-signalen (dec_many)
# - Undo werkt voor zowel “leren” als “negatief klikken”
# - Query/match keywords bewerken, dubbelklik selecteert match, leren met confirm

import sys
import os
import json
import math
import threading
import base64
from io import BytesIO
from typing import List, Tuple, Dict, Optional

import numpy as np
from PIL import Image

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QMessageBox, QTableWidget, QHBoxLayout, QDialog, QSplitter, QInputDialog,
    QComboBox, QFrame, QTableWidgetItem, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QEvent, QThread, Signal, QSize
from PySide6.QtGui import QPixmap, QImage, QFont, QIcon

# -------------------------------
# Config
# -------------------------------
USE_API = False
LABELS_FILE = "labels.txt"
DB_FOLDER = "./Img_data"
MODEL_ID = "openai/clip-vit-base-patch16"

DEFAULT_LABELS = [
    "3-delige afsluiter", "afsluiter", "kogelafsluiter", "pomp", "flens", "doorvoer",
    "tank", "filter", "sensor", "drukmeter", "leiding", "vlinderklep", "manometer",
    "inox", "schroefdraad", "bolkraan", "M/F", "FF", "met hendel", "2-delig", "3-delig"
]

LABEL_CACHE_PATH = "label_cache.npz"
KEYWORD_STATS_PATH = "keywords_stats_v2.json"
KW_EMB_FILENAME = "kw_embedding.npy"
CENTROID_FILENAME = "centroid.npy"
CENTROID_COUNT = "centroid_count.txt"
NEGCOUNT_FILENAME = "neg_count.txt"

# Frequentie-boost (voor suggesties)
FREQ_ALPHA = 0.35
FREQ_FLOOR = 1.0

# Feedback-gewichten
POS_WEIGHT = 3             # extra voor positieve keywords per klik
NEG_WEIGHT = 1             # straf voor niet-geselecteerde topN bij positief leren
POS_ALPHA = 0.15           # bijdrage pos in embedding-gewicht
NEG_BETA = 0.10            # bijdrage neg in embedding-gewicht

# Rerank/centroid defaults
DEFAULT_RERANK_ALPHA = 0.35
DEFAULT_CENTROID_GAMMA = 0.30

# Negatieve klik (expliciet fout)
NEG_CLICK_WEIGHT = 3       # hoeveel neg voor keywords van de (foute) match
ARTICLE_NEG_ETA  = 0.12    # ranking-penalty per artikel: ETA * log(1+neg_cnt)

# -------------------------------
# Lazy CLIP loader
# -------------------------------
_clip = {"model": None, "processor": None}
_clip_lock = threading.Lock()

def get_clip(local_only=True):
    if _clip["model"] is not None:
        return _clip["model"], _clip["processor"]
    with _clip_lock:
        if _clip["model"] is not None:
            return _clip["model"], _clip["processor"]
        from transformers import CLIPProcessor, CLIPModel
        import torch
        try:
            model = CLIPModel.from_pretrained(MODEL_ID, local_files_only=local_only)
            processor = CLIPProcessor.from_pretrained(MODEL_ID, local_files_only=local_only)
        except Exception:
            model = CLIPModel.from_pretrained(MODEL_ID)
            processor = CLIPProcessor.from_pretrained(MODEL_ID)
        model = model.cpu()
        torch.set_grad_enabled(False)
        try:
            torch.set_num_threads(max(1, (os.cpu_count() or 2) // 2))
        except Exception:
            pass
        _clip["model"], _clip["processor"] = model, processor
        return model, processor

class ModelWarmupThread(QThread):
    loaded = Signal(bool)
    def run(self):
        try:
            get_clip(local_only=True)
            self.loaded.emit(True)
        except Exception:
            try:
                get_clip(local_only=False)
                self.loaded.emit(True)
            except Exception:
                self.loaded.emit(False)

# -------------------------------
# Utils
# -------------------------------
def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)

def cos_sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)

def pil2pixmap(img):
    if img.mode != "RGB":
        img = img.convert("RGB")
    arr = np.array(img)
    h, w, ch = arr.shape
    bytes_per_line = ch * w
    return QPixmap(QImage(arr.data, w, h, bytes_per_line, QImage.Format_RGB888))

def image_to_base64(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def base64_to_image(b64str: str) -> Image.Image:
    img_bytes = base64.b64decode(b64str)
    return Image.open(BytesIO(img_bytes)).convert("RGB")

# -------------------------------
# Repositories
# -------------------------------
class Repository:
    def list_all_keywords(self) -> List[str]: ...
    def iter_entries(self) -> List[str]: ...
    def get_entry_embedding(self, art_id: str) -> Optional[np.ndarray]: ...
    def get_entry_kw_embedding(self, art_id: str) -> Optional[np.ndarray]: ...
    def save_entry_kw_embedding(self, art_id: str, kw_emb: np.ndarray) -> None: ...
    def get_entry_image_b64(self, art_id: str) -> Optional[str]: ...
    def get_entry_keywords(self, art_id: str) -> List[str]: ...
    def save_new_entry(self, art_id: str, img_b64: str, embedding: np.ndarray, keywords: List[str], kw_emb: Optional[np.ndarray]) -> None: ...
    def update_entry_keywords(self, art_id: str, keywords: List[str]) -> None: ...
    # centroid
    def get_entry_centroid(self, art_id: str) -> Optional[np.ndarray]: ...
    def get_entry_centroid_count(self, art_id: str) -> int: ...
    def save_entry_centroid(self, art_id: str, centroid: np.ndarray, count: int) -> None: ...
    # negative counts
    def get_entry_neg_count(self, art_id: str) -> int: ...
    def inc_entry_neg_count(self, art_id: str, amount: int = 1) -> None: ...
    def set_entry_neg_count(self, art_id: str, value: int) -> None: ...

class LocalFSRepository(Repository):
    def __init__(self, root: str):
        self.root = root
        ensure_dir(root)
    def _dir(self, art_id: str) -> str:
        return os.path.join(self.root, art_id)
    def list_all_keywords(self) -> List[str]:
        kws = set()
        for entry in os.listdir(self.root):
            kwp = os.path.join(self._dir(entry), "keywords.txt")
            if os.path.exists(kwp):
                try:
                    with open(kwp, "r", encoding="utf-8") as f:
                        for k in f.read().split(","):
                            k = k.strip()
                            if k:
                                kws.add(k)
                except Exception:
                    pass
        return sorted(kws)
    def iter_entries(self) -> List[str]:
        return [e for e in os.listdir(self.root) if os.path.isdir(self._dir(e))]
    def get_entry_embedding(self, art_id: str) -> Optional[np.ndarray]:
        p = os.path.join(self._dir(art_id), "embedding.npy")
        if os.path.exists(p):
            try: return np.load(p)
            except Exception: return None
        return None
    def get_entry_kw_embedding(self, art_id: str) -> Optional[np.ndarray]:
        p = os.path.join(self._dir(art_id), KW_EMB_FILENAME)
        if os.path.exists(p):
            try: return np.load(p)
            except Exception: return None
        return None
    def save_entry_kw_embedding(self, art_id: str, kw_emb: np.ndarray) -> None:
        d = self._dir(art_id); ensure_dir(d)
        np.save(os.path.join(d, KW_EMB_FILENAME), kw_emb)
    def get_entry_image_b64(self, art_id: str) -> Optional[str]:
        p = os.path.join(self._dir(art_id), "image.b64")
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                return None
        return None
    def get_entry_keywords(self, art_id: str) -> List[str]:
        p = os.path.join(self._dir(art_id), "keywords.txt")
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return [k.strip() for k in f.read().split(",") if k.strip()]
            except Exception:
                return []
        return []
    def save_new_entry(self, art_id: str, img_b64: str, embedding: np.ndarray, keywords: List[str], kw_emb: Optional[np.ndarray]) -> None:
        d = self._dir(art_id); ensure_dir(d)
        with open(os.path.join(d, "image.b64"), "w", encoding="utf-8") as f:
            f.write(img_b64)
        np.save(os.path.join(d, "embedding.npy"), embedding)
        with open(os.path.join(d, "keywords.txt"), "w", encoding="utf-8") as f:
            f.write(", ".join(keywords))
        if kw_emb is not None:
            np.save(os.path.join(d, KW_EMB_FILENAME), kw_emb)
    def update_entry_keywords(self, art_id: str, keywords: List[str]) -> None:
        d = self._dir(art_id); ensure_dir(d)
        with open(os.path.join(d, "keywords.txt"), "w", encoding="utf-8") as f:
            f.write(", ".join(keywords))
    # centroid
    def get_entry_centroid(self, art_id: str) -> Optional[np.ndarray]:
        p = os.path.join(self._dir(art_id), CENTROID_FILENAME)
        if os.path.exists(p):
            try: return np.load(p)
            except Exception: return None
        return None
    def get_entry_centroid_count(self, art_id: str) -> int:
        p = os.path.join(self._dir(art_id), CENTROID_COUNT)
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f: return int(f.read().strip() or "0")
            except Exception: return 0
        return 0
    def save_entry_centroid(self, art_id: str, centroid: np.ndarray, count: int) -> None:
        d = self._dir(art_id); ensure_dir(d)
        np.save(os.path.join(d, CENTROID_FILENAME), centroid)
        with open(os.path.join(d, CENTROID_COUNT), "w", encoding="utf-8") as f:
            f.write(str(int(count)))
    # neg counts
    def get_entry_neg_count(self, art_id: str) -> int:
        p = os.path.join(self._dir(art_id), NEGCOUNT_FILENAME)
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return int(f.read().strip() or "0")
            except Exception:
                return 0
        return 0
    def inc_entry_neg_count(self, art_id: str, amount: int = 1) -> None:
        d = self._dir(art_id); ensure_dir(d)
        cur = self.get_entry_neg_count(art_id)
        with open(os.path.join(d, NEGCOUNT_FILENAME), "w", encoding="utf-8") as f:
            f.write(str(int(cur + amount)))
    def set_entry_neg_count(self, art_id: str, value: int) -> None:
        d = self._dir(art_id); ensure_dir(d)
        with open(os.path.join(d, NEGCOUNT_FILENAME), "w", encoding="utf-8") as f:
            f.write(str(int(value)))

class ApiRepository(Repository):
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url; self.api_key = api_key
    def list_all_keywords(self) -> List[str]: return []
    def iter_entries(self) -> List[str]: return []
    def get_entry_embedding(self, art_id: str) -> Optional[np.ndarray]: return None
    def get_entry_kw_embedding(self, art_id: str) -> Optional[np.ndarray]: return None
    def save_entry_kw_embedding(self, art_id: str, kw_emb: np.ndarray) -> None: pass
    def get_entry_image_b64(self, art_id: str) -> Optional[str]: return None
    def get_entry_keywords(self, art_id: str) -> List[str]: return []
    def save_new_entry(self, art_id: str, img_b64: str, embedding: np.ndarray, keywords: List[str], kw_emb: Optional[np.ndarray]) -> None: pass
    def update_entry_keywords(self, art_id: str, keywords: List[str]) -> None: pass
    def get_entry_centroid(self, art_id: str) -> Optional[np.ndarray]: return None
    def get_entry_centroid_count(self, art_id: str) -> int: return 0
    def save_entry_centroid(self, art_id: str, centroid: np.ndarray, count: int) -> None: pass
    def get_entry_neg_count(self, art_id: str) -> int: return 0
    def inc_entry_neg_count(self, art_id: str, amount: int = 1) -> None: pass
    def set_entry_neg_count(self, art_id: str, value: int) -> None: pass

# -------------------------------
# Label cache + stats (met pos/neg)
# -------------------------------
class LabelCache:
    def __init__(self, cache_path: str = LABEL_CACHE_PATH):
        self.cache_path = cache_path
        self._labels: List[str] = []
        self._embeddings: Optional[np.ndarray] = None
        self._dirty = False
        self._lock = threading.Lock()
        self.load()
    def load(self):
        if os.path.exists(self.cache_path):
            try:
                data = np.load(self.cache_path, allow_pickle=False)
                self._labels = list(data["labels"])
                self._embeddings = data["embeddings"]
            except Exception:
                self._labels = []; self._embeddings = None
    def save(self):
        if not self._dirty: return
        try:
            np.savez_compressed(self.cache_path,
                                labels=np.array(self._labels, dtype=object),
                                embeddings=self._embeddings)
            self._dirty = False
        except Exception:
            pass
    def get_vectors_for(self, labels: List[str]) -> Tuple[List[str], np.ndarray]:
        with self._lock:
            new_needed = [lb for lb in labels if lb not in self._labels]
            if new_needed:
                model, processor = get_clip()
                import torch
                prompts = []
                map_idx = []
                for lb in new_needed:
                    idxs = []
                    for t in [
                        f"industrieel onderdeel: {lb}",
                        f"productfoto van {lb}",
                        f"industrial equipment: {lb}",
                        f"a product photo of {lb}",
                    ]:
                        idxs.append(len(prompts)); prompts.append(t)
                    map_idx.append(idxs)
                with torch.no_grad():
                    text_inputs = processor(text=prompts, return_tensors="pt", padding=True)
                    feats = model.get_text_features(**text_inputs)
                    feats = feats / feats.norm(dim=-1, keepdim=True)
                    feats = feats.cpu().numpy()
                new_vecs = []
                for idxs in map_idx:
                    vec = np.mean([feats[i] for i in idxs], axis=0)
                    vec = vec / (np.linalg.norm(vec) or 1e-9)
                    new_vecs.append(vec)
                if self._embeddings is None or len(self._labels) == 0:
                    self._labels = list(new_needed)
                    self._embeddings = np.vstack(new_vecs)
                else:
                    self._labels.extend(new_needed)
                    self._embeddings = np.vstack([self._embeddings, np.vstack(new_vecs)])
                self._dirty = True; self.save()
            idxs = [self._labels.index(lb) for lb in labels]
            emb = self._embeddings[idxs, :]
            return labels, emb

class KeywordStats:
    """Bewaar pos/neg counts; JSON: {keyword: {"pos": int, "neg": int}}"""
    def __init__(self, path: str = KEYWORD_STATS_PATH):
        self.path = path
        self._stats: Dict[str, Dict[str, int]] = {}
        self._lock = threading.Lock()
        self.load()
    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._stats = json.load(f)
            except Exception:
                self._stats = {}
        else:
            self._stats = {}
    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._stats, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    def _ensure(self, k: str):
        if k not in self._stats:
            self._stats[k] = {"pos": 0, "neg": 0}
    def inc_many(self, keywords: List[str], amount: int = 1):
        with self._lock:
            for k in keywords:
                self._ensure(k)
                self._stats[k]["pos"] = int(self._stats[k]["pos"]) + amount
            self.save()
    def dec_many(self, keywords: List[str], amount: int = 1):
        with self._lock:
            for k in keywords:
                self._ensure(k)
                self._stats[k]["neg"] = int(self._stats[k]["neg"]) + amount
            self.save()
    def get_pos_neg(self, keyword: str) -> Tuple[int, int]:
        d = self._stats.get(keyword, {"pos": 0, "neg": 0})
        return int(d.get("pos", 0)), int(d.get("neg", 0))
    def weight(self, keyword: str) -> float:
        """Gewicht voor embedding-aggregatie: exp(POS_ALPHA*pos - NEG_BETA*neg)."""
        pos, neg = self.get_pos_neg(keyword)
        return math.exp(POS_ALPHA * pos - NEG_BETA * neg)

# -------------------------------
# Generator
# -------------------------------
class SmartLabelGenerator:
    def __init__(self, repo: Repository, label_cache: LabelCache, stats: KeywordStats):
        self.repo = repo; self.cache = label_cache; self.stats = stats
    def _candidate_labels(self) -> List[str]:
        if os.path.exists(LABELS_FILE):
            try:
                with open(LABELS_FILE, "r", encoding="utf-8") as f:
                    file_labels = [ln.strip() for ln in f if ln.strip()]
            except Exception:
                file_labels = []
        else:
            file_labels = []
        if not file_labels:
            file_labels = DEFAULT_LABELS
        repo_labels = self.repo.list_all_keywords()
        seen = set(); out = []
        for l in file_labels + repo_labels:
            if l not in seen:
                out.append(l); seen.add(l)
        return out
    def image_embedding(self, img: Image.Image) -> np.ndarray:
        model, processor = get_clip(); import torch
        inputs = processor(images=img, return_tensors="pt")
        with torch.no_grad():
            image_features = model.get_image_features(**inputs)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            vec = image_features.cpu().numpy().flatten()
        return vec
    def text_embedding_for_keywords(self, keywords: List[str]) -> Optional[np.ndarray]:
        """Gewogen gemiddelde van tekst-embeddings volgens KeywordStats.weight()."""
        if not keywords: return None
        labels, vecs = self.cache.get_vectors_for(keywords)
        weights = np.array([self.stats.weight(lb) for lb in labels], dtype=np.float64)
        weights = weights / (weights.sum() or 1.0)
        vec = (weights[:, None] * vecs).sum(axis=0)
        norm = np.linalg.norm(vec)
        return vec / (norm or 1e-9)
    def top_labels(self, img: Image.Image, top_n: int = 5) -> List[str]:
        labels = self._candidate_labels()
        if not labels: return []
        labels_ordered, lab_vecs = self.cache.get_vectors_for(labels)
        q = self.image_embedding(img)
        sims = lab_vecs.dot(q)
        scores = []
        for i, lb in enumerate(labels_ordered):
            base = float(sims[i])
            pos, neg = self.stats.get_pos_neg(lb)
            boost = 1.0 + FREQ_ALPHA * math.log(FREQ_FLOOR + pos + 1.0) - 0.10 * math.log(1.0 + neg)
            scores.append((base * boost, lb))
        scores.sort(key=lambda x: x[0], reverse=True)
        return [lb for _, lb in scores[:top_n]]

# -------------------------------
# Keywords Dialog (bewerken)
# -------------------------------
class KeywordsDialog(QDialog):
    def __init__(self, keywords, all_keywords, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kernwoorden bewerken")
        self.setMinimumWidth(520)
        self.keywords = keywords.copy()
        self.all_keywords = all_keywords if all_keywords else DEFAULT_LABELS

        layout = QVBoxLayout()
        self.table = QTableWidget(len(self.keywords), 1)
        self.table.setHorizontalHeaderLabels(["Kernwoord"])
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 280)
        header_font = self.table.horizontalHeader().font()
        header_font.setPointSize(12); header_font.setBold(True)
        self.table.horizontalHeader().setFont(header_font)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)

        for i, kw in enumerate(self.keywords):
            cb = QComboBox(); cb.setEditable(True)
            cb.addItems(self.all_keywords)
            cb.setMinimumWidth(270)
            cb.setStyleSheet("QComboBox{font-size:12pt;padding:4px 16px 4px 6px;} QComboBox QAbstractItemView{font-size:12pt;}")
            if kw: cb.setCurrentText(kw)
            self.table.setCellWidget(i, 0, cb)
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        add_btn = QPushButton("➕ Toevoegen"); add_btn.clicked.connect(self.add_row)
        del_btn = QPushButton("🗑 Verwijder"); del_btn.clicked.connect(self.delete_row)
        btns.addWidget(add_btn); btns.addWidget(del_btn); btns.addStretch(1)
        layout.addLayout(btns)

        ok_btn = QPushButton("OK"); ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)
        self.setLayout(layout)
        self.table.installEventFilter(self)
    def eventFilter(self, obj, event):
        if obj is self.table and event.type() == QEvent.MouseButtonPress:
            idx = self.table.indexAt(event.pos())
            if idx.isValid():
                w = self.table.cellWidget(idx.row(), idx.column())
                if isinstance(w, QComboBox):
                    w.setFocus(); w.showPopup()
        return super().eventFilter(obj, event)
    def add_row(self):
        r = self.table.rowCount(); self.table.insertRow(r)
        cb = QComboBox(); cb.setEditable(True)
        cb.addItems(self.all_keywords)
        cb.setMinimumWidth(270)
        cb.setStyleSheet("QComboBox{font-size:12pt;padding:4px 16px 4px 6px;} QComboBox QAbstractItemView{font-size:12pt;}")
        self.table.setCellWidget(r, 0, cb)
    def delete_row(self):
        r = self.table.currentRow()
        if r >= 0: self.table.removeRow(r)
    def get_keywords(self):
        out = []
        for r in range(self.table.rowCount()):
            w = self.table.cellWidget(r, 0)
            if isinstance(w, QComboBox):
                t = w.currentText().strip()
                if t: out.append(t)
        return out

# -------------------------------
# Main App (layout + learning)
# -------------------------------
class CombinedApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Labeling & Reverse Image Search")
        self.setMinimumWidth(1500)

        self.repo: Repository = ApiRepository("https://api.example", api_key=None) if USE_API else LocalFSRepository(DB_FOLDER)
        self.label_cache = LabelCache(LABEL_CACHE_PATH)
        self.stats = KeywordStats(KEYWORD_STATS_PATH)
        self.generator = SmartLabelGenerator(self.repo, self.label_cache, self.stats)

        self.current_img: Optional[Image.Image] = None
        self.current_keywords: List[str] = []
        self._model_ready = False
        self._pending_autogen = False
        self.best_match_id: Optional[str] = None
        self.best_match_keywords: List[str] = []
        self.last_similarity: Optional[float] = None
        self._last_ranked_items: List[Tuple[float, str]] = []  # voor negatieve feedback
        self._undo_feedback = None

        # ---------- Root layout ----------
        root = QVBoxLayout()
        root.setContentsMargins(8, 6, 8, 8)
        root.setSpacing(6)

        # Status
        self.status_label = QLabel("Model aan het laden…")
        self.status_label.setStyleSheet("color:#666;")
        root.addWidget(self.status_label)

        # Top bar (knoppen)
        topbar = QHBoxLayout(); topbar.setSpacing(6)
        self.load_btn = QPushButton("Afbeelding kiezen of URL invullen")
        self.load_btn.clicked.connect(self.load_img_dialog)
        self.save_button = QPushButton("Sla op als nieuw artikel")
        self.save_button.clicked.connect(self.save_new_entry)
        self.keywords_button = QPushButton("Genereer/Bewerk kernwoorden")     # query keywords
        self.keywords_button.clicked.connect(self.show_keywords_dialog)
        self.search_btn = QPushButton("Zoek gelijkaardige")
        self.search_btn.clicked.connect(self.run_search)
        for b in (self.load_btn, self.save_button, self.keywords_button, self.search_btn):
            b.setMinimumHeight(28)
        topbar.addWidget(self.load_btn); topbar.addWidget(self.save_button); topbar.addWidget(self.keywords_button); topbar.addWidget(self.search_btn); topbar.addStretch(1)
        root.addLayout(topbar)

        # Parameter bar
        parambar = QHBoxLayout(); parambar.setSpacing(10)
        small_lbl_css = "QLabel{font-size:11px;color:#444;}"
        small_combo_css = "QComboBox{font-size:11px;min-height:24px;padding:2px 12px 2px 6px;}"
        lbl_d = QLabel("Drempel:"); lbl_d.setStyleSheet(small_lbl_css)
        self.threshold_combo = QComboBox(); self.threshold_combo.addItems(["90%", "85%"]); self.threshold_combo.setCurrentIndex(0); self.threshold_combo.setStyleSheet(small_combo_css)
        lbl_m = QLabel("Zoekmodus:"); lbl_m.setStyleSheet(small_lbl_css)
        self.mode_combo = QComboBox(); self.mode_combo.addItems(["Beeld (alleen)", "Dual-fusie (img+kw)", "Re-rank (topK)"]); self.mode_combo.setCurrentIndex(1); self.mode_combo.setStyleSheet(small_combo_css)
        lbl_l = QLabel("λ kw:"); lbl_l.setStyleSheet(small_lbl_css)
        self.fusion_kw_weight = QComboBox(); self.fusion_kw_weight.addItems(["0.25", "0.50", "0.75"]); self.fusion_kw_weight.setCurrentIndex(1); self.fusion_kw_weight.setStyleSheet(small_combo_css)
        lbl_a = QLabel("α:"); lbl_a.setStyleSheet(small_lbl_css)
        self.rerank_alpha = QComboBox(); self.rerank_alpha.addItems(["0.25", "0.35", "0.50"]); self.rerank_alpha.setCurrentIndex(1); self.rerank_alpha.setStyleSheet(small_combo_css)
        lbl_k = QLabel("topK:"); lbl_k.setStyleSheet(small_lbl_css)
        self.rerank_topk = QComboBox(); self.rerank_topk.addItems(["20", "50", "100"]); self.rerank_topk.setCurrentIndex(1); self.rerank_topk.setStyleSheet(small_combo_css)
        lbl_g = QLabel("γ centroid:"); lbl_g.setStyleSheet(small_lbl_css)
        self.centroid_gamma = QComboBox(); self.centroid_gamma.addItems(["0.00", "0.20", "0.30", "0.40"]); self.centroid_gamma.setCurrentText(f"{DEFAULT_CENTROID_GAMMA:.2f}"); self.centroid_gamma.setStyleSheet(small_combo_css)
        for w in [lbl_d, self.threshold_combo, lbl_m, self.mode_combo, lbl_l, self.fusion_kw_weight, lbl_a, self.rerank_alpha, lbl_k, self.rerank_topk, lbl_g, self.centroid_gamma]:
            parambar.addWidget(w)
        parambar.addStretch(1)
        root.addLayout(parambar)

        self.img_path_label = QLabel("")
        self.img_path_label.setStyleSheet("color:#666;font-size:11px;")
        root.addWidget(self.img_path_label)

        # ======= Midden: 4 kolommen =======
        mid = QSplitter(); mid.setChildrenCollapsible(False)

        # (1) Kernwoorden voorstel (links) — query keywords
        kw_panel = QVBoxLayout()
        kw_title = QLabel("Kernwoorden (voorstel) — Query")
        kw_title.setStyleSheet("font-weight:bold;")
        self.kw_list = QListWidget()
        self.kw_list.setStyleSheet("QListWidget{font-size:11px;}")
        kw_wrap = QWidget(); kw_wrap.setLayout(kw_panel)
        kw_panel.addWidget(kw_title)
        kw_panel.addWidget(self.kw_list)
        mid.addWidget(kw_wrap)

        # (2) Query met kop
        left_box = QVBoxLayout()
        left_title = QLabel("Afbeelding (query)")
        left_title.setAlignment(Qt.AlignCenter)
        self.left_img_label = QLabel("")
        self.left_img_label.setFixedSize(260, 260); self.left_img_label.setAlignment(Qt.AlignCenter)
        left_col = QWidget(); left_col.setLayout(left_box)
        left_box.addWidget(left_title)
        left_box.addWidget(self.left_img_label, alignment=Qt.AlignCenter)
        mid.addWidget(left_col)

        # (3) Voorstel + percentage
        right_box = QVBoxLayout()
        right_title = QLabel("Voorstel (match)")
        right_title.setAlignment(Qt.AlignCenter)
        self.right_img_label = QLabel("")
        self.right_img_label.setFixedSize(260, 260); self.right_img_label.setAlignment(Qt.AlignCenter)

        self.sim_frame = QFrame()
        self.sim_frame.setFixedSize(360, 160)
        self.sim_frame.setStyleSheet("QFrame{background:#f8f8f8;border:2px solid #2e7d32;border-radius:7px;}")
        self.sim_label = QLabel(""); self.sim_label.setAlignment(Qt.AlignCenter)
        f = QFont(); f.setPointSize(32); f.setBold(True); self.sim_label.setFont(f)
        sim_v = QVBoxLayout(); sim_v.addStretch(); sim_v.addWidget(self.sim_label); sim_v.addStretch()
        self.sim_frame.setLayout(sim_v); self.sim_frame.setVisible(False)

        right_col = QWidget(); right_col.setLayout(right_box)
        right_box.addWidget(right_title)
        right_box.addWidget(self.right_img_label, alignment=Qt.AlignCenter)
        right_box.addWidget(self.sim_frame, alignment=Qt.AlignCenter)
        mid.addWidget(right_col)

        # (4) Info rechts
        info_box = QVBoxLayout()
        info_title = QLabel("Details — Geselecteerde match")
        info_title.setStyleSheet("font-weight:bold;")
        self.lbl_artikel = QLabel("Artikel: –")
        self.lbl_keywords = QLabel("Kernwoorden: –")
        self.lbl_keywords.setWordWrap(True)
        # actiekoppen
        self.learn_btn = QPushButton("Voeg toe als betere keuze")
        self.learn_btn.setToolTip("Leer van de geselecteerde match met je huidige (query) kernwoorden.")
        self.learn_btn.clicked.connect(self.learn_from_choice)
        self.learn_btn.setEnabled(False)

        self.not_correct_btn = QPushButton("Niet correct (negatief)")
        self.not_correct_btn.setToolTip("Geef negatieve feedback op deze voorgestelde match.")
        self.not_correct_btn.clicked.connect(self.mark_current_as_incorrect)
        self.not_correct_btn.setEnabled(False)

        self.undo_btn = QPushButton("Ongedaan maken")
        self.undo_btn.setToolTip("Maak de laatste leer-actie ongedaan.")
        self.undo_btn.setEnabled(False)
        self.undo_btn.clicked.connect(self.undo_last_learn)

        info_col = QWidget(); info_col.setLayout(info_box)
        info_box.addWidget(info_title)
        info_box.addWidget(self.lbl_artikel)
        info_box.addWidget(self.lbl_keywords)
        info_box.addWidget(self.learn_btn)
        info_box.addWidget(self.not_correct_btn)
        info_box.addWidget(self.undo_btn)
        info_box.addStretch(1)
        mid.addWidget(info_col)

        mid.setSizes([240, 300, 380, 260])
        root.addWidget(mid)

        # ======= Resultaten =======
        results_lbl = QLabel("Resultaten:")
        results_lbl.setStyleSheet("font-size:12px;color:#333;")
        root.addWidget(results_lbl)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Preview", "Artikel", "%", "Keywords"])
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setIconSize(QSize(72, 72))
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setShowGrid(False)
        self.results_table.cellDoubleClicked.connect(self.on_result_double_clicked)
        hdr_font = self.results_table.horizontalHeader().font()
        hdr_font.setPointSize(10); hdr_font.setBold(False)
        self.results_table.horizontalHeader().setFont(hdr_font)
        self.results_table.setStyleSheet("QTableWidget{font-size:11px;}")
        root.addWidget(self.results_table, stretch=1)

        # Acties onderaan
        actions = QHBoxLayout()
        self.edit_match_keywords_btn = QPushButton("Bewerk kernwoorden van geselecteerde match")
        self.edit_match_keywords_btn.clicked.connect(self.edit_match_keywords)
        self.edit_match_keywords_btn.setVisible(False)
        self.make_new_from_match_btn = QPushButton("Nieuwe artikel op basis van geselecteerde match")
        self.make_new_from_match_btn.clicked.connect(self.make_new_from_match)
        self.make_new_from_match_btn.setVisible(False)
        actions.addWidget(self.edit_match_keywords_btn)
        actions.addWidget(self.make_new_from_match_btn)
        actions.addStretch(1)
        root.addLayout(actions)

        self.setLayout(root)

        # state & warmup
        self._set_model_dependent_enabled(False)
        self._warm = ModelWarmupThread()
        self._warm.loaded.connect(self._on_model_ready)
        self._warm.start()

    # ---------- helpers ----------
    def _set_model_dependent_enabled(self, enabled: bool):
        for w in (self.save_button, self.search_btn, self.keywords_button):
            w.setEnabled(enabled)

    def _on_model_ready(self, ok: bool):
        self._model_ready = bool(ok)
        if ok:
            self.status_label.setText("Model klaar.")
            self.status_label.setStyleSheet("color:#2e7d32;")
            self._set_model_dependent_enabled(True)
            try:
                if self.current_img is not None and (self._pending_autogen or True):
                    self._pending_autogen = False
                    self.auto_generate_keywords(self.current_img)
            except Exception as e:
                QMessageBox.warning(self, "Kernwoorden", f"Automatische generatie mislukte: {e}")
        else:
            self.status_label.setText("Model laden mislukt. Controleer internet of cache.")
            self.status_label.setStyleSheet("color:#c62828;")
            self._set_model_dependent_enabled(False)

    def _threshold_value(self) -> float:
        return 0.90 if "90" in self.threshold_combo.currentText() else 0.85
    def _get_mode(self) -> str:
        txt = self.mode_combo.currentText()
        if "Dual" in txt: return "dual"
        if "Re-rank" in txt: return "rerank"
        return "image"

    # ---------- actions ----------
    def _refresh_kw_list(self):
        self.kw_list.clear()
        for kw in self.current_keywords:
            QListWidgetItem(kw, self.kw_list)

    def load_img_dialog(self):
        dlg = QInputDialog(self); dlg.setWindowTitle("Afbeelding laden")
        dlg.setLabelText("Voer een afbeelding-URL in of klik op Annuleer voor bestand...")
        dlg.setTextValue("")
        if dlg.exec() and dlg.textValue().strip():
            url = dlg.textValue().strip()
            try:
                import requests
                resp = requests.get(url, timeout=10); resp.raise_for_status()
                img = Image.open(BytesIO(resp.content)).convert("RGB")
                self.current_img = img; self.img_path_label.setText("[van URL geladen]")
                self.show_preview(self.left_img_label, img)
                if self._model_ready: self.auto_generate_keywords(img)
                else:
                    self._pending_autogen = True
                    self.status_label.setText("Model aan het laden… kernwoorden volgen automatisch zodra het klaar is.")
            except Exception as e:
                QMessageBox.critical(self, "Fout bij laden", str(e)); return
        else:
            file_path, _ = QFileDialog.getOpenFileName(self, "Selecteer afbeelding", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
            if not file_path: return
            try:
                img = Image.open(file_path).convert("RGB")
                self.current_img = img; self.img_path_label.setText(os.path.basename(file_path))
                self.show_preview(self.left_img_label, img)
                if self._model_ready: self.auto_generate_keywords(img)
                else:
                    self._pending_autogen = True
                    self.status_label.setText("Model aan het laden… kernwoorden volgen automatisch zodra het klaar is.")
            except Exception as e:
                QMessageBox.critical(self, "Fout bij laden", str(e)); return

    def auto_generate_keywords(self, img: Image.Image):
        try:
            top = self.generator.top_labels(img, top_n=5)
            self.current_keywords = top
            self._refresh_kw_list()
        except Exception as e:
            QMessageBox.critical(self, "Kernwoorden genereren", f"Er ging iets mis: {e}")

    def show_keywords_dialog(self):
        """Bewerk kernwoorden van de OPGELADEN (query) afbeelding."""
        current = self.current_keywords
        all_keywords = self.generator._candidate_labels()
        dlg = KeywordsDialog(current, all_keywords, parent=self)
        if dlg.exec():
            self.current_keywords = dlg.get_keywords()
            self._refresh_kw_list()

    def _current_keywords(self) -> List[str]:
        return self.current_keywords

    def save_new_entry(self):
        if self.current_img is None:
            QMessageBox.warning(self, "Fout", "Laad eerst een afbeelding."); return
        if not self._model_ready:
            QMessageBox.warning(self, "Fout", "Model is nog niet klaar."); return
        art_id, ok = QInputDialog.getText(self, "Artikel ID", "Geef artikel-ID of naam:")
        if not ok or not art_id.strip(): return
        art_id = art_id.strip().replace(" ", "_")
        b64 = image_to_base64(self.current_img)
        emb = self.generator.image_embedding(self.current_img)
        kws = self._current_keywords()
        kw_emb = self.generator.text_embedding_for_keywords(kws)
        try:
            self.repo.save_new_entry(art_id, b64, emb, kws, kw_emb)
            self.stats.inc_many(kws, amount=1)
            QMessageBox.information(self, "Opgeslagen", f"Artikel '{art_id}' opgeslagen.")
        except Exception as e:
            QMessageBox.critical(self, "Opslaan mislukt", str(e))

    # ---- kern zoek/rank ----
    def run_search(self):
        if self.current_img is None:
            QMessageBox.warning(self, "Fout", "Laad eerst een afbeelding."); return
        if not self._model_ready:
            QMessageBox.warning(self, "Fout", "Model is nog niet klaar."); return

        mode = self._get_mode()
        thr = self._threshold_value()
        gamma = float(self.centroid_gamma.currentText())

        q_img = self.generator.image_embedding(self.current_img)
        items: List[Tuple[float, str]] = []

        # baseline: pure image similarity + centroid-boost - négative penalty
        for art_id in self.repo.iter_entries():
            v_img = self.repo.get_entry_embedding(art_id)
            if v_img is None or v_img.shape != q_img.shape:
                continue
            sim_img = cos_sim(q_img, v_img)
            cent = self.repo.get_entry_centroid(art_id)
            sim_cent = cos_sim(q_img, cent) if cent is not None else sim_img
            base = (1.0 - gamma) * sim_img + gamma * sim_cent
            # negatieve artikel-penalty
            negcnt = self.repo.get_entry_neg_count(art_id)
            penalty = ARTICLE_NEG_ETA * math.log1p(negcnt)
            base = base - penalty
            items.append((base, art_id))

        if not items:
            QMessageBox.warning(self, "Geen matches", "Geen vectoren gevonden.")
            self._clear_results_table()
            self._update_selected_match(None, None, [])
            return

        items.sort(key=lambda x: x[0], reverse=True)

        if mode == "image":
            final = items

        elif mode == "dual":
            lam = float(self.fusion_kw_weight.currentText())
            final = []
            for _, art_id in items:
                v_img = self.repo.get_entry_embedding(art_id)
                v_kw = self.repo.get_entry_kw_embedding(art_id)
                if v_kw is None:
                    kw = self.repo.get_entry_keywords(art_id)
                    v_kw = self.generator.text_embedding_for_keywords(kw)
                    if v_kw is not None:
                        try: self.repo.save_entry_kw_embedding(art_id, v_kw)
                        except Exception: pass
                if v_kw is None:
                    v = v_img
                else:
                    v = v_img + lam * v_kw
                    v = v / (np.linalg.norm(v) or 1e-9)
                sim = cos_sim(q_img, v)
                cent = self.repo.get_entry_centroid(art_id)
                sim = (1.0 - gamma) * sim + gamma * (cos_sim(q_img, cent) if cent is not None else sim)
                # penalty toepassen
                negcnt = self.repo.get_entry_neg_count(art_id)
                penalty = ARTICLE_NEG_ETA * math.log1p(negcnt)
                sim = sim - penalty
                final.append((sim, art_id))
            final.sort(key=lambda x: x[0], reverse=True)

        else:  # rerank
            alpha = float(self.rerank_alpha.currentText() or f"{DEFAULT_RERANK_ALPHA:.2f}")
            topK = int(self.rerank_topk.currentText())
            q_txt = self.generator.text_embedding_for_keywords(self._current_keywords())
            prelim = items[:topK]
            rescored = []
            for base, art_id in prelim:
                if q_txt is None:
                    new_score = base
                else:
                    v_kw = self.repo.get_entry_kw_embedding(art_id)
                    if v_kw is None:
                        kw = self.repo.get_entry_keywords(art_id)
                        v_kw = self.generator.text_embedding_for_keywords(kw)
                        if v_kw is not None:
                            try: self.repo.save_entry_kw_embedding(art_id, v_kw)
                            except Exception: pass
                    sim_txt = cos_sim(q_txt, v_kw) if v_kw is not None else 0.0
                    new_score = (1.0 - alpha) * base + alpha * sim_txt
                # penalty toepassen
                negcnt = self.repo.get_entry_neg_count(art_id)
                penalty = ARTICLE_NEG_ETA * math.log1p(negcnt)
                new_score = new_score - penalty
                rescored.append((new_score, art_id))
            final = rescored + items[topK:]
            final.sort(key=lambda x: x[0], reverse=True)

        filtered = [(s, i) for (s, i) in final if s >= thr]
        if not filtered:
            filtered = final[:10]

        self._last_ranked_items = final[:]  # bewaar voor negatieve feedback
        self._populate_results_table(filtered)
        if filtered:
            best_sim, best_id = filtered[0]
            self._select_match(best_id, best_sim)
        else:
            self._update_selected_match(None, None, [])

    def _clear_results_table(self):
        self.results_table.setRowCount(0)

    def _populate_results_table(self, items: List[Tuple[float, str]]):
        self._clear_results_table()
        self.results_table.setRowCount(len(items))
        self.results_table.setColumnWidth(0, 96)
        self.results_table.setColumnWidth(1, 220)
        self.results_table.setColumnWidth(2, 60)
        self.results_table.setColumnWidth(3, 600)
        for r, (sim, art_id) in enumerate(items):
            b64 = self.repo.get_entry_image_b64(art_id)
            icon_item = QTableWidgetItem()
            if b64:
                try:
                    img = base64_to_image(b64)
                    pm = pil2pixmap(img).scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    icon_item.setIcon(QIcon(pm))
                except Exception:
                    pass
            self.results_table.setItem(r, 0, icon_item)
            self.results_table.setRowHeight(r, 80)
            self.results_table.setItem(r, 1, QTableWidgetItem(art_id))
            perc = int(sim * 100)
            pi = QTableWidgetItem(f"{perc}"); pi.setTextAlignment(Qt.AlignCenter)
            self.results_table.setItem(r, 2, pi)
            kw_list = self.repo.get_entry_keywords(art_id)
            self.results_table.setItem(r, 3, QTableWidgetItem(", ".join(kw_list)))

    def on_result_double_clicked(self, row: int, col: int):
        """Dubbelklik selecteert de rij."""
        art_item = self.results_table.item(row, 1)
        perc_item = self.results_table.item(row, 2)
        if not art_item:
            return
        art_id = art_item.text()
        sim = None
        if perc_item:
            try:
                sim = int(perc_item.text()) / 100.0
            except Exception:
                sim = None
        self._select_match(art_id, sim)

    def _select_match(self, art_id: Optional[str], sim: Optional[float]):
        if art_id is None:
            self._update_selected_match(None, None, []); return
        b64 = self.repo.get_entry_image_b64(art_id)
        kws = self.repo.get_entry_keywords(art_id)
        self.best_match_id = art_id
        self.best_match_keywords = kws
        self.last_similarity = sim
        self._update_selected_match(art_id, sim, kws, b64)

    def _update_selected_match(self, art_id: Optional[str], sim: Optional[float], kws: List[str], b64: Optional[str] = None):
        if art_id and b64:
            try:
                img = base64_to_image(b64)
                self.show_preview(self.right_img_label, img)
            except Exception:
                pass
        if art_id:
            self.lbl_artikel.setText(f"Artikel: {art_id}")
            self.lbl_keywords.setText(f"Kernwoorden: {', '.join(kws) if kws else '–'}")
            if sim is not None:
                perc = int(sim * 100)
                color = "#4CAF50" if perc > 85 else "#FFA000" if perc > 65 else "#D32F2F"
                self.sim_label.setText(f"{perc}%")
                self.sim_frame.setStyleSheet(f"QFrame{{background:#fff6f3;border:2.5px solid {color};border-radius:7px;}}")
                self.sim_frame.setVisible(True)
            else:
                self.sim_frame.setVisible(False)
            self.edit_match_keywords_btn.setVisible(True)
            self.make_new_from_match_btn.setVisible(True)
            self.learn_btn.setEnabled(True)
            self.not_correct_btn.setEnabled(True)
        else:
            self.right_img_label.clear()
            self.lbl_artikel.setText("Artikel: –")
            self.lbl_keywords.setText("Kernwoorden: –")
            self.sim_frame.setVisible(False)
            self.edit_match_keywords_btn.setVisible(False)
            self.make_new_from_match_btn.setVisible(False)
            self.learn_btn.setEnabled(False)
            self.not_correct_btn.setEnabled(False)

    # ---- leren van keuze (met confirm + undo) ----
    def learn_from_choice(self):
        if not self.best_match_id or self.current_img is None:
            QMessageBox.warning(self, "Leren", "Geen geselecteerde match of query-afbeelding."); return

        confirm = QMessageBox.question(
            self, "Bevestigen",
            "Deze actie leert van de geselecteerde match met je huidige query-kernwoorden.\nDoorgaan?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        art_id = self.best_match_id
        prev_cent = self.repo.get_entry_centroid(art_id)
        prev_cnt  = self.repo.get_entry_centroid_count(art_id)
        pos_kws   = list(self._current_keywords())
        N = 5
        neg_ids = [aid for _, aid in self._last_ranked_items[:N+1] if aid != art_id]
        neg_kws = []
        for aid in neg_ids:
            neg_kws.extend(self.repo.get_entry_keywords(aid))
        neg_kws = list(set(neg_kws))

        # bewaar undo-info
        self._undo_feedback = {
            "type": "learn",
            "art_id": art_id,
            "pos_kws": pos_kws,
            "neg_kws": neg_kws,
            "prev_centroid": (None if prev_cent is None else prev_cent.copy()),
            "prev_count": prev_cnt,
        }

        # voer leer-actie uit
        if pos_kws:
            self.stats.inc_many(pos_kws, amount=POS_WEIGHT)
        if neg_kws:
            self.stats.dec_many(neg_kws, amount=NEG_WEIGHT)

        q = self.generator.image_embedding(self.current_img)
        if prev_cent is None:
            cent, cnt = q, 1
        else:
            cnt = prev_cnt + 1
            cent = (prev_cent * prev_cnt + q) / cnt
        try:
            self.repo.save_entry_centroid(art_id, cent, cnt)
        except Exception:
            pass

        self.undo_btn.setEnabled(True)
        self.run_search()

    def mark_current_as_incorrect(self):
        """Expliciete negatieve feedback op de geselecteerde match."""
        if not self.best_match_id:
            QMessageBox.warning(self, "Negatieve feedback", "Geen match geselecteerd.")
            return
        art_id = self.best_match_id

        confirm = QMessageBox.question(
            self, "Bevestigen",
            "Deze voorgestelde match wordt als 'niet correct' gemarkeerd.\n"
            "Dit verlaagt de ranking en geeft negatieve signalen aan de kernwoorden.\nDoorgaan?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        # 1) Bewaar undo-data
        prev_neg = self.repo.get_entry_neg_count(art_id)
        match_kws = self.repo.get_entry_keywords(art_id)
        self._undo_feedback = {
            "type": "neg_click",
            "art_id": art_id,
            "neg_was": prev_neg,
            "dec_keywords": match_kws[:] if match_kws else []
        }

        # 2) Artikel-penalty verhogen
        try:
            self.repo.inc_entry_neg_count(art_id, amount=1)
        except Exception:
            pass

        # 3) Negatieve keyword-signalen voor match-keywords
        if match_kws:
            self.stats.dec_many(match_kws, amount=NEG_CLICK_WEIGHT)

        self.undo_btn.setEnabled(True)
        self.run_search()

    def undo_last_learn(self):
        if not self._undo_feedback:
            QMessageBox.information(self, "Undo", "Geen actie om ongedaan te maken."); return
        data = self._undo_feedback

        if data.get("type") == "neg_click":
            # herstel neg_count
            try:
                self.repo.set_entry_neg_count(data["art_id"], int(data.get("neg_was", 0)))
            except Exception:
                # fallback voor LocalFS (zou al gedekt zijn)
                if isinstance(self.repo, LocalFSRepository):
                    d = self.repo._dir(data["art_id"])
                    try:
                        with open(os.path.join(d, NEGCOUNT_FILENAME), "w", encoding="utf-8") as f:
                            f.write(str(int(data.get("neg_was", 0))))
                    except Exception:
                        pass
            # herstel keyword neg
            for k in data.get("dec_keywords", []):
                pos, neg = self.stats.get_pos_neg(k)
                self.stats._stats.setdefault(k, {"pos":0,"neg":0})
                self.stats._stats[k]["neg"] = max(0, neg - NEG_CLICK_WEIGHT)
            self.stats.save()

            self._undo_feedback = None
            self.undo_btn.setEnabled(False)
            self.run_search()
            return

        # Anders: type = "learn"
        # herstel stats
        if data.get("pos_kws"):
            for k in data["pos_kws"]:
                pos, neg = self.stats.get_pos_neg(k)
                self.stats._stats.setdefault(k, {"pos":0,"neg":0})
                self.stats._stats[k]["pos"] = max(0, pos - POS_WEIGHT)
        if data.get("neg_kws"):
            for k in data["neg_kws"]:
                pos, neg = self.stats.get_pos_neg(k)
                self.stats._stats.setdefault(k, {"pos":0,"neg":0})
                self.stats._stats[k]["neg"] = max(0, neg - NEG_WEIGHT)
        self.stats.save()

        # herstel centroid
        if data.get("prev_centroid") is None:
            if isinstance(self.repo, LocalFSRepository):
                d = self.repo._dir(data["art_id"])
                for fname in (CENTROID_FILENAME, CENTROID_COUNT):
                    try: os.remove(os.path.join(d, fname))
                    except Exception: pass
        else:
            self.repo.save_entry_centroid(data["art_id"], data["prev_centroid"], data["prev_count"])

        self._undo_feedback = None
        self.undo_btn.setEnabled(False)
        self.run_search()

    def edit_match_keywords(self):
        """Bewerk kernwoorden van de GESELECTEERDE MATCH (rechts)."""
        if not self.best_match_id:
            QMessageBox.warning(self, "Fout", "Geen match geselecteerd."); return
        current = self.repo.get_entry_keywords(self.best_match_id)
        all_keywords = self.generator._candidate_labels()
        dlg = KeywordsDialog(current, all_keywords, parent=self)
        if dlg.exec():
            new_keywords = dlg.get_keywords()
            try:
                self.repo.update_entry_keywords(self.best_match_id, new_keywords)
                kw_emb = self.generator.text_embedding_for_keywords(new_keywords)
                if kw_emb is not None:
                    try: self.repo.save_entry_kw_embedding(self.best_match_id, kw_emb)
                    except Exception: pass
                self.stats.inc_many(new_keywords, amount=1)
                QMessageBox.information(self, "Opgeslagen", "Kernwoorden aangepast.")
                self.lbl_keywords.setText(f"Kernwoorden: {', '.join(new_keywords)}")
                self.best_match_keywords = new_keywords
            except Exception as e:
                QMessageBox.critical(self, "Opslaan mislukt", str(e))

    def make_new_from_match(self):
        if not self.best_match_id:
            QMessageBox.warning(self, "Fout", "Geen match geselecteerd."); return
        art_id, ok = QInputDialog.getText(self, "Nieuw artikel-ID", "Geef nieuwe artikel-ID of naam:")
        if not ok or not art_id.strip(): return
        art_id = art_id.strip().replace(" ", "_")
        b64 = self.repo.get_entry_image_b64(self.best_match_id) or ""
        emb = self.repo.get_entry_embedding(self.best_match_id)
        kws = self.repo.get_entry_keywords(self.best_match_id)
        kw_emb = self.repo.get_entry_kw_embedding(self.best_match_id)
        if kw_emb is None:
            kw_emb = self.generator.text_embedding_for_keywords(kws)
        if emb is None:
            QMessageBox.critical(self, "Fout", "Bron heeft geen embedding."); return
        try:
            self.repo.save_new_entry(art_id, b64, emb, kws, kw_emb)
            self.stats.inc_many(kws, amount=1)
            if b64:
                img = base64_to_image(b64)
                self.current_img = img; self.show_preview(self.left_img_label, img)
                self.img_path_label.setText(f"(Nieuw artikel: {art_id})")
            QMessageBox.information(self, "Aangemaakt", f"Nieuw artikel '{art_id}' gemaakt op basis van match.")
        except Exception as e:
            QMessageBox.critical(self, "Aanmaken mislukt", str(e))

    def show_preview(self, label, pil_img: Image.Image):
        qpix = pil2pixmap(pil_img).scaled(260, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(qpix)

# -------------------------------
# Main
# -------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = CombinedApp()
    win.show()
    sys.exit(app.exec())



'''
Hoe later overschakelen naar API
Zet USE_API = True.

Vul de ApiRepository-methodes in (endpoints voor keywords, articles, image, embedding, keywords-update).

Laat de signatures hetzelfde — de rest van de app hoeft niet te veranderen.
'''