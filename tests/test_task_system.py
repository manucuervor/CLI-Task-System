import shutil
import unittest
import uuid
from pathlib import Path
from unittest import mock

import numpy as np

from task_system import config, search
from task_system.store import TaskStore


class FakeModel:
    def encode(self, texts, normalize_embeddings=True):
        vectors = []
        for text in texts:
            base = np.zeros(384, dtype=np.float32)
            token_sum = float(sum(ord(ch) for ch in text))
            base[0] = float(len(text))
            base[1] = token_sum % 997.0
            base[2] = 1.0
            vectors.append(base)
        return np.vstack(vectors)


class TaskSystemTests(unittest.TestCase):
    def setUp(self):
        self.original_paths = (
            config.DATA_DIR,
            config.DB_PATH,
            config.LOG_PATH,
            config.INDEX_DIR,
        )
        self.data_dir = self.original_paths[0]
        suffix = uuid.uuid4().hex
        config.DATA_DIR = self.data_dir
        config.DB_PATH = self.data_dir / f"test_{suffix}.db"
        config.LOG_PATH = self.data_dir / f"test_{suffix}.jsonl"
        config.INDEX_DIR = self.data_dir / f"test_{suffix}_embeddings"
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        search._model = None
        search._index = None
        search._metadata = []

    def tearDown(self):
        test_db_path = config.DB_PATH
        test_log_path = config.LOG_PATH
        test_index_dir = config.INDEX_DIR
        config.DATA_DIR, config.DB_PATH, config.LOG_PATH, config.INDEX_DIR = self.original_paths
        search._model = None
        search._index = None
        search._metadata = []
        if test_db_path.exists():
            test_db_path.unlink()
        if test_log_path.exists():
            test_log_path.unlink()
        shutil.rmtree(test_index_dir, ignore_errors=True)

    def test_history_tracks_latest_revision_status(self):
        with mock.patch("task_system.search._get_model", return_value=FakeModel()):
            store = TaskStore()
            store.create_task("TASK-001", "Initial setup", "Write the bootstrap workflow.")
            store.execute_task("TASK-001", "Implemented and verified.")
            store.audit_task("TASK-001", "Meets the requested behavior.", "done")
            store.correct_task("TASK-001", "Rework the validation path.", "validation_error")

        history = store.get_history("TASK-001")

        self.assertEqual(history[0]["status"], "done")
        self.assertEqual(history[1]["status"], "correcting")

    def test_search_returns_results_with_mocked_semantic_model(self):
        with mock.patch("task_system.search._get_model", return_value=FakeModel()):
            store = TaskStore()
            store.create_task("TASK-002", "Bootstrap workflow", "Write the bootstrap workflow.")

        results = store.search("bootstrap workflow")

        self.assertTrue(results)
        self.assertEqual(results[0]["task_id"], "TASK-002")
        self.assertEqual(results[0]["revision"], 1)
